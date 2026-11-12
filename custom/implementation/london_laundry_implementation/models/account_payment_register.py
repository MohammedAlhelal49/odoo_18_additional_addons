from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # الفواتير اللي فيها تحصيل بالـ POS لسا ما انطابق: تنبيه قبل تسجيل الدفعة مرة تانية
    laundry_pending_collection = fields.Monetary(
        string='Collected at POS (not matched yet)', compute='_compute_laundry_pending_collection')
    laundry_pending_sessions = fields.Char(compute='_compute_laundry_pending_collection')

    @api.depends('line_ids')
    def _compute_laundry_pending_collection(self):
        for wizard in self:
            moves = wizard.line_ids.move_id
            wizard.laundry_pending_collection = sum(moves.mapped('laundry_pending_collection'))
            sessions = {name for value in moves.mapped('laundry_pending_sessions') for name in value.split(', ') if name}
            wizard.laundry_pending_sessions = ", ".join(sorted(sessions))
