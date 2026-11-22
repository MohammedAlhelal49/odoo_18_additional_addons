from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

INVOICE_TYPES = ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
# الفواتير اللي اتطابقت مع قيد الدفعة (من الجهتين)
RECONCILED_PATHS = (
    'move_id.line_ids.matched_debit_ids.debit_move_id.move_id',
    'move_id.line_ids.matched_credit_ids.credit_move_id.move_id',
)
# سياق لتجاوز منع الدفعة المكرّرة (للحالات الاستثنائية من الكود)
ALLOW_DUPLICATE_PAYMENT = 'bs_allow_duplicate_payment'


def _x2many_search(paths, operator, value, extra=None):
    """بحث على فواتير مربوطة عبر أكتر من مسار: مربوط / مش مربوط / برقم الفاتورة."""
    extra = extra or []
    if operator in ('=', '!=') and not value:
        linked = expression.OR([[(f'{path}.id', '!=', False)] + [(f'{path}.{f}', op, v) for f, op, v in extra]
                                for path in paths])
        return linked if operator == '!=' else ['!'] + linked
    if operator in ('ilike', 'like', '=', 'not ilike'):
        positive = 'ilike' if operator == 'not ilike' else operator
        matches = expression.OR([[(f'{path}.name', positive, value)] + [(f'{path}.{f}', op, v) for f, op, v in extra]
                                 for path in paths])
        return ['!'] + matches if operator == 'not ilike' else matches
    if operator == 'in':
        return expression.OR([[(f'{path}.id', 'in', value)] for path in paths])
    raise UserError(_("Unsupported search on invoices: %s", operator))


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bs_invoice_ids = fields.Many2many(
        'account.move', string='Linked Invoices', compute='_compute_bs_invoice_ids',
        search='_search_bs_invoice_ids',
        help="Invoices this payment is linked to (registered from the invoice or matched with it).")

    @api.depends('invoice_ids', 'reconciled_invoice_ids', 'reconciled_bill_ids')
    def _compute_bs_invoice_ids(self):
        for payment in self:
            payment.bs_invoice_ids = (payment.invoice_ids | payment.reconciled_invoice_ids
                                      | payment.reconciled_bill_ids).filtered(lambda m: m.state != 'cancel')

    def _search_bs_invoice_ids(self, operator, value):
        # "مش مربوطة" = كل الدفعات ناقص المربوطة (النفي جوّا مسارات x2many بيضيّع السجلات الفاضية)
        if (operator == '=' and not value) or operator == 'not ilike':
            positive = self._search_bs_invoice_ids('!=' if operator == '=' else 'ilike', value)
            return [('id', 'not in', self._search(positive))]
        return expression.OR([
            _x2many_search(RECONCILED_PATHS, operator, value, extra=[('move_type', 'in', INVOICE_TYPES)]),
            _x2many_search(('invoice_ids',), operator, value),
        ])

    # ------------------------------------------------------------ منع الدفعة المكرّرة
    def _bs_target_invoices(self):
        """الفواتير اللي الدفعة مسجّلة عليها: من شاشة "Register Payment"، أو برقمها بالـ Memo."""
        self.ensure_one()
        invoices = self.invoice_ids.filtered(lambda m: m.is_sale_document(True) and m.state == 'posted')
        if not invoices and self.memo:
            invoices = self.env['account.move'].search([
                ('company_id', '=', self.company_id.id), ('name', '=', self.memo.strip()),
                ('move_type', 'in', ('out_invoice', 'out_receipt')), ('state', '=', 'posted'),
                ('commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
            ])
        return invoices

    @api.model
    def _bs_check_invoice_payable(self, invoices, amount, currency):
        """فاتورة مدفوعة بالكامل (أو مقبوضة بنقطة البيع) ما بتنقبل عليها دفعة تانية؛
        المدفوعة جزئياً بتنقبل بس لحد المبلغ الباقي."""
        for invoice in invoices:
            if invoice.payment_state in ('paid', 'in_payment', 'reversed'):
                raise UserError(_("Invoice %s is already paid: another payment cannot be registered on it.",
                                  invoice.name))
            orders = invoice.sudo().pos_order_ids if 'pos_order_ids' in invoice._fields else self.env['pos.order']
            received = sum(orders.payment_ids.filtered(
                lambda p: p.payment_method_id.type != 'pay_later').mapped('amount'))
            if orders and invoice.currency_id.compare_amounts(received, invoice.amount_total) >= 0:
                raise UserError(_(
                    "Invoice %(inv)s was already paid in the Point of Sale (%(amount)s): "
                    "registering another payment would record the money twice.",
                    inv=invoice.name, amount=invoice.currency_id.format(received)))
        residual = sum(invoices.mapped('amount_residual'))
        if invoices and currency.compare_amounts(amount, residual) > 0:
            raise UserError(_(
                "The payment (%(amount)s) is more than what is left to pay on %(invs)s (%(residual)s).",
                amount=currency.format(amount), invs=', '.join(invoices.mapped('name')),
                residual=currency.format(residual)))

    def action_post(self):
        if not self.env.context.get(ALLOW_DUPLICATE_PAYMENT):
            for payment in self.filtered(lambda p: p.payment_type == 'inbound' and p.partner_type == 'customer'
                                         and not p.move_id.pos_session_ids):
                invoices = payment._bs_target_invoices()
                if invoices:
                    self._bs_check_invoice_payable(invoices, payment.amount, payment.currency_id)
        return super().action_post()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        if not self.env.context.get(ALLOW_DUPLICATE_PAYMENT):
            invoices = self.line_ids.move_id.filtered(lambda m: m.is_sale_document(True))
            if invoices and self.payment_type == 'inbound':
                # فرق الدفعة بيتسكّر بقيد تسوية (write-off): مش دفعة زايدة
                amount = self.amount if self.payment_difference_handling != 'reconcile' else 0.0
                self.env['account.payment']._bs_check_invoice_payable(invoices, amount, self.currency_id)
        # الفحص عملناه هون: ترحيل الدفعات اللي بتنعمل من هالشاشة ما بيعيده
        return super(AccountPaymentRegister, self.with_context(**{ALLOW_DUPLICATE_PAYMENT: True}))._create_payments()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bs_invoice_ids = fields.Many2many(
        'account.move', string='Invoices', compute='_compute_bs_invoice_ids', search='_search_bs_invoice_ids',
        help="Invoices of the sales order, purchase order or POS order of this transfer.")

    def _bs_invoice_paths(self):
        paths = []
        for path, field in (('sale_id.invoice_ids', 'sale_id'), ('purchase_id.invoice_ids', 'purchase_id'),
                            ('pos_order_id.account_move', 'pos_order_id')):
            if field in self._fields:
                paths.append(path)
        return paths

    def _compute_bs_invoice_ids(self):
        for picking in self:
            invoices = self.env['account.move']
            for path in picking._bs_invoice_paths():
                invoices |= picking.mapped(path)
            picking.bs_invoice_ids = invoices.filtered(lambda m: m.state == 'posted')

    def _search_bs_invoice_ids(self, operator, value):
        if (operator == '=' and not value) or operator == 'not ilike':
            positive = self._search_bs_invoice_ids('!=' if operator == '=' else 'ilike', value)
            return [('id', 'not in', self._search(positive))]
        return _x2many_search(self._bs_invoice_paths(), operator, value, extra=[('state', '=', 'posted')])
