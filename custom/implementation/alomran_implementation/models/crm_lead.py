from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, timedelta
import random
from odoo.tools import html2plaintext

from .alomran_validity import NUMBER_KEY_SQL, VALIDITY_STATUS, WON_FOLLOWUP_START_PARAM

OPPORTUNITY_NOTES_MIN_LENGTH = 50


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def init(self):
        super().init()
        # Follow-up of won opportunities required from the first install of
        # this rule on (grace period for the existing won opportunities).
        self._cr.execute("""
            INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
            VALUES (%s, to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'), 1, now(), 1, now())
            ON CONFLICT (key) DO NOTHING
        """, [WON_FOLLOWUP_START_PARAM])
        # Customer matching by number (alomran.validity.tools NUMBER_KEY_SQL)
        for col in ('phone', 'mobile'):
            self._cr.execute(
                f"CREATE INDEX IF NOT EXISTS crm_lead_alomran_{col}_key_idx "
                f"ON crm_lead ({NUMBER_KEY_SQL.format(col=col)})")

    is_tracked = fields.Boolean('Is tracked')

    date = fields.Date('Date')

    referred_by_id = fields.Many2one(
        'res.partner',
        string='Referred By',
        domain="[('customer_rank', '>', 0), ('user_id', '!=', False)]",
        help='Customer who referred this lead (must be a customer assigned to a salesperson).'
    )

    show_referred_field = fields.Boolean(
        string="Show Referred By",
        compute="_compute_show_referred_field",
        store=False
    )


    mobile = fields.Char(
        string="Mobile",
        compute="_compute_mobile",
        inverse="_inverse_mobile",
        readonly=False,
        store=True,
    )

    same_contact_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_duplicate_partners",
        string="Duplicate Phone/Mobile",
    )

    same_name_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_duplicate_partners",
        string="Duplicate Name",
    )

    contact_conflict_label = fields.Char(
        compute="_compute_duplicate_partners",
    )

    # ------------------------------------------------------------------
    # Lead validity (last update / remaining days / Active-Expired)
    # ------------------------------------------------------------------
    alomran_last_update_date = fields.Datetime(
        string="Last Update",
        compute="_compute_alomran_validity",
        compute_sudo=True,
        help="Most recent note, message, completed activity or stage change "
             "on this opportunity.",
    )
    alomran_remaining_days = fields.Integer(
        string="Remaining Days",
        compute="_compute_alomran_validity",
        compute_sudo=True,
        help="Days left before this opportunity expires.",
    )
    alomran_validity_status = fields.Selection(
        VALIDITY_STATUS,
        string="Lead Status",
        compute="_compute_alomran_validity",
        compute_sudo=True,
        search="_search_alomran_validity_status",
    )
    alomran_transfer_date = fields.Datetime(
        string="Transferable On",
        compute="_compute_alomran_validity",
        compute_sudo=True,
    )

    def _compute_alomran_validity(self):
        tools = self.env['alomran.validity.tools']
        real_leads = self.filtered(lambda l: isinstance(l.id, int))
        last_map = tools._get_lead_last_update_map(real_leads)
        for lead in self:
            last_update = last_map.get(lead.id) if isinstance(lead.id, int) else False
            remaining, status, transfer_date = tools._get_validity_info(last_update)
            lead.alomran_last_update_date = last_update
            lead.alomran_remaining_days = remaining
            lead.alomran_validity_status = status if isinstance(lead.id, int) else False
            lead.alomran_transfer_date = transfer_date

    def _search_alomran_validity_status(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            raise UserError(_("Unsupported search on Lead Status."))
        statuses = [value] if isinstance(value, str) else list(value or [])
        ids = self.env['alomran.validity.tools']._get_lead_ids_by_status(statuses)
        return [('id', 'not in' if operator in ('!=', 'not in') else 'in', ids)]

    # ------------------------------------------------------------------
    # Opportunity mandatory data (Notes >= 50 chars, Source on creation)
    # ------------------------------------------------------------------
    def _alomran_enforce_opportunity_rules(self):
        """Rules apply to internal users working from the UI / RPC.
        Superuser-mode flows (website forms, mail gateway, crons, sudo code)
        are not blocked."""
        env = self.env
        return not env.su and env.uid != SUPERUSER_ID and env.user._is_internal()

    def _alomran_check_source_required(self):
        if not self._alomran_enforce_opportunity_rules():
            return
        missing = self.filtered(lambda l: l.type == 'opportunity' and not l.source_id)
        if missing:
            raise ValidationError(_(
                "Source is required when creating an opportunity.\n%s",
                ", ".join(missing.mapped('name')),
            ))

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._alomran_check_source_required()
        leads._alomran_check_notes_length()
        return leads

    def write(self, vals):
        res = super().write(vals)
        # Converting a lead into an opportunity == creating the opportunity
        if vals.get('type') == 'opportunity':
            self._alomran_check_source_required()
        # Old opportunities are only checked when the notes themselves change
        # or a lead is converted, so existing records stay editable.
        if 'description' in vals or vals.get('type') == 'opportunity':
            self._alomran_check_notes_length()
        return res

    @api.depends("partner_id.mobile")
    def _compute_mobile(self):
        super()._compute_mobile()

    def _inverse_mobile(self):
        for lead in self:
            if lead.partner_id and lead.partner_id.mobile != lead.mobile:
                lead.partner_id.mobile = lead.mobile

    @api.depends("partner_id", "partner_id.name", "partner_id.phone", "partner_id.mobile")
    def _compute_duplicate_partners(self):
        Partner = self.env["res.partner"].sudo()

        for lead in self:
            lead.same_contact_partner_id = False
            lead.same_name_partner_id = False
            lead.contact_conflict_label = _("Phone/Mobile")

            if not lead.partner_id:
                continue

            # Duplicate name
            if lead.partner_id.name:
                duplicate_name = Partner.search([
                    ("name", "=", lead.partner_id.name),
                    ("id", "!=", lead.partner_id.id),
                ], limit=1)
                lead.same_name_partner_id = duplicate_name

            # Duplicate phone/mobile
            numbers = list(filter(None, [
                lead.partner_id.phone,
                lead.partner_id.mobile,
            ]))

            if numbers:
                duplicate_contact = Partner.search([
                    ("id", "!=", lead.partner_id.id),
                    "|",
                    ("phone", "in", numbers),
                    ("mobile", "in", numbers),
                ], limit=1)

                lead.same_contact_partner_id = duplicate_contact



    # Branch / salesperson of the existing contact shown in the duplicate warning
    same_contact_owner_info = fields.Char(
        compute='_compute_same_contact_owner_info',
        compute_sudo=True,
    )

    @api.depends('same_contact_partner_id')
    def _compute_same_contact_owner_info(self):
        Partner = self.env['res.partner']
        for rec in self:
            rec.same_contact_owner_info = (
                Partner._duplicate_owner_info(rec.same_contact_partner_id)
                if rec.same_contact_partner_id else False
            )

    @api.depends('source_id')
    def _compute_show_referred_field(self):
        for lead in self:
            lead.show_referred_field = lead.source_id and lead.source_id.name == 'Referral'

    def _alomran_check_notes_length(self):
        enforce = self._alomran_enforce_opportunity_rules()
        for rec in self:
            plain_text = html2plaintext(rec.description or '').strip()
            if rec.type == 'opportunity':
                # Opportunities: notes are mandatory and must be >= 50 chars
                if enforce and len(plain_text) < OPPORTUNITY_NOTES_MIN_LENGTH:
                    raise ValidationError(_(
                        "Opportunity \"%(name)s\" cannot be saved: Notes/Details must contain "
                        "at least %(min)s characters (currently %(count)s).",
                        name=rec.name, min=OPPORTUNITY_NOTES_MIN_LENGTH, count=len(plain_text),
                    ))
            elif plain_text and len(plain_text) < OPPORTUNITY_NOTES_MIN_LENGTH:
                # Leads: previous behaviour kept (only checked when filled)
                raise ValidationError(
                    _("Internal Notes must be at least 50 characters.")
                )

    # Prevent duplicate opportunities with the same customer and title.
    @api.constrains('partner_id', 'name')
    def _check_duplicate_opportunity(self):
        for lead in self:
            if lead.type != 'opportunity' or not lead.partner_id or not lead.name:
                continue

            domain = [
                ('id', '!=', lead.id),
                ('type', '=', 'opportunity'),
                ('partner_id', '=', lead.partner_id.id),
                ('name', '=', lead.name),
            ]
            duplicate = self.search(domain, limit=1)
            if duplicate:
                raise ValidationError(_(
                    "A duplicate opportunity already exists for the same customer with the same title: %s" % lead.name
                ))

    @api.model
    def cron_auto_transfer_inactive_opportunities(self):
        # Public method -> callable through RPC. Only the cron (OdooBot) or
        # an administrator may trigger the mass reassignment.
        if not (self.env.su or self.env.uid == SUPERUSER_ID
                or self.env.user.has_group('base.group_system')):
            raise AccessError(_("You are not allowed to run the opportunity auto-transfer."))
        ICPSudo = self.env['ir.config_parameter'].sudo()
        enabled = ICPSudo.get_param('alomran_implementation.enable_auto_transfer') == 'True'
        duration_days = int(ICPSudo.get_param('alomran_implementation.auto_transfer_duration_days', default=10))

        if not enabled or duration_days <= 0:
            return

        # Calculate the cutoff date
        cutoff_date = fields.Datetime.now() - timedelta(days=duration_days)

        # Search for opportunities in "New" stage (assumption: name='New') and inactive
        leads = self.search([
            ('type', '=', 'opportunity'),
            ('stage_id.name', '=', 'New'),
            ('write_date', '<=', cutoff_date),
            ('user_id', '!=', False),
            ('active', '=', True)
        ])

        all_users = self.env['res.users'].search([('share', '=', False), ('active', '=', True)])

        for lead in leads:
            all_users = self.env['res.users'].search([
                ('share', '=', False),
                ('active', '=', True),
                '|',
                ('company_id', '=', lead.company_id.id),
                ('company_ids', 'in', lead.company_id.id)
            ])

            possible_users = all_users.filtered(lambda u: u.id != lead.user_id.id)
            if not possible_users:
                continue

            new_user = random.choice(possible_users)
            old_user = lead.user_id

            lead.sudo().with_context(force_company=lead.company_id.id).write({'user_id': new_user.id})

            lead.message_post(body=_(
                "Salesperson automatically changed from %s to %s due to inactivity."
            ) % (old_user.name, new_user.name))



    same_contact_partner_inactive = fields.Boolean(
        string='Duplicate Phone/Mobile Contact Inactive 30+ Days',
        compute='_compute_partner_duplicate_inactive',
    )

    @api.depends('same_contact_partner_id', 'partner_id')
    def _compute_partner_duplicate_inactive(self):
        Partner = self.env['res.partner']
        for lead in self:
            if not lead.same_contact_partner_id or not lead.partner_id:
                lead.same_contact_partner_inactive = False
                continue
            duplicates = Partner._get_all_duplicate_contact_partners(lead.partner_id)
            lead.same_contact_partner_inactive = Partner._is_duplicate_inactive_via_crm_leads(
                lead.same_contact_partner_id, duplicates
            )

    def _takeover_duplicate_partner(self, duplicate):
        self.ensure_one()
        if not duplicate:
            raise ValidationError(_("The existing contact could not be found."))

        self.env['res.partner'].action_takeover_duplicate_partner(duplicate.id)
        self.write({'partner_id': duplicate.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Contact Reassigned'),
                'message': _('"%s" has been reassigned to you and linked to this record.') % duplicate.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_takeover_same_contact_partner(self):
        self.ensure_one()
        return self._takeover_duplicate_partner(self.same_contact_partner_id)

    @api.model
    def _alomran_takeover_orphan_lead(self, lead_id):
        """Take over the customer of an opportunity (with or without a contact).
        All the checks are done server side in _take_over_customer."""
        lead = self.sudo().browse(int(lead_id)).exists()
        if not lead:
            raise UserError(_("The lead could not be found."))
        self.env['alomran.validity.tools']._take_over_customer(leads=lead)
        return True


class UtmSource(models.Model):
    _inherit = 'utm.source'

    _order = 'name asc'
