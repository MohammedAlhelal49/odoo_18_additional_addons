import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mail import single_email_re


class PosConfig(models.Model):
    _inherit = "pos.config"

    laundry_report_emails = fields.Char(
        string="Daily Report Emails",
        help="Comma-separated e-mail addresses that receive the daily summary of this point of sale "
             "(sent after midnight for the previous day).")
    # منتج أجرة التوصيل (خدمة)، بيتضاف لحاله لما الكاشير يختار طريقة توصيل بأجرة
    laundry_delivery_product_id = fields.Many2one(
        'product.product', string='Delivery Charge Product',
        domain=[('type', '=', 'service'), ('available_in_pos', '=', True)],
        default=lambda self: self.env.ref('london_laundry_implementation.product_laundry_delivery', raise_if_not_found=False))
    # خصم الزبون التلقائي: سطر سالب بهالمنتج (خدمة، ضريبة البيع الافتراضية)
    laundry_customer_discount_product_id = fields.Many2one(
        'product.product', string='Customer Discount Product',
        domain=[('type', '=', 'service'), ('available_in_pos', '=', True)],
        default=lambda self: self.env.ref('london_laundry_implementation.product_laundry_customer_discount', raise_if_not_found=False))
    # التوصيل مجاني للطلبات من هالمبلغ وطالع (شامل الضريبة)، وتحته الطلب مع التوصيل ما بيتعدّاه
    laundry_free_delivery_from = fields.Float(
        string='Free Delivery From', default=50.0,
        help='Orders of this amount or more (VAT included) get free delivery. Below it, the delivery charge '
             'is capped so that the order with delivery does not exceed this amount. 0 = no rule.')
    # إغلاق آخر اليوم: بالوقت المحدد (بتوقيت المغسلة) شاشة الـ POS بتفتح نافذة Close Register لحالها
    # (إجبارية، جرد أعمى للكاشير). إذا ضل الصندوق مفتوح بعد المهلة، السيرفر بيسكّره (المعدود = المتوقع)
    laundry_auto_close = fields.Boolean(string='Auto-close Sessions', default=True)
    laundry_auto_close_time = fields.Float(
        string='Auto-close Time', default=0.0,
        help='Local time (24h) at which the POS opens the closing screen by itself. 00:00 = midnight.')
    laundry_auto_close_grace = fields.Integer(
        string='Server Close After (min)', default=30,
        help='If the register is still open this many minutes after the closing time, the server closes it '
             'without a cash count (counted = expected).')
    # توقيت المغسلة للـ POS (توقيت الشركة، أو دبي إذا مش معبّى)
    laundry_tz = fields.Char(compute='_compute_laundry_tz')
    # رصيد الغسيل المسبق: بونص بنسبة ثابتة على الشحن من حد أدنى وطالع (100 → 125)
    laundry_prepaid_bonus_percent = fields.Float(
        string='Top-up Bonus %', default=25.0,
        help='Bonus added to the customer prepaid balance on each top-up, in % of the amount paid.')
    laundry_prepaid_bonus_min = fields.Float(
        string='Bonus From', default=100.0,
        help='Top-ups of this amount or more get the bonus. Smaller top-ups are allowed without a bonus. 0 = always.')
    laundry_report_last_date = fields.Date(
        string="Last Daily Report", readonly=True, copy=False,
        help="Last day whose summary was sent automatically.")

    def _compute_laundry_tz(self):
        daily = self.env['london.laundry.daily.report']
        for config in self:
            config.laundry_tz = daily._config_tz(config).zone

    def _laundry_report_email_list(self):
        self.ensure_one()
        return [e.strip() for e in re.split(r"[,;\s]+", self.laundry_report_emails or "") if e.strip()]

    @api.constrains("laundry_report_emails")
    def _check_laundry_report_emails(self):
        for config in self:
            invalid = [e for e in config._laundry_report_email_list() if not single_email_re.match(e)]
            if invalid:
                raise ValidationError(_("Invalid e-mail address(es) for the daily report: %s", ", ".join(invalid)))

    @api.model
    def _get_special_products(self):
        # منتج التوصيل بينحمّل دايماً بالـ POS، وما بيطلع بشبكة المنتجات (بينضاف من Delivery Method)
        configs = self.env['pos.config'].sudo().search([])
        return super()._get_special_products() | configs.laundry_delivery_product_id \
            | configs.laundry_customer_discount_product_id

    @api.model
    def _laundry_set_customer_discount_product(self):
        product = self.env.ref('london_laundry_implementation.product_laundry_customer_discount', raise_if_not_found=False)
        if product:
            self.sudo().search([('laundry_customer_discount_product_id', '=', False)]).laundry_customer_discount_product_id = product

    @api.model
    def _laundry_set_delivery_product(self):
        product = self.env.ref('london_laundry_implementation.product_laundry_delivery', raise_if_not_found=False)
        if product:
            self.sudo().search([('laundry_delivery_product_id', '=', False)]).laundry_delivery_product_id = product

