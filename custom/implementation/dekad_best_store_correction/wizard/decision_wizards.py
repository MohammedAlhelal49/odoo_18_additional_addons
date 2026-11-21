from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# سياق best_store_implementation: بيسمح يرجّع قيود وفواتير نقطة البيع لمسودة
ALLOW_POS_RESET = 'bs_allow_pos_invoice_reset'


class BestStoreDecisionMixin(models.AbstractModel):
    """أساس أدوات "التصحيح بعد القرار": المحاسب بيراجع الأسطر وبيختار، والأداة بتعمل القيود."""
    _name = 'bs.decision.mixin'
    _description = 'Best Store Correction Decision'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    journal_id = fields.Many2one(
        'account.journal', string='Journal',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        default=lambda self: self._default_journal())
    state = fields.Selection([('draft', 'To Review'), ('done', 'Done')], default='draft', required=True)
    batch = fields.Char(readonly=True)

    @api.model
    def _default_journal(self):
        journals = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', self.env.company.id)])
        return journals.filtered(lambda j: j.code == 'MISC')[:1] or journals[:1]

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _new_batch(self, prefix):
        return '%s/%s/%s' % (prefix, self.company_id.id, fields.Datetime.now().strftime('%Y%m%d-%H%M%S'))

    def _check_lock_date(self, dates):
        lock_date = self.company_id._get_user_fiscal_lock_date(self.journal_id)
        if any(d and d <= lock_date for d in dates):
            raise UserError(_("Some dates are on or before the lock date (%s).", lock_date))

    def _open_moves(self, moves):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Created Entries"),
            'res_model': moves._name,
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
            'context': {'create': False},
        }

    def _create_entry(self, date, ref, lines, batch, source=None):
        """lines: [(account, balance, product, partner)] بالمجموع صفر."""
        move = self.env['account.move'].with_company(self.company_id).create({
            'bs_correction_source_id': source.id if source else False,
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'date': date,
            'ref': ref,
            'bs_correction_batch': batch,
            'line_ids': [(0, 0, {
                'account_id': account.id,
                'name': ref,
                'debit': max(balance, 0.0),
                'credit': max(-balance, 0.0),
                'product_id': product.id if product else False,
                'partner_id': partner.id if partner else False,
            }) for account, balance, product, partner in lines],
        })
        move.action_post()
        return move


# ---------------------------------------------------------------------------------- Stock Input
class BestStoreStockInputFix(models.TransientModel):
    """رصيد Stock Input المتبقي على منتج (فرق سعر استلام، رصيد افتتاحي، ...): قيد واحد لكل منتج
    مقابل حساب بيختاره المحاسب."""
    _name = 'bs.stock.input.fix'
    _inherit = 'bs.decision.mixin'
    _description = 'Stock Input Balance Fix'

    date = fields.Date(required=True, default=fields.Date.context_today)
    line_ids = fields.One2many('bs.stock.input.fix.line', 'wizard_id')

    def _load_lines(self, balances):
        vals = []
        for (account, product), balance in balances.items():
            expense = product.categ_id.with_company(self.company_id).property_account_expense_categ_id if product else False
            vals.append((0, 0, {
                'account_id': account.id, 'product_id': product.id if product else False,
                'balance': balance, 'counter_account_id': expense.id if expense else False,
            }))
        self.line_ids = vals

    def action_create(self):
        self.ensure_one()
        lines = self.line_ids.filtered('selected')
        if not lines:
            raise UserError(_("Select at least one line."))
        if lines.filtered(lambda l: not l.counter_account_id):
            raise UserError(_("Choose the counterpart account of every selected line."))
        self._check_lock_date([self.date])
        batch = self._new_batch('BSFIX-SI')
        moves = self.env['account.move']
        for line in lines:
            ref = _("Stock Input balance of %s", line.product_id.display_name or line.account_id.display_name)
            moves |= self._create_entry(self.date, ref, [
                (line.account_id, -line.balance, line.product_id, False),
                (line.counter_account_id, line.balance, line.product_id, False),
            ], batch)
        self.write({'state': 'done', 'batch': batch})
        return self._open_moves(moves)


class BestStoreStockInputFixLine(models.TransientModel):
    _name = 'bs.stock.input.fix.line'
    _description = 'Stock Input Balance Fix Line'

    wizard_id = fields.Many2one('bs.stock.input.fix', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    selected = fields.Boolean(string='Apply', default=True)
    account_id = fields.Many2one('account.account', string='Stock Input Account', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    balance = fields.Monetary(string='Balance', readonly=True)
    counter_account_id = fields.Many2one('account.account', string='Counterpart Account')


# ---------------------------------------------------------------------------------- assets
class BestStoreAssetCreate(models.TransientModel):
    """مشتريات أصول ثابتة بدون أصل: بينعمل أصل مسودة لكل سطر فاتورة حسب النموذج المختار
    (العمر الإنتاجي والحسابات)، والمحاسب بيراجعه وبيأكده."""
    _name = 'bs.asset.create'
    _inherit = 'bs.decision.mixin'
    _description = 'Create Fixed Assets'

    model_id = fields.Many2one(
        'account.asset', string='Asset Model',
        domain="[('state', '=', 'model'), ('company_id', '=', company_id)]")
    line_ids = fields.One2many('bs.asset.create.line', 'wizard_id')

    def action_create(self):
        self.ensure_one()
        lines = self.line_ids.filtered('selected')
        if not lines:
            raise UserError(_("Select at least one line."))
        if not self.model_id:
            raise UserError(_("Choose the asset model (useful life and accounts)."))
        model = self.model_id
        assets = self.env['account.asset']
        for line in lines:
            move_line = line.move_line_id
            assets |= self.env['account.asset'].with_company(self.company_id).create({
                'name': move_line.name or move_line.product_id.display_name or move_line.move_id.name,
                'company_id': self.company_id.id,
                'model_id': model.id,
                'original_move_line_ids': [(6, 0, move_line.ids)],
                'acquisition_date': move_line.date,
                'method': model.method,
                'method_number': model.method_number,
                'method_period': model.method_period,
                'method_progress_factor': model.method_progress_factor,
                'prorata_computation_type': model.prorata_computation_type,
                'account_asset_id': move_line.account_id.id,
                'account_depreciation_id': model.account_depreciation_id.id,
                'account_depreciation_expense_id': model.account_depreciation_expense_id.id,
                'journal_id': model.journal_id.id,
            })
        self.state = 'done'
        return self._open_moves(assets) | {'name': _("Draft Assets")}


class BestStoreAssetCreateLine(models.TransientModel):
    _name = 'bs.asset.create.line'
    _description = 'Create Fixed Assets Line'

    wizard_id = fields.Many2one('bs.asset.create', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    selected = fields.Boolean(string='Apply', default=True)
    move_line_id = fields.Many2one('account.move.line', string='Bill Line', readonly=True)
    move_id = fields.Many2one(related='move_line_id.move_id', string='Bill')
    date = fields.Date(related='move_line_id.date')
    name = fields.Char(related='move_line_id.name', string='Description')
    account_id = fields.Many2one(related='move_line_id.account_id')
    amount = fields.Monetary(related='move_line_id.balance', string='Amount')


# ---------------------------------------------------------------------------------- cash differences
class BestStoreCashDifferenceFix(models.TransientModel):
    """فرق صندوق عند إغلاق جلسة انقيّد على حساب غلط (مثلاً حساب موظف): إما بيضل (إذا الموظف
    فعلاً استلم المبلغ) أو بينقل لحساب الخسارة / الربح بقيد تسوية بنفس التاريخ."""
    _name = 'bs.cash.difference.fix'
    _inherit = 'bs.decision.mixin'
    _description = 'POS Cash Difference Fix'

    line_ids = fields.One2many('bs.cash.difference.fix.line', 'wizard_id')

    def action_create(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.decision == 'reclass')
        if not lines:
            raise UserError(_("No line is set to move to the loss / profit account."))
        if lines.filtered(lambda l: not l.target_account_id):
            raise UserError(_("Choose the target account of every line to move."))
        self._check_lock_date(lines.mapped('date'))
        batch = self._new_batch('BSFIX-CASH')
        moves = self.env['account.move']
        for line in lines:
            source = line.move_line_id
            ref = _("Cash difference of %(move)s moved from %(account)s",
                    move=source.move_id.name, account=source.account_id.display_name)
            moves |= self._create_entry(line.date, ref, [
                (source.account_id, -source.balance, False, source.partner_id),
                (line.target_account_id, source.balance, False, False),
            ], batch, source=source.move_id)
        self.write({'state': 'done', 'batch': batch})
        return self._open_moves(moves)


class BestStoreCashDifferenceFixLine(models.TransientModel):
    _name = 'bs.cash.difference.fix.line'
    _description = 'POS Cash Difference Fix Line'

    wizard_id = fields.Many2one('bs.cash.difference.fix', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    move_line_id = fields.Many2one('account.move.line', string='Entry Line', readonly=True)
    move_id = fields.Many2one(related='move_line_id.move_id', string='Entry')
    date = fields.Date(related='move_line_id.date')
    account_id = fields.Many2one(related='move_line_id.account_id', string='Booked On')
    amount = fields.Monetary(related='move_line_id.balance', string='Amount')
    decision = fields.Selection(
        [('keep', 'Keep (the employee received the money)'), ('reclass', 'Move to the loss / profit account')],
        default='keep', required=True)
    target_account_id = fields.Many2one('account.account', string='Target Account',
                                        compute='_compute_target_account', store=True, readonly=False)

    @api.depends('move_line_id')
    def _compute_target_account(self):
        for line in self:
            journal = line.move_line_id.journal_id
            line.target_account_id = (journal.loss_account_id if line.move_line_id.balance > 0
                                      else journal.profit_account_id)


# ---------------------------------------------------------------------------------- duplicate invoices
class BestStoreDuplicateInvoiceFix(models.TransientModel):
    """طلب نقطة بيع إله أكتر من فاتورة مرحّلة (الأصلية ما انلغت وانعملت فاتورة جديدة بعد الإغلاق):
    بتنلغى الفاتورة المكرّرة مع قيد دفعتها وقيد عكس المبيعات تبعها، فما بيتغيّر لا المبيعات ولا الذمم."""
    _name = 'bs.duplicate.invoice.fix'
    _inherit = 'bs.decision.mixin'
    _description = 'Duplicate POS Invoices Fix'

    line_ids = fields.One2many('bs.duplicate.invoice.fix.line', 'wizard_id')

    def _related_moves(self, origin, invoice):
        """قيد دفعة نقطة البيع للفاتورة وقيد عكس المبيعات اللي انعمل معها."""
        Move = self.env['account.move']
        payments = Move.search([('company_id', '=', self.company_id.id), ('state', '=', 'posted'),
                                ('ref', '=like', 'Invoice payment for %s (%s)%%' % (origin, invoice.name))])
        reversals = Move.search([('company_id', '=', self.company_id.id), ('state', '=', 'posted'),
                                 ('ref', '=like', 'Reversal of POS closing entry %% for order %s from session %%' % origin),
                                 ('create_date', '>=', invoice.create_date - timedelta(minutes=5)),
                                 ('create_date', '<=', invoice.create_date + timedelta(minutes=5))])
        return payments | reversals

    def _load_groups(self, groups):
        vals = []
        for origin, invoices in groups.items():
            # نسخة مكرّرة = نفس المبلغ: منقترح إلغاء الأحدث. مبالغ مختلفة = غالباً بيعين مختلفين
            # بنفس اسم الطلب (طلب محذوف): ما منقترح شي، المحاسب بيقرر
            same_amount = len(set(invoices.mapped('amount_total'))) == 1
            for index, invoice in enumerate(invoices.sorted('id')):
                related = self._related_moves(origin, invoice)
                vals.append((0, 0, {
                    'origin': origin, 'invoice_id': invoice.id, 'cancel': same_amount and bool(index),
                    'related_move_ids': [(6, 0, related.ids)],
                    'note': '' if same_amount else _("Different amounts: probably two different sales, check before cancelling."),
                }))
        self.line_ids = vals

    def action_create(self):
        self.ensure_one()
        lines = self.line_ids.filtered('cancel')
        if not lines:
            raise UserError(_("No invoice is selected to cancel."))
        for origin in set(self.line_ids.mapped('origin')):
            if not self.line_ids.filtered(lambda l: l.origin == origin and not l.cancel):
                raise UserError(_("Keep at least one invoice of %s.", origin))
        moves = (lines.invoice_id | lines.related_move_ids).with_context(**{ALLOW_POS_RESET: True})
        moves.button_draft()
        moves.button_cancel()
        for invoice in lines.invoice_id:
            invoice.message_post(body=_("Cancelled by the Best Store correction center: duplicate invoice of %s.",
                                        invoice.invoice_origin))
        self.state = 'done'
        return self._open_moves(moves)


class BestStoreDuplicateInvoiceFixLine(models.TransientModel):
    _name = 'bs.duplicate.invoice.fix.line'
    _description = 'Duplicate POS Invoices Fix Line'

    wizard_id = fields.Many2one('bs.duplicate.invoice.fix', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    origin = fields.Char(string='POS Order', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoice_date = fields.Date(related='invoice_id.invoice_date')
    amount = fields.Monetary(related='invoice_id.amount_total')
    payment_state = fields.Selection(related='invoice_id.payment_state')
    cancel = fields.Boolean(string='Cancel')
    related_move_ids = fields.Many2many('account.move', string='Cancelled With It', readonly=True)
    note = fields.Char(readonly=True)
