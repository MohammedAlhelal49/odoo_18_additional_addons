from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .res_partner import laundry_number_variants


class LaundryPrepaidOpening(models.Model):
    """أرصدة مسبقة قديمة (من قبل النظام): بتنزاد على رصيد الزبون لما تترحّل.

    القيد: مدين حساب الافتتاح (الأرباح غير الموزعة افتراضياً) / دائن رصيد الزبائن المسبق باسم الزبون.
    """
    _name = 'london.prepaid.opening'
    _description = 'Opening Prepaid Balance'
    _order = 'date desc, id desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True)
    # للاستيراد من Excel: إذا ما في زبون، منلاقيه برقم الموبايل
    mobile = fields.Char(string='Mobile')
    amount = fields.Monetary(string='Balance', required=True, help='Balance the customer has today, bonus included.')
    bonus = fields.Monetary(
        string='Bonus Included',
        help='Part of the balance that is bonus. It is deducted if the customer asks for a refund.')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    note = fields.Char(string='Note')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default='draft', required=True, readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    counterpart_account_id = fields.Many2one(
        'account.account', string='Counterpart Account',
        default=lambda self: self.env.company.get_unaffected_earnings_account(),
        help='Debited with the opening balances (default: undistributed profits/losses).')
    journal_id = fields.Many2one(
        'account.journal', string='Journal', domain=[('type', '=', 'general')], default=lambda self: self._default_journal())
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    _sql_constraints = [
        ('amount_positive', 'CHECK(amount > 0)', 'The balance must be positive.'),
        ('bonus_valid', 'CHECK(bonus >= 0 AND bonus <= amount)', 'The bonus must be between 0 and the balance.'),
    ]

    @api.model
    def _default_journal(self):
        """دفتر القيود المتنوعة (JV / MISC)، وإلا أول دفتر عام."""
        Journal = self.env['account.journal']
        domain = [('type', '=', 'general'), ('company_id', '=', self.env.company.id)]
        return Journal.search(domain + [('code', 'in', ('JV', 'MISC'))], limit=1) or Journal.search(domain, limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        Partner = self.env['res.partner']
        for vals in vals_list:
            if not vals.get('partner_id') and vals.get('mobile'):
                variants = list(laundry_number_variants(vals['mobile']))
                partner = Partner.search(['|', ('mobile', 'in', variants), ('phone', 'in', variants)], limit=1)
                if not partner:
                    raise UserError(_("No customer with the mobile number %s.", vals['mobile']))
                vals['partner_id'] = partner.id
        return super().create(vals_list)

    def unlink(self):
        if any(record.state == 'posted' for record in self):
            raise UserError(_("A posted opening balance cannot be deleted. Reset it to draft first."))
        return super().unlink()

    def action_post(self):
        methods = self.env['pos.payment.method']._laundry_prepaid_methods()
        if 'balance' not in methods:
            raise UserError(_("The laundry prepaid balance is not set up. "
                              "Point of Sale > Settings > Laundry Prepaid Balance > Set Up."))
        deposit = methods['balance'].outstanding_account_id
        for record in self.filtered(lambda r: r.state == 'draft'):
            if not record.counterpart_account_id or not record.journal_id:
                raise UserError(_("Set the journal and the counterpart account of %s.", record.partner_id.display_name))
            label = _("Opening prepaid balance - %s", record.partner_id.display_name)
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': record.journal_id.id,
                'date': record.date,
                'ref': label,
                'line_ids': [
                    (0, 0, {'account_id': record.counterpart_account_id.id, 'name': label, 'debit': record.amount,
                            'partner_id': record.partner_id.commercial_partner_id.id}),
                    (0, 0, {'account_id': deposit.id, 'name': label, 'credit': record.amount,
                            'partner_id': record.partner_id.commercial_partner_id.id}),
                ],
            })
            move.action_post()
            record.write({'state': 'posted', 'move_id': move.id})

    def action_reset_draft(self):
        for record in self.filtered(lambda r: r.state == 'posted'):
            if record.move_id:
                record.move_id.button_draft()
                record.move_id.unlink()
            record.state = 'draft'
