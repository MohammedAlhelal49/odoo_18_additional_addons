# -*- coding: utf-8 -*-
import math
import re
from datetime import timedelta

from psycopg2 import errors as pg_errors

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import str2bool

DEFAULT_VALIDITY_DAYS = 31

# Date the follow-up of won opportunities started to be required (set once at
# install / upgrade): no won opportunity expires before it + the period.
WON_FOLLOWUP_START_PARAM = 'alomran_implementation.won_followup_start'

# Phone numbers of the same customer are matched on their last 9 digits
# (UAE local number 5X XXX XXXX) so '050 123 4567', '+971 50 123 4567' and
# '00971501234567' are the same customer. Shorter numbers must match fully.
MATCH_SUFFIX_DIGITS = 9
MIN_NUMBER_DIGITS = 7

# SQL expression of a phone column reduced to its comparable key. The same
# expression is indexed in res.partner / crm.lead init() - keep them in sync.
NUMBER_KEY_SQL = "right(regexp_replace(COALESCE({col}, ''), '[^0-9]', '', 'g'), %d)" % MATCH_SUFFIX_DIGITS

# Chatter notes posted automatically by the system, not by an employee.
SYSTEM_SUBJECTS = ('Duplicate Information Detected',)

# Message types an employee produces while working: notes / messages written in
# Odoo, e-mails sent from their mailbox to the record, SMS.
EMPLOYEE_MESSAGE_TYPES = ('comment', 'email', 'sms')

# Author is a real employee: internal user, never OdooBot / __system__.
EMPLOYEE_AUTHOR_JOIN = """
      JOIN res_users u ON u.partner_id = m.author_id
                      AND u.share IS NOT TRUE AND u.id != %d
""" % SUPERUSER_ID

EMPLOYEE_MESSAGE_FILTER = """
       AND (m.mail_activity_type_id IS NOT NULL
            OR (m.message_type IN %(message_types)s
                AND COALESCE(m.subject, '') NOT IN %(system_subjects)s))
"""

# Generic employee updates on any record (res.partner...): (res_id, date).
UPDATES_SQL = """
    SELECT m.res_id, m.date AS dt
      FROM mail_message m
      """ + EMPLOYEE_AUTHOR_JOIN + """
     WHERE m.model = %(model)s
       AND m.res_id = ANY(%(ids)s)
""" + EMPLOYEE_MESSAGE_FILTER


def lead_updates_sql(restrict):
    """Employee updates of opportunities: (res_id, dt).

    ``restrict``: only the leads in %(ids)s (else every lead).
    Counted as an update of the opportunity:
      * a note / message / e-mail / SMS written by an employee,
      * an activity marked as done by an employee,
      * a stage change made by an employee,
      * a new salesperson or a restore from Lost (any author: assignment
        rules and managers included, so the new owner gets a full period),
      * a quotation created from the opportunity and the employees'
        messages / completed activities on that quotation,
      * a meeting of the opportunity that already took place.
    """
    def cond(col):
        return "%s = ANY(%%(ids)s)" % col if restrict else "TRUE"
    return f"""
    SELECT m.res_id, m.date AS dt
      FROM mail_message m
      {EMPLOYEE_AUTHOR_JOIN}
     WHERE m.model = 'crm.lead' AND {cond('m.res_id')}
      {EMPLOYEE_MESSAGE_FILTER}
    UNION ALL
    SELECT m.res_id, m.date
      FROM mail_tracking_value tv
      JOIN mail_message m ON m.id = tv.mail_message_id
      JOIN ir_model_fields f ON f.id = tv.field_id
      {EMPLOYEE_AUTHOR_JOIN}
     WHERE m.model = 'crm.lead' AND {cond('m.res_id')}
       AND f.model = 'crm.lead' AND f.name = 'stage_id'
    UNION ALL
    SELECT m.res_id, m.date
      FROM mail_tracking_value tv
      JOIN mail_message m ON m.id = tv.mail_message_id
      JOIN ir_model_fields f ON f.id = tv.field_id
     WHERE m.model = 'crm.lead' AND {cond('m.res_id')}
       AND f.model = 'crm.lead' AND f.name IN ('user_id', 'active')
    UNION ALL
    SELECT so.opportunity_id, so.create_date
      FROM sale_order so
     WHERE so.opportunity_id IS NOT NULL AND {cond('so.opportunity_id')}
    UNION ALL
    SELECT so.opportunity_id, m.date
      FROM mail_message m
      JOIN sale_order so ON so.id = m.res_id
      {EMPLOYEE_AUTHOR_JOIN}
     WHERE m.model = 'sale.order'
       AND so.opportunity_id IS NOT NULL AND {cond('so.opportunity_id')}
      {EMPLOYEE_MESSAGE_FILTER}
    UNION ALL
    SELECT ev.opportunity_id, ev.start
      FROM calendar_event ev
     WHERE ev.opportunity_id IS NOT NULL AND {cond('ev.opportunity_id')}
       AND ev.active IS TRUE AND ev.start <= %(now)s
    """


VALIDITY_STATUS = [
    ('active', 'Active'),
    ('expired', 'Expired'),
    ('won', 'Won'),
]


class AlomranValidityTools(models.AbstractModel):
    """Shared helpers that compute the "validity" of opportunities and the
    Manual Transfer (Take Over) of customers.

    Validity is computed per OPPORTUNITY, from its own history only (see
    lead_updates_sql): work on the contact or on other opportunities does not
    extend it. The opportunity expires after N FULL days without any update.
    Won opportunities too: a customer who bought must be followed up, else it
    can be taken over with its won opportunities. For the won opportunities
    that existed before this rule, the period starts at its installation
    (WON_FOLLOWUP_START_PARAM, grace period).

    A *customer* is the set of contacts and opportunities sharing a phone
    number (or linked to those contacts). It can be taken over (contacts +
    opportunities together) only when ALL its opportunities owned by
    other salespeople are expired.
    """
    _name = 'alomran.validity.tools'
    _description = 'Al Omran Lead Validity Helpers'

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    @api.model
    def _is_manual_transfer_enabled(self):
        """Manual Transfer (Take Over) switch, ON unless disabled in the CRM settings."""
        return str2bool(self.env['ir.config_parameter'].sudo().get_param(
            'alomran_implementation.manual_transfer_enabled', 'True'))

    @api.model
    def _check_manual_transfer_enabled(self):
        if not self._is_manual_transfer_enabled():
            raise UserError(_("Manual transfer (Take Over) is currently disabled by the administrator."))

    @api.model
    def _get_won_followup_start(self):
        value = self.env['ir.config_parameter'].sudo().get_param(WON_FOLLOWUP_START_PARAM)
        try:
            return fields.Datetime.to_datetime(value) if value else None
        except ValueError:
            return None

    @api.model
    def _get_validity_days(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'alomran_implementation.lead_validity_days', DEFAULT_VALIDITY_DAYS)
        try:
            days = int(value)
        except (TypeError, ValueError):
            days = DEFAULT_VALIDITY_DAYS
        return days if days > 0 else DEFAULT_VALIDITY_DAYS

    # ------------------------------------------------------------------
    # Last update / validity
    # ------------------------------------------------------------------
    def _sql_params(self, **params):
        params.update({
            'system_subjects': SYSTEM_SUBJECTS,
            'message_types': EMPLOYEE_MESSAGE_TYPES,
            'now': fields.Datetime.now(),
        })
        return params

    def _flush_update_sources(self):
        for model in ('crm.lead', 'mail.message', 'mail.tracking.value',
                      'sale.order', 'calendar.event'):
            self.env[model].flush_model()

    @api.model
    def _get_last_update_map(self, model_name, ids):
        """Return {res_id: last employee update} for ``ids`` (one query)."""
        ids = [i for i in (ids or []) if isinstance(i, int)]
        if not ids:
            return {}
        self._flush_update_sources()
        query = lead_updates_sql(restrict=True) if model_name == 'crm.lead' else UPDATES_SQL
        self.env.cr.execute(f"""
            SELECT res_id, MAX(dt) FROM ({query}) AS updates
            GROUP BY res_id
        """, self._sql_params(model=model_name, ids=ids))
        return dict(self.env.cr.fetchall())

    @api.model
    def _get_partner_last_update_map(self, partners):
        """{partner_id: last update} over the partner + its open opportunities."""
        partners = partners.sudo().exists()
        if not partners:
            return {}
        own_map = self._get_last_update_map('res.partner', partners.ids)
        result = {}
        for partner in partners:
            dates = [d for d in (own_map.get(partner.id), partner.create_date) if d]
            result[partner.id] = max(dates) if dates else False

        leads = self.env['crm.lead'].sudo().search([
            ('partner_id', 'in', partners.ids),
            ('stage_id.is_won', '=', False),
        ])
        lead_map = self._get_lead_last_update_map(leads)
        for lead in leads:
            last = lead_map.get(lead.id)
            pid = lead.partner_id.id
            if last and (not result.get(pid) or last > result[pid]):
                result[pid] = last
        return result

    @api.model
    def _get_lead_last_update_map(self, leads):
        """{lead_id: last update}, from each lead's own history only."""
        leads = leads.sudo().exists()
        if not leads:
            return {}
        own_map = self._get_last_update_map('crm.lead', leads.ids)
        won_start = self._get_won_followup_start()
        result = {}
        for lead in leads:
            dates = [d for d in (own_map.get(lead.id), lead.create_date) if d]
            if won_start and lead.stage_id.is_won:
                dates.append(won_start)
            result[lead.id] = max(dates) if dates else False
        return result

    @api.model
    def _get_validity_info(self, last_update):
        """Return (remaining_days, status, transfer_date) for a last-update datetime.

        The record expires once ``validity_days`` FULL days (24h each) have
        passed since the last update. Remaining days are rounded up so a
        record is never shown as "0 days" while it is still active.
        """
        if not last_update:
            return 0, 'expired', False
        transfer_date = last_update + timedelta(days=self._get_validity_days())
        now = fields.Datetime.now()
        if transfer_date <= now:
            return 0, 'expired', transfer_date
        remaining = math.ceil((transfer_date - now).total_seconds() / 86400.0)
        return remaining, 'active', transfer_date

    @api.model
    def _get_lead_ids_by_status(self, statuses):
        """Ids of crm.lead records whose validity status is in statuses.
        Same rules as _get_lead_last_update_map, computed in SQL for search."""
        return [lead_id for lead_id, __, status in self._get_lead_validity_rows()
                if status in statuses]

    @api.model
    def _get_lead_validity_rows(self, lead_ids=None):
        """[(lead_id, last_update, status)] for all leads, or only ``lead_ids``."""
        self._flush_update_sources()
        cutoff = fields.Datetime.now() - timedelta(days=self._get_validity_days())
        restrict = lead_ids is not None
        lead_filter = "WHERE l.id = ANY(%(ids)s)" if restrict else ""
        self.env.cr.execute(f"""
            WITH lead_upd AS (
                SELECT res_id, MAX(dt) AS dt FROM ({lead_updates_sql(restrict)}) x
                 GROUP BY res_id
            )
            SELECT id, dt, CASE WHEN dt IS NULL OR dt <= %(cutoff)s THEN 'expired' ELSE 'active' END
              FROM (
                SELECT l.id,
                       GREATEST(l.create_date, lu.dt,
                                CASE WHEN COALESCE(s.is_won, FALSE) THEN %(won_start)s::timestamp END) AS dt
                  FROM crm_lead l
                  LEFT JOIN crm_stage s ON s.id = l.stage_id
                  LEFT JOIN lead_upd lu ON lu.res_id = l.id
                 {lead_filter}
              ) x
        """, self._sql_params(cutoff=cutoff, ids=list(lead_ids or []),
                               won_start=self._get_won_followup_start()))
        return self.env.cr.fetchall()

    # ------------------------------------------------------------------
    # Customer = contacts + opportunities sharing a number
    # ------------------------------------------------------------------
    @api.model
    def _number_key(self, value):
        """Comparable key of a phone number ('' when too short to be reliable)."""
        digits = re.sub(r'\D', '', value or '')
        if len(digits) < MIN_NUMBER_DIGITS:
            return ''
        return digits[-MATCH_SUFFIX_DIGITS:]

    @api.model
    def _number_keys(self, records):
        keys = set()
        for rec in records:
            keys.update(filter(None, (self._number_key(rec.phone), self._number_key(rec.mobile))))
        return keys

    @api.model
    def _search_ids_by_number_keys(self, table, keys):
        """Ids of ``table`` rows whose phone or mobile has one of ``keys``.
        Employees' and companies' own partners are never part of a customer."""
        assert table in ('res_partner', 'crm_lead')  # hard-coded whitelist
        keys = list(keys or [])
        if not keys:
            return []
        extra = ""
        if table == 'res_partner':
            extra = """
               AND NOT EXISTS (SELECT 1 FROM res_users u
                                WHERE u.partner_id = t.id AND u.share IS NOT TRUE)
               AND NOT EXISTS (SELECT 1 FROM res_company c WHERE c.partner_id = t.id)
            """
        self.env.cr.execute(f"""
            SELECT t.id FROM {table} t
             WHERE ({NUMBER_KEY_SQL.format(col='t.phone')} = ANY(%(keys)s)
                 OR {NUMBER_KEY_SQL.format(col='t.mobile')} = ANY(%(keys)s))
               {extra}
        """, {'keys': keys})
        return [row[0] for row in self.env.cr.fetchall()]

    @api.model
    def _get_customer_scope(self, partners=None, leads=None):
        """(contacts, opportunities) of the customer of ``partners`` / ``leads``.

        Contacts: the given ones, the contacts of the given leads and every
        contact (archived included) sharing one of their numbers.
        Opportunities: active (won ones included), linked to those contacts OR
        sharing one of the numbers - so opportunities without a contact are
        part of the customer too.
        """
        Partner = self.env['res.partner'].sudo().with_context(active_test=False)
        Lead = self.env['crm.lead'].sudo()
        partners = Partner.browse(partners.ids if partners else [])
        leads = Lead.browse(leads.ids if leads else [])
        self.env['res.partner'].flush_model(['phone', 'mobile'])
        self.env['crm.lead'].flush_model(['phone', 'mobile', 'partner_id'])

        partners |= Partner.browse(leads.partner_id.ids)
        keys = self._number_keys(partners) | self._number_keys(leads)
        if keys:
            partners |= Partner.browse(self._search_ids_by_number_keys('res_partner', keys))
        domain = [('partner_id', 'in', partners.ids)] if partners else [('id', '=', 0)]
        if keys:
            domain = ['|', ('id', 'in', self._search_ids_by_number_keys('crm_lead', keys))] + domain
        opportunities = Lead.search([('type', '=', 'opportunity')] + domain)
        return partners, opportunities

    @api.model
    def _get_transfer_info(self, opportunities):
        """Manual Transfer state of a customer from its open ``opportunities``
        owned by someone else than the current user.

        Returns (remaining_days, status, transfer_date): status is False when
        there is no such opportunity (nothing to take over), 'active' while at
        least one is still active (remaining days / date of the LAST one to
        expire), 'expired' when all of them are expired.
        """
        others = opportunities.filtered(lambda l: l.user_id != self.env.user)
        if not others:
            return 0, False, False
        last_map = self._get_lead_last_update_map(others)
        infos = [self._get_validity_info(last_map.get(lead.id)) for lead in others]
        active = [info for info in infos if info[1] == 'active']
        if active:
            return max(i[0] for i in active), 'active', max(i[2] for i in active)
        return 0, 'expired', max((i[2] for i in infos if i[2]), default=False)

    @api.model
    def _get_customer_transfer_info(self, partners=None, leads=None):
        return self._get_transfer_info(self._get_customer_scope(partners, leads)[1])

    # ------------------------------------------------------------------
    # Take Over
    # ------------------------------------------------------------------
    @api.model
    def _take_over_customer(self, partners=None, leads=None):
        """Manual transfer of a whole customer to the current user.
        Every check is done here, server side: callers are reachable by RPC."""
        user = self.env.user
        if not user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(_("Only salespeople can take over customers."))
        self._check_manual_transfer_enabled()

        contacts, opportunities = self._get_customer_scope(partners, leads)
        if not opportunities.filtered(lambda l: l.user_id != user):
            if opportunities or contacts.filtered(lambda p: p.user_id == user):
                raise UserError(_("This customer is already assigned to you."))
            raise UserError(_(
                "This customer has no opportunity with another salesperson, "
                "so there is nothing to take over."))

        # Two salespeople taking over the same customer at the same time:
        # the second one does not wait and gets a clear message.
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(
                    "SELECT id FROM crm_lead WHERE id = ANY(%s) FOR UPDATE NOWAIT",
                    [opportunities.ids])
        except pg_errors.LockNotAvailable:
            raise UserError(_("Another salesperson is taking over this customer right now. "
                              "Please try again in a moment."))
        opportunities.invalidate_recordset()

        remaining, status, __ = self._get_transfer_info(opportunities)
        if status != 'expired':
            raise UserError(_(
                "This customer still has an active opportunity with another salesperson. "
                "Manual transfer is allowed only when all its opportunities have had no update "
                "for %(days)s full days (available in %(remaining)s day(s)).",
                days=self._get_validity_days(), remaining=remaining,
            ))

        taken_leads = opportunities.filtered(lambda l: l.user_id != user)
        taken_contacts = contacts.filtered(lambda p: p.user_id != user)
        previous_owner = {lead.id: lead.user_id for lead in taken_leads}
        old_users = (taken_leads.user_id | taken_contacts.user_id) - user
        old_companies = taken_leads.company_id | taken_contacts.company_id
        company = self.env.company
        vals = {'user_id': user.id, 'company_id': company.id}

        taken_contacts.with_context(skip_duplicate_check=True).write(vals)
        taken_leads.write(vals)

        # Follow-ups go with the customer; the previous owners stop following it.
        self.env['mail.activity'].sudo().search([
            ('user_id', 'in', old_users.ids),
            '|',
            '&', ('res_model', '=', 'crm.lead'), ('res_id', 'in', taken_leads.ids),
            '&', ('res_model', '=', 'res.partner'), ('res_id', 'in', contacts.ids),
        ]).write({'user_id': user.id})
        if old_users:
            for records in (taken_leads, contacts):
                if records:
                    records.message_unsubscribe(partner_ids=old_users.partner_id.ids)

        body = _("Manually transferred from %(old)s to %(new)s (%(company)s): all the customer's "
                 "opportunities had no update for %(days)s full days.",
                 old=", ".join(old_users.mapped('name')) or _("Unassigned"),
                 new=user.name, company=company.name, days=self._get_validity_days())
        for lead in taken_leads:
            # The previous owner of the opportunity is notified in their inbox.
            lead.message_post(
                body=body, subject=_("Opportunity Reassigned"),
                message_type='comment', subtype_xmlid='mail.mt_note',
                partner_ids=previous_owner[lead.id].partner_id.ids,
            )
        for contact in taken_contacts:
            contact.message_post(body=body, subject=_("Contact Reassigned"),
                                 message_type='comment', subtype_xmlid='mail.mt_note')

        first_contact, first_lead = contacts[:1], opportunities[:1]
        self.env['alomran.takeover.log'].sudo().create({
            'user_id': user.id,
            'company_id': company.id,
            'previous_user_ids': [(6, 0, old_users.ids)],
            'previous_company_ids': [(6, 0, old_companies.ids)],
            'partner_ids': [(6, 0, contacts.ids)],
            'lead_ids': [(6, 0, opportunities.ids)],
            'customer_name': (first_contact.name or first_lead.contact_name
                              or first_lead.partner_name or first_lead.name),
            'number': (first_contact.mobile or first_contact.phone
                       or first_lead.mobile or first_lead.phone),
        })
        return contacts, opportunities


class AlomranTakeoverLog(models.Model):
    """Audit trail of the manual transfers (Take Over), for the sales managers."""
    _name = 'alomran.takeover.log'
    _description = 'Al Omran Take Over Log'
    _order = 'date desc, id desc'

    date = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Taken By", required=True, readonly=True)
    company_id = fields.Many2one('res.company', string="New Branch", readonly=True)
    previous_user_ids = fields.Many2many(
        'res.users', 'alomran_takeover_log_prev_user_rel', 'log_id', 'user_id',
        string="Previous Salespeople", readonly=True)
    previous_company_ids = fields.Many2many(
        'res.company', 'alomran_takeover_log_prev_company_rel', 'log_id', 'company_id',
        string="Previous Branches", readonly=True)
    partner_ids = fields.Many2many(
        'res.partner', 'alomran_takeover_log_partner_rel', 'log_id', 'partner_id',
        string="Contacts", readonly=True)
    lead_ids = fields.Many2many(
        'crm.lead', 'alomran_takeover_log_lead_rel', 'log_id', 'lead_id',
        string="Opportunities", readonly=True)
    customer_name = fields.Char(string="Customer", readonly=True)
    number = fields.Char(readonly=True)
    lead_count = fields.Integer(string="# Opportunities", compute='_compute_lead_count')
    cross_branch = fields.Boolean(
        string="From Another Branch", compute='_compute_cross_branch', store=True,
        help="The customer was taken over from another branch.")

    def _compute_lead_count(self):
        for log in self:
            log.lead_count = len(log.lead_ids)

    @api.depends('company_id', 'previous_company_ids')
    def _compute_cross_branch(self):
        for log in self:
            log.cross_branch = bool(log.previous_company_ids - log.company_id)
