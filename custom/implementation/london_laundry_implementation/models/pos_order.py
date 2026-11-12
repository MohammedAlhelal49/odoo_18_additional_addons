import urllib.parse

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from .account_move import EXPECTED_HOURS, PACKING_TYPES

# رسالة واتساب "الطلب جاهز" (قابلة للتعديل من الإعدادات)
READY_MESSAGE_PARAM = 'london_laundry_implementation.ready_whatsapp_message'
DEFAULT_READY_MESSAGE = """عزيزنا {{partner_name}}،
طلبكم رقم {{order}} بقيمة {{amount}} درهم جاهز للاستلام.
إجمالي الرصيد المستحق: {{balance}} درهم.
رابط الفاتورة: {{invoice_link}}
شكراً لاستخدامكم خدماتنا - {{company}}

Dear {{partner_name}},
Your laundry job {{order}}, amount of {{amount}} AED, is finished and ready.
Your total outstanding balance is {{balance}} AED.
Invoice link: {{invoice_link}}
Thank you for using our service - {{company}}."""


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # بيعبيه الكاشير من قائمة Actions بواجهة الـ POS
    laundry_expected_delivery = fields.Date(string='Expected Delivery', copy=False)
    # الساعة بس (بدون دقائق)، بيختارها الكاشير مع التاريخ
    laundry_expected_hour = fields.Selection(EXPECTED_HOURS, string='Expected Hour', copy=False)
    # بيختارها الكاشير من زر جنب Internal Note
    laundry_delivery_method_id = fields.Many2one('london.delivery.method', string='Delivery Method', copy=False)
    # تعليق أو طي: بيختاره الكاشير من Actions (إجباري قبل الدفع)، بيطلع على الإيصال وبينتقل للفاتورة
    laundry_packing = fields.Selection(PACKING_TYPES, string='Hanger / Fold', copy=False)

    # حقول الفاتورة (الرف والتسليم) معروضة على الطلب، لشاشة الطلبات بالـ POS
    laundry_shelf = fields.Char(related='account_move.laundry_shelf', string='Shelf')
    laundry_delivered = fields.Boolean(related='account_move.laundry_delivered', string='Delivered')
    laundry_delivered_employee_id = fields.Many2one(
        related='account_move.laundry_delivered_employee_id', string='Delivered By')
    laundry_delivery_datetime = fields.Datetime(
        related='account_move.laundry_delivery_datetime', string='Delivery Date & Time')

    # حالة "Paid" تبع Odoo معناها إن الطلب تسكّر، مو إن المصاري وصلت:
    # هالحقول بتوضّح الطلبات اللي انعملت على الحساب (On Credit) وهل الزبون دفعها
    laundry_credit_amount = fields.Monetary(
        string='On Credit Amount', compute='_compute_laundry_collection', store=True,
        help='Part of the order paid with a customer-account (pay later) payment method.')
    laundry_collection_status = fields.Selection(
        selection=[
            ('paid', 'Paid'),
            ('credit_unpaid', 'On Credit - Unpaid'),
            ('credit_partial', 'On Credit - Partially Paid'),
            ('credit_paid', 'On Credit - Collected'),
            ('collection', 'Collection'),
            ('collection_cancelled', 'Collection - Cancelled'),
            ('collection_reversal', 'Collection Reversal'),
        ],
        string='Collection Status', compute='_compute_laundry_collection', store=True,
        help='Paid: settled at the counter (cash, card, transfer).\n'
             'On Credit: sold on the customer account; the status follows the invoice payment '
             'and the collections taken at the POS.\n'
             'Collection: a payment collected at the POS for earlier On Credit orders.\n'
             'Collection Reversal: cancels a collection of the same session (money given back).')

    # تحصيل الدين من الـ POS: دفعات طلبات التحصيل اللي بتسدّد هالطلب
    laundry_collection_payment_ids = fields.One2many(
        'pos.payment', 'laundry_collected_order_id', string='Collections', readonly=True)
    laundry_is_collection = fields.Boolean(
        string='Is Collection', compute='_compute_laundry_collection', store=True,
        help='Order created at the POS to collect earlier On Credit orders (no products, no invoice).')
    # انقبضت بجلسة لسا ما انطابقت مع الفاتورة (المطابقة بتصير عند إغلاق الجلسة)
    laundry_pending_collection = fields.Monetary(
        string='Pending Collection', compute='_compute_laundry_collection', store=True,
        help='Collected at the POS but not reconciled with the invoice yet (done when the session closes).')
    # إلغاء تحصيل: طلب معاكس بنفس الجلسة (المصاري بترجع للزبون والدين بيرجع على الطلبات)
    laundry_reversed_order_id = fields.Many2one(
        'pos.order', string='Cancelled Collection', index='btree_not_null', copy=False, readonly=True)
    laundry_reversal_order_ids = fields.One2many(
        'pos.order', 'laundry_reversed_order_id', string='Collection Cancellations', readonly=True)
    # رصيد الزبون (كل طلباته على الحساب) بعد هالتحصيل، لحظة التحصيل: بيطلع على الإيصال
    laundry_partner_balance = fields.Monetary(string='Customer Balance After', copy=False, readonly=True)
    laundry_credit_remaining = fields.Monetary(
        string='Remaining On Credit', compute='_compute_laundry_collection', store=True,
        help='Amount the customer still owes on this order, collections taken at the POS included.')

    @api.depends('state', 'payment_ids.amount', 'payment_ids.payment_method_id.journal_id',
                 'payment_ids.payment_method_id.is_cash_count', 'payment_ids.laundry_collected_order_id',
                 'account_move.state', 'account_move.payment_state', 'account_move.amount_residual',
                 'laundry_collection_payment_ids.amount', 'laundry_collection_payment_ids.laundry_reconciled',
                 'laundry_collection_payment_ids.pos_order_id.state',
                 'laundry_reversed_order_id', 'laundry_reversal_order_ids.state')
    def _compute_laundry_collection(self):
        for order in self:
            # أسطر التحصيل وإلغائه (مربوطة بطلب) مو بيع على الحساب
            credit = sum(order.payment_ids.filtered(
                lambda p: p.payment_method_id.type == 'pay_later' and not p.laundry_collected_order_id
            ).mapped('amount'))
            # سالب = تسديد دين أو إيداع من نقطة البيع، مو بيع على الحساب
            credit = max(credit, 0.0)
            order.laundry_credit_amount = credit
            order.laundry_is_collection = bool(order.payment_ids.laundry_collected_order_id)
            pending = -sum(order.laundry_collection_payment_ids.filtered(
                lambda p: not p.laundry_reconciled and p.pos_order_id.state not in ('draft', 'cancel')
            ).mapped('amount'))
            order.laundry_pending_collection = pending
            invoice = order.account_move
            if order.currency_id.is_zero(credit):
                remaining = 0.0
            elif invoice.state == 'posted':
                remaining = max(invoice.amount_residual - pending, 0.0)
            else:
                remaining = max(credit - pending, 0.0)
            order.laundry_credit_remaining = remaining

            if order.state in ('draft', 'cancel'):
                order.laundry_collection_status = False
            elif order.laundry_reversed_order_id:
                order.laundry_collection_status = 'collection_reversal'
            elif order.laundry_is_collection and order.laundry_reversal_order_ids.filtered(
                    lambda o: o.state not in ('draft', 'cancel')):
                order.laundry_collection_status = 'collection_cancelled'
            elif order.laundry_is_collection:
                order.laundry_collection_status = 'collection'
            elif order.currency_id.is_zero(credit):
                order.laundry_collection_status = 'paid'
            elif invoice.payment_state in ('paid', 'in_payment', 'reversed') or order.currency_id.is_zero(remaining):
                order.laundry_collection_status = 'credit_paid'
            elif invoice.payment_state == 'partial' or not order.currency_id.is_zero(pending):
                order.laundry_collection_status = 'credit_partial'
            else:
                order.laundry_collection_status = 'credit_unpaid'

    # ------------------------------------------------------------------ WhatsApp "order ready"
    def _laundry_ready_whatsapp_url(self):
        """رابط wa.me برسالة "الطلب جاهز" (عربي + إنكليزي)، أو رسالة خطأ."""
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return None, _("This order has no customer.")
        report = self.env['london.laundry.report']
        phone = report._whatsapp_phone(partner)
        if not phone:
            return None, _("The customer's mobile number is missing or not valid for WhatsApp.")
        invoice = self.sudo().account_move
        balance = self.get_laundry_credit_orders(partner.id)['total_due']
        values = {
            'partner_name': partner.name or '',
            'order': self.name or '',
            'amount': '%.2f' % self.amount_total,
            'balance': '%.2f' % balance,
            # الكاشير بيقدر يشوف هالطلب، فرابط فاتورته (برمز وصول) ما فيه مشكلة
            'invoice_link': (invoice.get_base_url() + invoice._get_share_url()) if invoice else '',
            'company': self.company_id.name or '',
        }
        text = self.env['ir.config_parameter'].sudo().get_param(READY_MESSAGE_PARAM) or DEFAULT_READY_MESSAGE
        for key, value in values.items():
            text = text.replace('{{%s}}' % key, str(value))
        return 'https://wa.me/%s?text=%s' % (phone, urllib.parse.quote(text, safe='')), None

    @api.model
    def get_laundry_ready_whatsapp(self, order_id):
        """من شاشة الطلبات بالـ POS: رابط واتساب "الطلب جاهز"."""
        order = self.browse(order_id).exists()
        if not order:
            return {'error': _("Order not found.")}
        url, error = order._laundry_ready_whatsapp_url()
        if error:
            return {'error': error}
        order.sudo().message_post(body=_("WhatsApp opened with the 'order ready' message."))
        return {'url': url}

    def action_laundry_whatsapp_ready(self):
        """زر الباك إند (طلب الـ POS أو فاتورته)."""
        self.ensure_one()
        result = self.get_laundry_ready_whatsapp(self.id)
        if result.get('error'):
            raise UserError(result['error'])
        return {'type': 'ir.actions.act_url', 'url': result['url'], 'target': 'new'}

    def _laundry_receipt_details(self):
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
    def get_laundry_credit_orders(self, partner_id, order_ids=None):
        """طلبات الزبون اللي عليها مصاري وإلها فاتورة، لنافذة "Collect Payment" بالـ POS.

        order_ids: بس هالطلبات (فحص المتبقي قبل Validate).
        الطلبات القديمة اللي ما إلها فاتورة ما بتنحصّل من هون (مأجّلة): منرجّع عددها بس.
        """
        partner = self.env['res.partner'].browse(partner_id).commercial_partner_id
        domain = [
            ('partner_id', 'child_of', partner.id),
            ('laundry_collection_status', 'in', ('credit_unpaid', 'credit_partial')),
            ('company_id', 'in', self.env.companies.ids),
        ]
        all_orders = self.search(domain, order='date_order, id')
        # رصيد الزبون: كل اللي عليه (حتى الطلبات القديمة بلا فاتورة)، للإيصال
        total_due = sum(all_orders.mapped('laundry_credit_remaining'))
        orders = all_orders if order_ids is None else all_orders.filtered(lambda o: o.id in order_ids)
        result, without_invoice = [], 0
        for order in orders:
            invoice = order.sudo().account_move
            if invoice.state != 'posted':
                without_invoice += 1
                continue
            if order.currency_id.is_zero(order.laundry_credit_remaining):
                continue
            result.append({
                'id': order.id,
                'name': order.name,
                'pos_reference': order.pos_reference or '',
                'date_order': fields.Datetime.to_string(order.date_order),
                'invoice': invoice.name,
                'amount_total': order.amount_total,
                'credit_amount': order.laundry_credit_amount,
                'remaining': order.laundry_credit_remaining,
            })
        return {'orders': result, 'without_invoice': without_invoice, 'total_due': total_due}

    @api.model
    def set_laundry_shelf(self, order_id, shelf):
        """من شاشة الطلبات بالـ POS: رقم الرف (1 لـ 9) بينحفظ على الفاتورة."""
        invoice = self.browse(order_id).exists().account_move
        if not invoice:
            return {'error': _("This order has no invoice, the shelf cannot be saved.")}
        # الكاشير ما عنده صلاحية تعديل الفواتير: منكتب هالحقل بس (والقيد 1 لـ 9 بيتحقق)
        invoice.sudo().laundry_shelf = shelf or False
        return {'shelf': invoice.laundry_shelf or ''}

    @api.model
    def set_laundry_delivered(self, order_id, employee_id):
        """من شاشة الطلبات بالـ POS: الطلب تسلّم، والكاشير اللي ضغط الزر هو اللي سلّمه."""
        invoice = self.browse(order_id).exists().account_move
        if not invoice:
            return {'error': _("This order has no invoice, the delivery cannot be saved.")}
        employee = self.env['hr.employee'].sudo().browse(employee_id or 0).exists()
        invoice.sudo().write({
            'laundry_delivered': True,
            'laundry_delivered_employee_id': employee.id or self.env.user.employee_id.id or False,
        })
        return {'delivered_by': invoice.sudo().laundry_delivered_employee_id.name or ''}

    @api.model
    def _laundry_is_pos_manager(self, session, employee_id):
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
    def get_laundry_collection_cancel(self, order_id, session_id, employee_id=None):
        """هل فينا نلغي هالتحصيل؟ بنفس الجلسة المفتوحة بس، ومرة وحدة، وقبل المطابقة.

        بيرجّع الدفعات اللي لازم تنعكس (On Credit المربوطة بالطلبات + الدفع الفعلي صافي لكل طريقة).
        """
        order = self.browse(order_id).exists()
        if not order or not order.laundry_is_collection or order.laundry_reversed_order_id:
            return {'error': _("This order is not a collection.")}
        if order.laundry_reversal_order_ids.filtered(lambda o: o.state not in ('draft', 'cancel')):
            return {'error': _("This collection is already cancelled.")}
        if not self._laundry_is_pos_manager(order.session_id, employee_id):
            return {'error': _("Only a manager can cancel a collection.")}
        if order.session_id.id != session_id or order.session_id.state != 'opened':
            return {'error': _("A collection can only be cancelled in the session where it was taken, "
                               "before the session is closed. Ask the accountant.")}
        credit_lines = order.payment_ids.filtered('laundry_collected_order_id')
        if any(credit_lines.mapped('laundry_reconciled')):
            return {'error': _("This collection is already matched with the invoices. Ask the accountant.")}
        methods = {}
        for payment in order.payment_ids - credit_lines:
            methods[payment.payment_method_id.id] = methods.get(payment.payment_method_id.id, 0.0) + payment.amount
        return {
            'credit_lines': [{
                'id': p.id,
                'method_id': p.payment_method_id.id,
                'amount': p.amount,
                'target_id': p.laundry_collected_order_id.id,
                'due': p.laundry_collected_due,
            } for p in credit_lines],
            'payments': [{'method_id': m, 'amount': a} for m, a in methods.items()
                         if not order.currency_id.is_zero(a)],
        }

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        vals['laundry_expected_delivery'] = self.laundry_expected_delivery
        vals['laundry_expected_hour'] = self.laundry_expected_hour
        vals['laundry_delivery_method_id'] = self.laundry_delivery_method_id.id
        vals['laundry_packing'] = self.laundry_packing
        return vals
