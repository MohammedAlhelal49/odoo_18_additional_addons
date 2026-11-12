# -*- coding: utf-8 -*-
import logging
import re

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from ..models.alomran_validity import MATCH_SUFFIX_DIGITS, NUMBER_KEY_SQL, VALIDITY_STATUS

_logger = logging.getLogger(__name__)

MIN_LOOKUP_DIGITS = 7      # anti-enumeration: no partial / short searches
MAX_RESULTS = 50


class AlomranCustomerLookup(models.TransientModel):
    """Search a phone/mobile number across ALL branches and salespeople.

    Salespeople normally cannot see contacts/leads owned by others (record
    rules), so the lookup runs with sudo but only exposes a minimal, read-only
    summary (no links, no emails, no notes).
    """
    _name = 'alomran.customer.lookup'
    _description = 'Customer / Lead Number Lookup'

    search_term = fields.Char(string="Phone / Mobile Number")
    line_ids = fields.One2many('alomran.customer.lookup.line', 'lookup_id', string="Results")
    result_count = fields.Integer(compute='_compute_result_count')
    validity_days = fields.Integer(compute='_compute_result_count')
    transfer_enabled = fields.Boolean(compute='_compute_result_count')
    searched = fields.Boolean()

    @api.depends('line_ids')
    def _compute_result_count(self):
        tools = self.env['alomran.validity.tools']
        days = tools._get_validity_days()
        enabled = tools._is_manual_transfer_enabled()
        for rec in self:
            rec.result_count = len(rec.line_ids)
            rec.validity_days = days
            rec.transfer_enabled = enabled

    @api.model
    def _normalize_digits(self, term):
        digits = re.sub(r'\D', '', term or '')
        if digits.startswith('00'):
            digits = digits[2:]
        return digits

    def _check_lookup_access(self):
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(_("Only salespeople can use the customer lookup."))

    def _search_ids(self, table, digits):
        """Match on digits only so '0501234567', '+971 50 123 4567' and
        '971501234567' all find each other."""
        if len(digits) >= MATCH_SUFFIX_DIGITS:
            # same key as the customer matching (indexed expression)
            key = digits[-MATCH_SUFFIX_DIGITS:]
            number_cond = "({} = %(key)s OR {} = %(key)s)".format(
                NUMBER_KEY_SQL.format(col='t.phone'), NUMBER_KEY_SQL.format(col='t.mobile'))
        else:
            key = None
            number_cond = """(regexp_replace(COALESCE(t.phone, ''), '[^0-9]', '', 'g') LIKE %(p)s
                 OR regexp_replace(COALESCE(t.mobile, ''), '[^0-9]', '', 'g') LIKE %(p)s)"""
        pattern = '%' + digits + '%'
        extra = ""
        if table == 'res_partner':
            # never expose employees' or companies' own partner records
            extra = """
               AND NOT EXISTS (SELECT 1 FROM res_users u
                                WHERE u.partner_id = t.id AND u.share IS NOT TRUE)
               AND NOT EXISTS (SELECT 1 FROM res_company c WHERE c.partner_id = t.id)
            """
        elif table == 'crm_lead':
            extra = "AND t.type = 'opportunity'"
        # table name comes from a hard-coded whitelist, never from user input
        assert table in ('res_partner', 'crm_lead')
        self.env.cr.execute(f"""
            SELECT t.id FROM {table} t
             WHERE t.active IS TRUE
               AND {number_cond}
               {extra}
             ORDER BY t.id DESC
             LIMIT %(limit)s
        """, {'p': pattern, 'key': key, 'limit': MAX_RESULTS})
        return [r[0] for r in self.env.cr.fetchall()]

    def action_search(self):
        self.ensure_one()
        self._check_lookup_access()
        digits = self._normalize_digits(self.search_term)
        if len(digits) < MIN_LOOKUP_DIGITS:
            raise UserError(_(
                "Please enter a valid phone/mobile number (at least %s digits).",
                MIN_LOOKUP_DIGITS,
            ))
        _logger.info("Customer lookup by user %s (uid %s) for number ending ...%s",
                     self.env.user.login, self.env.uid, digits[-4:])

        Partner = self.env['res.partner'].sudo()
        Lead = self.env['crm.lead'].sudo()
        self.env['res.partner'].flush_model(['phone', 'mobile', 'active'])
        self.env['crm.lead'].flush_model(['phone', 'mobile', 'active'])

        # Opportunities only: matched by their own number or by their contact's
        partners = Partner.browse(self._search_ids('res_partner', digits))
        leads = Lead.browse(self._search_ids('crm_lead', digits))
        if partners:
            leads |= Lead.search([
                ('partner_id', 'in', partners.ids),
                ('type', '=', 'opportunity'),
            ], order='id desc', limit=MAX_RESULTS)

        tools = self.env['alomran.validity.tools']
        me = self.env.user
        # Take Over is customer-wide (contacts + opportunities sharing the
        # number): allowed only when ALL its opportunities (won included) are expired.
        leads = leads[:MAX_RESULTS]
        customer_status = {}
        for lead in leads:
            if lead.id in customer_status:
                continue
            __, opportunities = tools._get_customer_scope(leads=lead)
            status = tools._get_transfer_info(opportunities)[1]
            for opportunity in opportunities | lead:
                customer_status.setdefault(opportunity.id, status)

        lines = []
        for lead in leads:
            transferable = (lead.user_id != me and lead.alomran_validity_status == 'expired'
                            and customer_status.get(lead.id) == 'expired')
            lines.append({
                'record_type': lead.type,
                'customer_name': lead.partner_id.name or lead.contact_name or lead.name,
                'phone': lead.mobile or lead.phone,
                'branch_name': lead.company_id.name or _("No Branch"),
                'salesperson_name': lead.user_id.name or _("Unassigned"),
                'stage_name': lead.stage_id.name,
                'last_update_date': lead.alomran_last_update_date,
                'remaining_days': lead.alomran_remaining_days,
                'status': lead.alomran_validity_status,
                'transfer_date': lead.alomran_transfer_date,
                'is_mine': lead.user_id == me,
                'transferable': transferable,
                'lead_ref': lead.id,
                'partner_ref': lead.partner_id.id or False,
            })

        self.write({
            'searched': True,
            'line_ids': [Command.clear()] + [Command.create(v) for v in lines],
        })
        return True

    def action_clear(self):
        self.write({'search_term': False, 'searched': False, 'line_ids': [Command.clear()]})
        return True


class AlomranCustomerLookupLine(models.TransientModel):
    _name = 'alomran.customer.lookup.line'
    _description = 'Customer / Lead Number Lookup Result'
    _order = 'status, remaining_days desc, id'

    lookup_id = fields.Many2one('alomran.customer.lookup', required=True, ondelete='cascade')
    record_type = fields.Selection([
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('opportunity', 'Opportunity'),
    ], string="Type", readonly=True)
    customer_name = fields.Char(string="Customer", readonly=True)
    phone = fields.Char(string="Number", readonly=True)
    branch_name = fields.Char(string="Branch", readonly=True)
    salesperson_name = fields.Char(string="Salesperson", readonly=True)
    stage_name = fields.Char(string="Stage", readonly=True)
    last_update_date = fields.Datetime(string="Last Update", readonly=True)
    remaining_days = fields.Integer(string="Remaining Days", readonly=True)
    status = fields.Selection(VALIDITY_STATUS, string="Status", readonly=True)
    transfer_date = fields.Datetime(string="Transferable On", readonly=True)
    is_mine = fields.Boolean(readonly=True)
    transferable = fields.Boolean(readonly=True)
    # Plain integers on purpose: no many2one -> no clickable link and no
    # display_name read on records the user is not allowed to access.
    partner_ref = fields.Integer(readonly=True)
    lead_ref = fields.Integer(readonly=True)

    def action_takeover(self):
        """Manual transfer. All checks are re-done server side in the
        takeover methods; the values stored on this line are NOT trusted."""
        self.ensure_one()
        self.lookup_id._check_lookup_access()
        if self.partner_ref:
            self.env['res.partner'].action_takeover_duplicate_partner(self.partner_ref)
        elif self.lead_ref:
            self.env['crm.lead']._alomran_takeover_orphan_lead(self.lead_ref)
        else:
            raise UserError(_("Nothing to transfer."))
        self.lookup_id.action_search()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Transferred"),
                'message': _("The customer has been transferred to you."),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
