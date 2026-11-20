# -*- coding: utf-8 -*-
# تحصيل دين الزبون (On Credit) من نقطة البيع
# (منقولة من london_laundry_implementation: "Collect Payment")
#
# طلب التحصيل: طلب فاضي بدون أصناف وبدون فاتورة، فيه سطر On Credit سالب لكل طلب عم يندفع
# (مربوط فيه) + الدفع الفعلي (كاش / فيزا / تحويل). عند إغلاق الجلسة كل سطر بيتطابق مع فاتورة طلبه.
# إلغاء التحصيل (للمدير، بنفس الجلسة): طلب معاكس، On Credit موجب لكل طلب + المصاري بترجع.
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    # سطر On Credit سالب على طلب التحصيل، مربوط بالطلب اللي عم يندفع
    bs_collected_order_id = fields.Many2one(
        'pos.order', string='Collected Order', index='btree_not_null', copy=False, readonly=True,
        help='On Credit order this collection payment pays.')
    # المتبقي على الطلب لحظة التحصيل (قبل هالدفعة): للإيصال لو انطبع مرة تانية
    bs_collected_due = fields.Monetary(string='Due Before Collection', copy=False, readonly=True)
    # بيتعبّى بس لما المطابقة مع الفاتورة تنجح فعلاً (عند إغلاق الجلسة)
    bs_reconciled = fields.Boolean(string='Collection Reconciled', copy=False, readonly=True)
    # اسم الطلب للإيصال لما ينطبع مرة تانية والطلب الأصلي مو محمّل بالـ POS
    bs_collected_order_name = fields.Char(
        related='bs_collected_order_id.name', string='Collected Order Ref')
    # إلغاء تحصيل: سطر On Credit موجب على طلب الإلغاء، بيلغي سطر التحصيل الأصلي
    bs_reversed_payment_id = fields.Many2one(
        'pos.payment', string='Cancelled Collection Line', index='btree_not_null', copy=False, readonly=True)
    # تفاصيل الطلب المدفوع (للإيصال لما ينطبع مرة تانية والطلب الأصلي مو محمّل بالـ POS)
    bs_collected_details = fields.Json(
        string='Collected Order Details', compute='_compute_bs_collected_details')

    @api.depends('bs_collected_order_id')
    def _compute_bs_collected_details(self):
        for payment in self:
            order = payment.sudo().bs_collected_order_id
            payment.bs_collected_details = order._bs_receipt_details() if order else False


class PosOrder(models.Model):
    _inherit = 'pos.order'

    bs_credit_amount = fields.Monetary(
        string='On Credit Amount', compute='_compute_bs_collection', store=True,
        help='Part of the order paid with a customer-account (pay later) payment method.')
    bs_collection_status = fields.Selection(
        selection=[
            ('paid', 'Paid'),
            ('credit_unpaid', 'On Credit - Unpaid'),
            ('credit_partial', 'On Credit - Partially Paid'),
            ('credit_paid', 'On Credit - Collected'),
            ('collection', 'Collection'),
            ('collection_cancelled', 'Collection - Cancelled'),
            ('collection_reversal', 'Collection Reversal'),
        ],
        string='Collection Status', compute='_compute_bs_collection', store=True,
        help='Paid: settled at the counter (cash, card, transfer).\n'
             'On Credit: sold on the customer account; the status follows the invoice payment '
             'and the collections taken at the POS.\n'
             'Collection: a payment collected at the POS for earlier On Credit orders.\n'
             'Collection Reversal: cancels a collection of the same session (money given back).')
    bs_collection_payment_ids = fields.One2many(
        'pos.payment', 'bs_collected_order_id', string='Collections', readonly=True)
    bs_is_collection = fields.Boolean(
        string='Is Collection', compute='_compute_bs_collection', store=True,
        help='Order created at the POS to collect earlier On Credit orders (no products, no invoice).')
    # انقبضت بجلسة لسا ما انطابقت مع الفاتورة (المطابقة بتصير عند إغلاق الجلسة)
    bs_pending_collection = fields.Monetary(
        string='Pending Collection', compute='_compute_bs_collection', store=True,
        help='Collected at the POS but not reconciled with the invoice yet (done when the session closes).')
    bs_reversed_order_id = fields.Many2one(
        'pos.order', string='Cancelled Collection', index='btree_not_null', copy=False, readonly=True)
    bs_reversal_order_ids = fields.One2many(
        'pos.order', 'bs_reversed_order_id', string='Collection Cancellations', readonly=True)
    # رصيد الزبون (كل طلباته على الحساب) بعد هالتحصيل: بيطلع على الإيصال
    bs_partner_balance = fields.Monetary(string='Customer Balance After', copy=False, readonly=True)
    bs_credit_remaining = fields.Monetary(
        string='Remaining On Credit', compute='_compute_bs_collection', store=True,
        help='Amount the customer still owes on this order, collections taken at the POS included.')

    @api.depends('state', 'payment_ids.amount', 'payment_ids.payment_method_id.journal_id',
                 'payment_ids.bs_collected_order_id',
                 'account_move.state', 'account_move.payment_state', 'account_move.amount_residual',
                 'bs_collection_payment_ids.amount', 'bs_collection_payment_ids.bs_reconciled',
                 'bs_collection_payment_ids.pos_order_id.state',
                 'bs_reversed_order_id', 'bs_reversal_order_ids.state')
    def _compute_bs_collection(self):
        for order in self:
            # أسطر التحصيل وإلغائه (مربوطة بطلب) مو بيع على الحساب
            credit = sum(order.payment_ids.filtered(
                lambda p: p.payment_method_id.type == 'pay_later' and not p.bs_collected_order_id
            ).mapped('amount'))
            credit = max(credit, 0.0)
            order.bs_credit_amount = credit
            order.bs_is_collection = bool(order.payment_ids.bs_collected_order_id)
            pending = -sum(order.bs_collection_payment_ids.filtered(
                lambda p: not p.bs_reconciled and p.pos_order_id.state not in ('draft', 'cancel')
            ).mapped('amount'))
            order.bs_pending_collection = pending
            invoice = order.account_move
            if order.currency_id.is_zero(credit):
                remaining = 0.0
            elif invoice.state == 'posted':
                remaining = max(invoice.amount_residual - pending, 0.0)
            else:
                remaining = max(credit - pending, 0.0)
            order.bs_credit_remaining = remaining

            if order.state in ('draft', 'cancel'):
                order.bs_collection_status = False
            elif order.bs_reversed_order_id:
                order.bs_collection_status = 'collection_reversal'
            elif order.bs_is_collection and order.bs_reversal_order_ids.filtered(
                    lambda o: o.state not in ('draft', 'cancel')):
                order.bs_collection_status = 'collection_cancelled'
            elif order.bs_is_collection:
                order.bs_collection_status = 'collection'
            elif order.currency_id.is_zero(credit):
                order.bs_collection_status = 'paid'
            elif invoice.payment_state in ('paid', 'in_payment', 'reversed') or order.currency_id.is_zero(remaining):
                order.bs_collection_status = 'credit_paid'
            elif invoice.payment_state == 'partial' or not order.currency_id.is_zero(pending):
                order.bs_collection_status = 'credit_partial'
            else:
                order.bs_collection_status = 'credit_unpaid'

    def _bs_receipt_details(self):
        """تفاصيل الطلب لإيصال التحصيل وإلغائه: التاريخ والأصناف والمجموع (شامل الضريبة)."""
        self.ensure_one()
        return {
            'date': fields.Datetime.to_string(self.date_order),
            'total': self.amount_total,
            'lines': [{
                'name': line.full_product_name or line.product_id.display_name,
                'qty': line.qty,
                'price_unit': line.price_subtotal_incl / line.qty if line.qty else 0.0,
                'price': line.price_subtotal_incl,
            } for line in self.lines],
        }

    @api.model
    def get_bs_credit_orders(self, partner_id, order_ids=None):
        """طلبات الزبون اللي عليها مصاري وإلها فاتورة، لنافذة "Collect Payment" بالـ POS.

        order_ids: بس هالطلبات (فحص المتبقي قبل Validate).
        الطلبات اللي ما إلها فاتورة ما بتنحصّل من هون: منرجّع عددها بس.
        """
        partner = self.env['res.partner'].browse(partner_id).commercial_partner_id
        domain = [
            ('partner_id', 'child_of', partner.id),
            ('bs_collection_status', 'in', ('credit_unpaid', 'credit_partial')),
            ('company_id', 'in', self.env.companies.ids),
        ]
        all_orders = self.search(domain, order='date_order, id')
        # رصيد الزبون: كل اللي عليه، للإيصال
        total_due = sum(all_orders.mapped('bs_credit_remaining'))
        orders = all_orders if order_ids is None else all_orders.filtered(lambda o: o.id in order_ids)
        result, without_invoice = [], 0
        for order in orders:
            invoice = order.sudo().account_move
            if invoice.state != 'posted':
                without_invoice += 1
                continue
            if order.currency_id.is_zero(order.bs_credit_remaining):
                continue
            result.append({
                'id': order.id,
                'name': order.name,
                'pos_reference': order.pos_reference or '',
                'date_order': fields.Datetime.to_string(order.date_order),
                'invoice': invoice.name,
                'amount_total': order.amount_total,
                'credit_amount': order.bs_credit_amount,
                'remaining': order.bs_credit_remaining,
            })
        return {'orders': result, 'without_invoice': without_invoice, 'total_due': total_due}

    @api.model
    def _bs_is_pos_manager(self, session, employee_id):
        """مدير بالـ POS: نفس دور pos_hr ("manager") = موظف بـ Advanced rights، أو مستخدمه مدير نقطة بيع."""
        config = session.config_id
        if not config.module_pos_hr:
            return self.env.user.has_group('point_of_sale.group_pos_manager')
        employee = self.env['hr.employee'].sudo().browse(employee_id or 0).exists()
        if not employee:
            return False
        return bool(employee in config.advanced_employee_ids or (
            employee.user_id and employee.user_id.has_group('point_of_sale.group_pos_manager')))

    @api.model
    def get_bs_collection_cancel(self, order_id, session_id, employee_id=None):
        """هل فينا نلغي هالتحصيل؟ بنفس الجلسة المفتوحة بس، ومرة وحدة، وقبل المطابقة.

        بيرجّع الدفعات اللي لازم تنعكس (On Credit المربوطة بالطلبات + الدفع الفعلي صافي لكل طريقة).
        """
        order = self.browse(order_id).exists()
        if not order or not order.bs_is_collection or order.bs_reversed_order_id:
            return {'error': _("This order is not a collection.")}
        if order.bs_reversal_order_ids.filtered(lambda o: o.state not in ('draft', 'cancel')):
            return {'error': _("This collection is already cancelled.")}
        if not self._bs_is_pos_manager(order.session_id, employee_id):
            return {'error': _("Only a manager can cancel a collection.")}
        if order.session_id.id != session_id or order.session_id.state != 'opened':
            return {'error': _("A collection can only be cancelled in the session where it was taken, "
                               "before the session is closed. Ask the accountant.")}
        credit_lines = order.payment_ids.filtered('bs_collected_order_id')
        if any(credit_lines.mapped('bs_reconciled')):
            return {'error': _("This collection is already matched with the invoices. Ask the accountant.")}
        methods = {}
        for payment in order.payment_ids - credit_lines:
            methods[payment.payment_method_id.id] = methods.get(payment.payment_method_id.id, 0.0) + payment.amount
        return {
            'credit_lines': [{
                'id': p.id,
                'method_id': p.payment_method_id.id,
                'amount': p.amount,
                'target_id': p.bs_collected_order_id.id,
                'due': p.bs_collected_due,
            } for p in credit_lines],
            'payments': [{'method_id': m, 'amount': a} for m, a in methods.items()
                         if not order.currency_id.is_zero(a)],
        }


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_pay_later_receivable_lines(self, data):
        data = super()._create_pay_later_receivable_lines(data)
        # On Credit مفعّل عليه split_transactions: سطر ذمم لكل دفعة، بنفس ترتيب الإنشاء
        # (الـ combine أول، بعدين الـ split). منحفظ سطر كل دفعة تحصيل لنطابقه مع فاتورة طلبها.
        split = data.get('split_receivables_pay_later') or {}
        combine = data.get('combine_receivables_pay_later') or {}
        lines = data.get('pay_later_move_lines') or self.env['account.move.line']
        split_lines = lines[len(combine):]
        data['bs_collection_lines'] = {
            payment: line
            for payment, line in zip(split.keys(), split_lines)
            if payment.bs_collected_order_id
        } if len(split_lines) == len(split) else {}
        if len(split_lines) != len(split):
            _logger.warning("Session %s: pay-later receivable lines do not match the payments; "
                            "collections are left unreconciled.", self.name)
        return data

    def _reconcile_account_move_lines(self, data):
        data = super()._reconcile_account_move_lines(data)
        self._bs_reconcile_collections(data.get('bs_collection_lines') or {})
        return data

    def _bs_reconcile_collections(self, collection_lines):
        """كل دفعة تحصيل بتنطابق مع فاتورة الطلب اللي اندفع.

        أي مشكلة ما بتوقف إغلاق الجلسة: الدفعة بتضل "معلّقة" (bs_reconciled = False)
        ومنكتب السبب على الجلسة، والمبلغ بيضل رصيد للزبون لحتى المحاسب يطابقه يدوياً.
        """
        problems = []
        # إلغاء تحصيل بنفس الجلسة: سطر الإلغاء بيتطابق مع سطر التحصيل الأصلي (صافي صفر)
        for payment, line in list(collection_lines.items()):
            original = payment.bs_reversed_payment_id
            if not original:
                continue
            collection_lines.pop(payment)
            original_line = collection_lines.pop(original, None)
            label = payment.bs_collected_order_id.name
            if not original_line:
                problems.append(_("%(order)s: cancelled collection %(original)s is not in this session.",
                                  order=label, original=original.pos_order_id.name))
                continue
            try:
                with self.env.cr.savepoint():
                    (line | original_line).with_context(no_cash_basis=True).reconcile()
                    (payment | original).bs_reconciled = True
            except Exception as error:  # noqa: BLE001 - never block the session closing
                _logger.exception("Session %s: cannot match collection cancel of %s", self.name, label)
                self.env.invalidate_all()
                problems.append(_("%(order)s: %(error)s", order=label, error=error))

        for payment, line in collection_lines.items():
            target = payment.bs_collected_order_id
            invoice = target.account_move
            label = target.name
            if invoice.state != 'posted':
                problems.append(_("%(order)s: no posted invoice.", order=label))
                continue
            invoice_lines = invoice.line_ids.filtered(
                lambda l: l.account_id == line.account_id and not l.reconciled)
            if not invoice_lines:
                problems.append(_("%(order)s: invoice %(invoice)s is already paid.",
                                  order=label, invoice=invoice.name))
                continue
            if invoice.currency_id.compare_amounts(-payment.amount, invoice.amount_residual) > 0:
                problems.append(_("%(order)s: collected %(paid)s but only %(due)s was due; "
                                  "the difference stays as customer credit.",
                                  order=label, paid=-payment.amount, due=invoice.amount_residual))
            try:
                with self.env.cr.savepoint():
                    (line | invoice_lines).with_context(no_cash_basis=True).reconcile()
                    payment.bs_reconciled = True
            except Exception as error:  # noqa: BLE001 - never block the session closing
                _logger.exception("Session %s: cannot reconcile collection of %s", self.name, label)
                self.env.invalidate_all()
                problems.append(_("%(order)s: %(error)s", order=label, error=error))
        if problems:
            self.message_post(body=_(
                "Collections not fully matched with their invoices (to check by the accountant):\n%s",
                "\n".join(problems)))
