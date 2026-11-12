from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# ساعة التسليم المتوقعة (بدون دقائق): 00:00 … 23:00
EXPECTED_HOURS = [('%02d' % hour, '%02d:00' % hour) for hour in range(24)]
# كيف بترجع الملابس للزبون: معلّقة على تعليقة، أو مطوية بكيس
PACKING_TYPES = [('hanger', 'Hanger'), ('fold', 'Fold')]
# الرفوف بالمحل: من 1 لـ 9
SHELVES = [str(number) for number in range(1, 10)]


class AccountMove(models.Model):
    _inherit = 'account.move'

    laundry_expected_delivery = fields.Date(string='Expected Delivery', copy=False)
    laundry_expected_hour = fields.Selection(EXPECTED_HOURS, string='Expected Hour', copy=False)
    laundry_delivery_method_id = fields.Many2one('london.delivery.method', string='Delivery Method', copy=False)
    laundry_packing = fields.Selection(PACKING_TYPES, string='Hanger / Fold', copy=False, tracking=True)
    laundry_shelf = fields.Char(string='Shelf', copy=False, tracking=True)
    # (قديم: أسماء موصّلين بالكتابة، انحلّ محلّه الموظف تحت)
    laundry_delivery_person_id = fields.Many2one(
        'london.delivery.person', string='Delivery Person (old)', copy=False)
    # مين سلّم الطلب: الكاشير اللي ضغط "Delivered" بالـ POS (أو موظف المستخدم من الباك إند)
    laundry_delivered_employee_id = fields.Many2one(
        'hr.employee', string='Delivered By', copy=False, tracking=True)
    laundry_delivered = fields.Boolean(string='Delivered', copy=False, tracking=True)
    laundry_delivery_datetime = fields.Datetime(
        string='Delivery Date & Time',
        compute='_compute_laundry_delivery_datetime',
        store=True,
        copy=False,
    )

    def action_laundry_whatsapp_ready(self):
        """واتساب "الطلب جاهز" من الفاتورة (طلب الـ POS تبعها)."""
        self.ensure_one()
        order = self.sudo().pos_order_ids[:1]
        if not order:
            raise UserError(_("This invoice does not come from a POS order."))
        return order.action_laundry_whatsapp_ready()

    @api.constrains('laundry_shelf')
    def _check_laundry_shelf(self):
        for move in self:
            if move.laundry_shelf and move.laundry_shelf.strip() not in SHELVES:
                raise ValidationError(_("The shelf must be a number from 1 to 9."))

    def write(self, vals):
        if 'laundry_shelf' in vals and vals['laundry_shelf']:
            vals['laundry_shelf'] = str(vals['laundry_shelf']).strip()
        # تسليم من الباك إند: "Delivered By" = موظف المستخدم الحالي (إذا ما انبعت غيره)، وبيفضى عند الإلغاء
        if 'laundry_delivered' in vals and 'laundry_delivered_employee_id' not in vals:
            vals['laundry_delivered_employee_id'] = (
                self.env.user.employee_id.id if vals['laundry_delivered'] else False)
        return super().write(vals)

    @api.depends('laundry_delivered')
    def _compute_laundry_delivery_datetime(self):
        # تاريخ ووقت التسليم = لحظة تفعيل الـ checkbox، وبيفضى عند إلغائه
        for move in self:
            move.laundry_delivery_datetime = fields.Datetime.now() if move.laundry_delivered else False

    # قبض بالـ POS (تحصيل دين) ولسا ما انطابق مع الفاتورة: بيصير عند إغلاق جلسة الصندوق.
    # منعرضه على الفاتورة حتى المحاسب ما يسجّل نفس الدفعة مرة تانية من الباك إند.
    laundry_pending_collection = fields.Monetary(
        string='Collected at POS (not matched yet)', compute='_compute_laundry_pending_collection')
    laundry_pending_sessions = fields.Char(
        string='POS Sessions', compute='_compute_laundry_pending_collection')

    # مدفوعة كاملة (أو انحصّلت كاملة بالـ POS ولسا ناطرة إغلاق الجلسة): لتلوين لائحة الفواتير
    laundry_is_paid = fields.Boolean(string='Fully Paid', compute='_compute_laundry_is_paid')

    @api.depends('state', 'payment_state', 'amount_residual', 'laundry_pending_collection')
    def _compute_laundry_is_paid(self):
        for move in self:
            move.laundry_is_paid = move.payment_state in ('paid', 'in_payment', 'reversed') or (
                move.state == 'posted'
                and move.currency_id.compare_amounts(move.amount_residual, move.laundry_pending_collection) <= 0
            )

    @api.depends('pos_order_ids.laundry_pending_collection')
    def _compute_laundry_pending_collection(self):
        for move in self:
            orders = move.sudo().pos_order_ids
            move.laundry_pending_collection = sum(orders.mapped('laundry_pending_collection'))
            payments = orders.laundry_collection_payment_ids.filtered(
                lambda p: not p.laundry_reconciled and p.pos_order_id.state not in ('draft', 'cancel'))
            move.laundry_pending_sessions = ", ".join(sorted(set(payments.mapped('session_id.name'))))

    @api.onchange('laundry_delivered')
    def _onchange_laundry_delivered_unpaid(self):
        """تنبيه بس (التسليم مسموح): الطلب لسا عليه مصاري، حصّلها قبل ما تسلّم الملابس."""
        if not self.laundry_delivered or self._origin.laundry_delivered:
            return
        due = self._laundry_amount_due()
        if self.currency_id.is_zero(due):
            return
        return {'warning': {
            'title': _("Unpaid order"),
            'message': _("This order still has %(due)s to pay. Collect the payment before handing over "
                         "the clothes (POS: Orders > Unpaid > Collect Payment).",
                         due=self.currency_id.format(due)),
        }}

    def _laundry_amount_due(self):
        """المتبقي على الفاتورة ناقص التحصيلات اللي انقبضت بالـ POS ولسا ما انطابقت."""
        self.ensure_one()
        orders = self._origin.sudo().pos_order_ids
        if orders:
            return sum(orders.mapped('laundry_credit_remaining'))
        return self._origin.amount_residual if self._origin.state == 'posted' else 0.0

