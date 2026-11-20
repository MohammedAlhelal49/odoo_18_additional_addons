from odoo import _, models
from odoo.exceptions import UserError

# سياق داخلي: Correct Order / Cancel Order لجلسة مفتوحة بيلغوا الفاتورة ودفعاتها بأنفسهم
ALLOW_POS_RESET = 'bs_allow_pos_invoice_reset'


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _bs_check_session_not_closed(self, action):
        """بعد إغلاق الجلسة، قيد الإغلاق فيه الطلب (مبيعاته أو دفعة فاتورته). إلغاء الطلب أو
        تصحيحه بعدها بيترك قيود غلط: مبيعات ناقصة ورصيد مفتوح على حساب نقطة البيع."""
        closed = self.filtered(lambda o: o.session_id.state == 'closed')
        if closed:
            raise UserError(_(
                "%(action)s is not allowed after the session is closed (%(orders)s).\n"
                "The session closing entry already includes these orders: cancelling or re-invoicing them "
                "leaves wrong entries (missing sales, open POS receivable).\n"
                "Use a refund from the Point of Sale, or a credit note on the invoice.",
                action=action, orders=', '.join(closed.mapped('name'))))

    def action_correct_order(self):
        self._bs_check_session_not_closed(_("Correct Order"))
        return super(PosOrder, self.with_context(**{ALLOW_POS_RESET: True})).action_correct_order()

    def action_cancel_order(self):
        self._bs_check_session_not_closed(_("Cancel Order"))
        return super(PosOrder, self.with_context(**{ALLOW_POS_RESET: True})).action_cancel_order()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _bs_pos_linked_moves(self):
        """فواتير نقطة البيع، قيود دفعاتها، قيود إغلاق الجلسات وقيود عكسها."""
        return self.filtered(lambda m: m.sudo().pos_order_ids or m.sudo().pos_payment_ids
                             or m.sudo().pos_session_ids or m.sudo().reversed_pos_order_id)

    def _bs_check_pos_move_edit(self, action):
        if self.env.su or self.env.context.get(ALLOW_POS_RESET):
            return
        if self.env.user.has_group('best_store_implementation.group_pos_invoice_edit'):
            return
        moves = self._bs_pos_linked_moves()
        if moves:
            raise UserError(_(
                "%(action)s is not allowed on Point of Sale invoices and entries (%(moves)s).\n"
                "Editing them removes the link with the POS payment and the amount ends up recorded twice.\n"
                "To change a sale, make a refund in the Point of Sale or a credit note. "
                "Only users in the group \"Edit Point of Sale Invoices\" can do this.",
                action=action, moves=', '.join(moves.mapped('display_name'))))

    def button_draft(self):
        self._bs_check_pos_move_edit(_("Reset to Draft"))
        return super().button_draft()

    def button_cancel(self):
        self._bs_check_pos_move_edit(_("Cancel"))
        return super().button_cancel()

    def _post(self, soft=True):
        posted = super()._post(soft)
        posted._bs_reconcile_pos_payments()
        return posted

    def _bs_reconcile_pos_payments(self):
        """فاتورة نقطة بيع انرجعت مسودة وانرحّلت من جديد: Odoo بيفك ربطها بدفعات الطلب وما
        برجّعه، فبتطلع غير مدفوعة وبتنسجّل عليها دفعة يدوية مكرّرة. منرجّع الربط هون.
        بأول ترحيل من نقطة البيع ما في دفعات لسا (بتنعمل بعد الفاتورة)، فما بيتغيّر شي."""
        for move in self.filtered(lambda m: m.is_invoice() and m.sudo().pos_order_ids):
            receivable = move.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled)
            if not receivable:
                continue
            payment_moves = move.sudo().pos_order_ids.payment_ids.account_move_id.filtered(
                lambda m: m.state == 'posted')
            payment_lines = payment_moves.line_ids.filtered(
                lambda l: l.account_id in receivable.account_id and not l.reconciled
                and l.partner_id.commercial_partner_id == move.commercial_partner_id
                and l.amount_residual * receivable[0].amount_residual < 0)
            if payment_lines:
                (receivable | payment_lines).with_company(move.company_id).reconcile()
