import re

import phonenumbers

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

# أي رقم من أي بلد، بشرط يكون موبايل أو أرضي صحيح (مكتبة phonenumbers نفسها اللي بيستعملها Odoo).
# الرقم بلا رمز دولة بينحسب إماراتي؛ الإماراتي بينحفظ بالصيغة المحلية (05XXXXXXXX / 04XXXXXXX)
# متل الأرقام الموجودة، وغير الإماراتي بالصيغة الدولية (+963XXXXXXXXX).
DEFAULT_REGION = 'AE'
# جهات اتصال بتنعمل تلقائياً (مستخدمين، شركات، موظفين) ما إلها موبايل: ما منفحصها
SKIP_CTX = 'laundry_skip_mobile_check'
_VALID_TYPES = {
    phonenumbers.PhoneNumberType.MOBILE,
    phonenumbers.PhoneNumberType.FIXED_LINE,
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE,
}


def parse_laundry_number(value):
    """الرقم بصيغته المحفوظة إذا كان موبايل أو أرضي صحيح، وإلا None."""
    if not value:
        return None
    try:
        number = phonenumbers.parse(value, DEFAULT_REGION)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(number) or phonenumbers.number_type(number) not in _VALID_TYPES:
        return None
    if phonenumbers.region_code_for_number(number) == DEFAULT_REGION:
        return '0' + phonenumbers.national_significant_number(number)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def laundry_number_variants(value):
    """نفس الرقم بالصيغ اللي ممكن يكون محفوظ فيها (محلي، +971، 00971، 971)، للبحث عن التكرار."""
    number = normalize_uae_mobile(value)
    variants = {number, value}
    if number.startswith('0') and not number.startswith('00'):
        rest = number[1:]
        variants |= {'+971' + rest, '00971' + rest, '971' + rest}
    elif number.startswith('+'):
        variants |= {'00' + number[1:], number[1:]}
    return {v for v in variants if v}


def normalize_uae_mobile(value):
    """الصيغة المحفوظة للرقم (إذا صحيح)؛ إذا مو صحيح بيرجع متل ما انكتب بلا فراغات، والقيد بيرفضه."""
    if not value:
        return value
    return parse_laundry_number(value) or re.sub(r'[\s\-()./]', '', value)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # رصيد الغسيل المسبق (شحنات مع البونص ناقص اللي اندفع منه)، من دفعات الـ POS
    laundry_prepaid_balance = fields.Monetary(
        string='Prepaid Balance', compute='_compute_laundry_prepaid_balance', currency_field='currency_id',
        help='Laundry prepaid balance: top-ups (bonus included) minus what was paid from it at the POS.')

    # خصم الزبون التلقائي بالـ POS: نسبة من الأصناف أو مبلغ ثابت على كل طلب (شامل الضريبة)
    laundry_discount_type = fields.Selection(
        [('percent', 'Percentage'), ('fixed', 'Fixed Amount')], string='Customer Discount',
        help='Applied automatically on the new POS orders of this customer (clothes only, not the delivery).\n'
             'Not applied when the customer has a special price list or a prepaid balance.')
    laundry_discount_value = fields.Float(
        string='Discount Value', help='Percentage (e.g. 10 = 10%) or fixed amount per order, VAT included.')

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + ['laundry_discount_type', 'laundry_discount_value']

    @api.constrains('laundry_discount_type', 'laundry_discount_value')
    def _check_laundry_discount(self):
        for partner in self:
            if partner.laundry_discount_type and partner.laundry_discount_value < 0:
                raise ValidationError(_("The customer discount cannot be negative."))
            if partner.laundry_discount_type == 'percent' and partner.laundry_discount_value > 100:
                raise ValidationError(_("The customer discount cannot be more than 100%."))

    def _laundry_check_discount_rights(self, vals):
        """خصم الزبون: بيحطّه المدير أو المحاسب بس."""
        if {'laundry_discount_type', 'laundry_discount_value'} & set(vals) and not self.env.su and not (
                self.env.user.has_group('point_of_sale.group_pos_manager')
                or self.env.user.has_group('account.group_account_manager')):
            raise AccessError(_("Only a manager or an accountant can set the customer discount."))

    @api.onchange('laundry_discount_type', 'laundry_discount_value', 'property_product_pricelist')
    def _onchange_laundry_discount(self):
        default = self.env['pos.config'].search([], limit=1).pricelist_id
        if self.laundry_discount_type and self.property_product_pricelist and default \
                and self.property_product_pricelist != default:
            return {'warning': {
                'title': _("Customer with special prices"),
                'message': _("This customer has the price list %s: the customer discount is not applied "
                             "(discount for the normal prices only).", self.property_product_pricelist.display_name),
            }}

    def _compute_laundry_prepaid_balance(self):
        balances = self.env['pos.order'].sudo()._laundry_prepaid_balances(self.commercial_partner_id.ids)
        for partner in self:
            partner.laundry_prepaid_balance = balances.get(partner.commercial_partner_id.id, 0.0)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        # بدل تنسيق phone_validation الدولي (+971 ...) نخلي الرقم بالصيغة المحلية
        if self.mobile:
            self.mobile = normalize_uae_mobile(self.mobile)

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = normalize_uae_mobile(self.phone)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._laundry_check_discount_rights(vals)
            for field in ('mobile', 'phone'):
                if vals.get(field):
                    vals[field] = normalize_uae_mobile(vals[field])
        partners = super().create(vals_list)
        # constrains بيشتغل بس على الحقول المرسلة، فلازم نفحص الموبايل الفاضي هون
        partners._check_laundry_uae_mobile()
        return partners

    def write(self, vals):
        self._laundry_check_discount_rights(vals)
        for field in ('mobile', 'phone'):
            if vals.get(field):
                vals[field] = normalize_uae_mobile(vals[field])
        return super().write(vals)

    @api.constrains('mobile')
    def _check_laundry_uae_mobile(self):
        if self.env.context.get(SKIP_CTX) or self.env.context.get('install_mode'):
            return
        for partner in self:
            if not partner.mobile:
                raise ValidationError(_(
                    "The contact \"%s\" must have a mobile number.\n"
                    "لا يمكن حفظ جهة اتصال بدون رقم موبايل.", partner.display_name))
            if not parse_laundry_number(partner.mobile):
                raise ValidationError(_(
                    "The number \"%s\" is not a valid mobile or landline number. "
                    "A UAE number can be typed as it is (e.g. 0501234567 or 042345678); "
                    "a number from another country needs its country code (e.g. +963944123456).\n"
                    "الرقم لازم يكون موبايل أو أرضي صحيح. الرقم الإماراتي بينكتب عادي (0501234567 أو 042345678)، "
                    "والرقم من بلد تاني لازم مع رمز الدولة (مثلاً +963944123456).",
                    partner.mobile))

    @api.constrains('mobile', 'phone')
    def _check_laundry_unique_number(self):
        """ما في رقمين متشابهين: الموبايل أو الهاتف ما بيتكرر عند جهة اتصال تانية."""
        if self.env.context.get(SKIP_CTX) or self.env.context.get('install_mode'):
            return
        for partner in self:
            for number in {partner.mobile, partner.phone} - {False, ''}:
                variants = list(laundry_number_variants(number))
                other = self.sudo().search([
                    ('id', '!=', partner.id),
                    '|', ('mobile', 'in', variants), ('phone', 'in', variants),
                ], limit=1)
                if other:
                    raise ValidationError(_(
                        "The number %(number)s is already used by the contact \"%(other)s\".\n"
                        "الرقم %(number)s مستعمل عند جهة الاتصال \"%(other)s\".",
                        number=number, other=other.display_name))

    @api.constrains('phone')
    def _check_laundry_uae_phone(self):
        # الهاتف التاني اختياري، بس إذا انعبّى لازم يكون موبايل أو أرضي صحيح كمان
        if self.env.context.get(SKIP_CTX) or self.env.context.get('install_mode'):
            return
        for partner in self:
            if partner.phone and not parse_laundry_number(partner.phone):
                raise ValidationError(_(
                    "The phone \"%s\" is not a valid mobile or landline number "
                    "(a number from another country needs its country code, e.g. +963944123456).\n"
                    "رقم الهاتف لازم يكون موبايل أو أرضي صحيح (الرقم من بلد تاني مع رمز الدولة).",
                    partner.phone))


class ResUsers(models.Model):
    _inherit = 'res.users'

    # جهة الاتصال اللي بتنعمل تلقائياً للمستخدم ما إلها موبايل
    @api.model_create_multi
    def create(self, vals_list):
        return super(ResUsers, self.with_context(**{SKIP_CTX: True})).create(vals_list)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        return super(ResCompany, self.with_context(**{SKIP_CTX: True})).create(vals_list)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # جهة اتصال العمل اللي بتنعمل تلقائياً للموظف
    def _create_work_contacts(self):
        return super(HrEmployee, self.with_context(**{SKIP_CTX: True}))._create_work_contacts()
