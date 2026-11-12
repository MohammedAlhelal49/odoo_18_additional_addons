import re

import phonenumbers

from odoo import _, api, models
from odoo.exceptions import ValidationError

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
            for field in ('mobile', 'phone'):
                if vals.get(field):
                    vals[field] = normalize_uae_mobile(vals[field])
        partners = super().create(vals_list)
        # constrains بيشتغل بس على الحقول المرسلة، فلازم نفحص الموبايل الفاضي هون
        partners._check_laundry_uae_mobile()
        return partners

    def write(self, vals):
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
