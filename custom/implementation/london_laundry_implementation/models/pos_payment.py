from odoo import api, fields, models


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    # تحصيل دين: سطر On Credit سالب على طلب التحصيل، مربوط بالطلب اللي عم يندفع.
    # عند إغلاق الجلسة، قيد الذمم تبع هالسطر بيتطابق مع فاتورة هالطلب بالضبط.
    laundry_collected_order_id = fields.Many2one(
        'pos.order', string='Collected Order', index='btree_not_null', copy=False, readonly=True,
        help='On Credit order this collection payment pays.')
    # المتبقي على الطلب لحظة التحصيل (قبل هالدفعة): إيصال التحصيل بيطلع بنفس الأرقام لو انطبع مرة تانية
    laundry_collected_due = fields.Monetary(string='Due Before Collection', copy=False, readonly=True)
    # بيتعبّى بس لما المطابقة مع الفاتورة تنجح فعلاً (عند إغلاق الجلسة)
    laundry_reconciled = fields.Boolean(string='Collection Reconciled', copy=False, readonly=True)
    # اسم الطلب للإيصال لما ينطبع مرة تانية والطلب الأصلي مو محمّل بالـ POS
    laundry_collected_order_name = fields.Char(
        related='laundry_collected_order_id.name', string='Collected Order Ref')
    # إلغاء تحصيل: سطر On Credit موجب على طلب الإلغاء، بيلغي سطر التحصيل الأصلي (بنفس الجلسة)
    laundry_reversed_payment_id = fields.Many2one(
        'pos.payment', string='Cancelled Collection Line', index='btree_not_null', copy=False, readonly=True)
    # تفاصيل الطلب المدفوع (للإيصال لما ينطبع مرة تانية والطلب الأصلي مو محمّل بالـ POS)
    laundry_collected_details = fields.Json(
        string='Collected Order Details', compute='_compute_laundry_collected_details')

    @api.depends('laundry_collected_order_id')
    def _compute_laundry_collected_details(self):
        for payment in self:
            order = payment.sudo().laundry_collected_order_id
            payment.laundry_collected_details = order._laundry_receipt_details() if order else False
