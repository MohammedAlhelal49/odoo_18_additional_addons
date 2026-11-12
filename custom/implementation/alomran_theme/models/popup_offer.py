# -*- coding: utf-8 -*-
import re
from urllib.parse import quote

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

# رقم الواتساب الافتراضي للعروض — نفس رقم صفحة تواصل معنا
# (ممكن يتغير من System Parameter: alomran.offers_whatsapp)
OFFER_WHATSAPP_NUMBER = '971505829697'

# صفحات الكورسات اللي فيك تخصص إلها عرض: key -> (المسار، اسم الكورس عربي، إنجليزي)
OFFER_TARGET_PAGES = {
    'english': ('/english-ielts', 'كورسات اللغة الإنجليزية', 'English courses'),
    'tutoring': ('/private-tutoring', 'الدروس الخصوصية والدعم الأكاديمي', 'private tutoring & academic support'),
    'women': ('/women-courses', 'دورات السيدات', "women's courses"),
    'saudi': ('/saudi-online', 'التعلم أونلاين - السعودية', 'online learning (Saudi Arabia)'),
    'languages': ('/languages', 'كورسات اللغات', 'language courses'),
    'teachers': ('/teachers', 'برامج تأهيل المعلمين', 'teacher training programs'),
    'it_programs': ('/it-programs', 'برامج تقنية المعلومات', 'IT programs'),
    'courses': ('/courses', 'الدورات التدريبية', 'training courses'),
}

_LANG_PREFIX_RE = re.compile(r'^/[a-z]{2}(?:_[A-Za-z0-9]+)?(?=/|$)')
_HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{3,8}$')


def normalize_offer_path(path):
    """/ar/english-ielts/ -> /english-ielts (بلا بادئة لغة ولا / بالآخر)."""
    path = (path or '/').split('?')[0].split('#')[0].strip() or '/'
    if not path.startswith('/'):
        path = '/' + path
    path = _LANG_PREFIX_RE.sub('', path) or '/'
    if len(path) > 1:
        path = path.rstrip('/') or '/'
    return path.lower()


def _fmt_number(value):
    return f'{value:g}'


class PopupOffer(models.Model):
    _name = 'popup.offer'
    _description = 'Pop-up Offers'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'
    _rec_name = 'name'

    # ============================================================
    # BASIC INFORMATION
    # ============================================================

    name = fields.Char(
        string='Offer Name',
        required=True,
        help='Internal offer name (e.g., Ramadan Offer 2026)'
    )

    # ✅ إضافة name_en للدعم الثنائي اللغة
    name_en = fields.Char(
        string='Offer Name (English)',
        help='Internal offer name in English'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Offer priority (lower number = higher priority)'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Deactivating stops the offer immediately'
    )

    # ============================================================
    # OFFER TYPE & SETTINGS
    # ============================================================

    offer_type = fields.Selection([
        ('buy_x_get_y', 'Buy X Get Y Free'),
        ('discount_percentage', 'Percentage Discount'),
        ('discount_fixed', 'Fixed Amount Discount'),
        ('free_consultation', 'Free Consultation'),
        ('custom', 'Custom Offer'),
    ], string='Offer Type', required=True, default='buy_x_get_y',
        help='Offer type determines how it is displayed in the Pop-up')

    # Buy X Get Y Settings
    buy_quantity = fields.Integer(
        string='Courses to Buy',
        default=2,
        help='Number of courses that must be purchased'
    )

    get_quantity = fields.Integer(
        string='Free Courses',
        default=1,
        help='Number of free courses'
    )

    # Discount Settings
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Discount Type', default='percentage')

    discount_value = fields.Float(
        string='Discount Value',
        help='Percentage or fixed amount'
    )

    # ============================================================
    # DISPLAY CONTENT (Arabic & English)
    # ============================================================

    title_ar = fields.Char(
        string='Title (Arabic)',
        required=True,
        help='Main offer title in Arabic'
    )

    title_en = fields.Char(
        string='Title (English)',
        help='Main offer title in English'
    )

    subtitle_ar = fields.Char(
        string='Subtitle (Arabic)',
        help='Additional text below the title'
    )

    subtitle_en = fields.Char(
        string='Subtitle (English)'
    )

    description_ar = fields.Text(
        string='Description (Arabic)',
        help='Detailed offer description'
    )

    description_en = fields.Text(
        string='Description (English)'
    )

    # ============================================================
    # BADGE CUSTOMIZATION
    # ============================================================

    badge_text_ar = fields.Char(
        string='Badge Text (Arabic)',
        default='عرض لفترة محدودة!',
        help='Text displayed on the offer badge in Arabic'
    )

    badge_text_en = fields.Char(
        string='Badge Text (English)',
        default='Limited Time Offer!',
        help='Text displayed on the offer badge in English'
    )

    badge_text = fields.Char(
        string='Badge Text',
        compute='_compute_badge_text',
        store=False
    )

    badge_color = fields.Char(
        string='Badge Color',
        default='#ff6b6b',
        help='Hex color code (e.g., #ff6b6b)'
    )

    @api.depends('badge_text_ar')
    def _compute_badge_text(self):
        for record in self:
            record.badge_text = record.badge_text_ar

    # ============================================================
    # DATES & SCHEDULING
    # ============================================================

    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help='Offer start date and time'
    )

    end_date = fields.Datetime(
        string='End Date',
        tracking=True,
        help='Offer end date and time (leave empty for unlimited offers)'
    )

    # ============================================================
    # COUNTDOWN TIMER
    # ============================================================

    show_countdown = fields.Boolean(
        string='Show Countdown',
        default=True,
        help='Display countdown timer in Pop-up'
    )

    countdown_days = fields.Integer(
        string='Countdown Days',
        compute='_compute_countdown_days',
        store=True,
        help='Days remaining (calculated automatically)'
    )

    # ============================================================
    # TERMS & CONDITIONS
    # ============================================================

    terms_ar = fields.Text(
        string='Terms & Conditions (Arabic)',
        help='Offer terms and conditions'
    )

    terms_en = fields.Text(
        string='Terms & Conditions (English)'
    )

    # ============================================================
    # POP-UP BEHAVIOR SETTINGS
    # ============================================================

    delay_seconds = fields.Integer(
        string='Delay (Seconds)',
        default=3,
        help='Seconds to wait before showing Pop-up'
    )

    cookie_duration = fields.Integer(
        string='Cookie Duration (Days)',
        default=7,
        help='Days before showing Pop-up again to same visitor'
    )

    exit_intent = fields.Boolean(
        string='Show on Exit Intent',
        default=False,
        help='Show Pop-up when user tries to leave the page'
    )

    display_frequency = fields.Selection([
        ('every_page', 'Every page visit (shows again even after closing)'),
        ('session', 'Once per browsing session'),
        ('days', 'Once every N days (Cookie Duration)'),
    ], string='Display Frequency', required=True, default='every_page',
        help='Every page visit: the offer appears on every page load, even if the visitor closed it before')

    # ============================================================
    # TARGETING (عام / صفحة كورس معينة)
    # ============================================================

    target_type = fields.Selection([
        ('all', 'All Pages (General Offer)'),
        ('page', 'Specific Course Page'),
    ], string='Show On', required=True, default='all', tracking=True,
        help='A page-specific offer takes priority over the general offer on its page')

    target_page = fields.Selection([
        ('english', 'English & Standardized Tests (/english-ielts)'),
        ('tutoring', 'Private Tutoring & Academic Support (/private-tutoring)'),
        ('women', "Women's Professional & Creative Courses (/women-courses)"),
        ('saudi', 'Saudi Online Learning (/saudi-online)'),
        ('languages', 'Languages (/languages)'),
        ('teachers', 'Teacher Training (/teachers)'),
        ('it_programs', 'IT Programs (/it-programs)'),
        ('courses', 'All Courses (/courses)'),
        ('custom', 'Custom Page Path'),
    ], string='Course Page', tracking=True)

    target_path = fields.Char(
        string='Page Path',
        help='e.g. /branch/alain-yahar-mall — without the language prefix (/ar, /en)'
    )

    course_label_ar = fields.Char(
        string='Course Name (Arabic)',
        help='Shown in the offer text, e.g. "خصم 10% على كورسات اللغة الإنجليزية"'
    )
    course_label_en = fields.Char(
        string='Course Name (English)',
        help='Shown in the offer text, e.g. "10% OFF English courses"'
    )

    # ============================================================
    # WHATSAPP CONTACT
    # ============================================================

    whatsapp_btn_ar = fields.Char(string='WhatsApp Button (Arabic)', default='احصل على العرض عبر واتساب')
    whatsapp_btn_en = fields.Char(string='WhatsApp Button (English)', default='Get the Offer on WhatsApp')
    whatsapp_message_ar = fields.Char(
        string='WhatsApp Message (Arabic)',
        help='Pre-filled message. Leave empty to generate it from the offer text.'
    )
    whatsapp_message_en = fields.Char(
        string='WhatsApp Message (English)',
        help='Pre-filled message. Leave empty to generate it from the offer text.'
    )

    click_count = fields.Integer(
        string='WhatsApp Clicks',
        readonly=True,
        default=0,
        copy=False,
        help='Visitors who clicked the WhatsApp button of this offer'
    )

    # ============================================================
    # STATIC TEXT CUSTOMIZATION (Arabic & English)
    # ============================================================

    form_title_ar = fields.Char(
        string='Form Title (Arabic)',
        default='سجّل الآن واحجز مقعدك!',
    )
    form_title_en = fields.Char(
        string='Form Title (English)',
        default='Register Now and Reserve Your Spot!',
    )

    form_subtitle_ar = fields.Char(
        string='Form Subtitle (Arabic)',
        default='أدخل بياناتك وسيتواصل معك فريقنا خلال 24 ساعة لتأكيد العرض',
    )
    form_subtitle_en = fields.Char(
        string='Form Subtitle (English)',
        default='Enter your details and our team will contact you within 24 hours to confirm the offer',
    )

    name_label_ar = fields.Char(default='الاسم الكامل')
    name_label_en = fields.Char(default='Full Name')
    name_placeholder_ar = fields.Char(default='مثال: أحمد محمد')
    name_placeholder_en = fields.Char(default='e.g., John Smith')

    phone_label_ar = fields.Char(default='رقم الهاتف')
    phone_label_en = fields.Char(default='Phone Number')
    phone_placeholder_ar = fields.Char(default='05XXXXXXXX')
    phone_placeholder_en = fields.Char(default='05XXXXXXXX')

    submit_btn_ar = fields.Char(default='احصل على العرض الآن')
    submit_btn_en = fields.Char(default='Get the Offer Now')
    close_btn_ar = fields.Char(default='ربما لاحقاً')
    close_btn_en = fields.Char(default='Maybe Later')

    success_title_ar = fields.Char(default='مبروك! تم حجز العرض بنجاح 🎉')
    success_title_en = fields.Char(default='Congratulations! Offer Reserved Successfully 🎉')
    success_message_ar = fields.Text(
        default='شكراً لك {name}! سيتواصل معك فريقنا خلال 24 ساعة لتأكيد حجزك والاستفادة من العرض.'
    )
    success_message_en = fields.Text(
        default='Thank you {name}! Our team will contact you within 24 hours to confirm your reservation.'
    )

    social_proof_ar = fields.Char(default='انضم لأكثر من 10,000+ متدرب استفادوا من عروضنا!')
    social_proof_en = fields.Char(default='Join 10,000+ trainees who benefited from our offers!')

    trust_text_ar = fields.Char(default='معلوماتك آمنة ومحمية | لن نشارك بياناتك مع أي طرف ثالث')
    trust_text_en = fields.Char(
        default='Your Information is Safe and Protected | We will not share your data with any third party')

    countdown_title_ar = fields.Char(default='ينتهي العرض خلال:')
    countdown_title_en = fields.Char(default='Offer Ends In:')
    days_label_ar = fields.Char(default='يوم')
    days_label_en = fields.Char(default='Days')
    hours_label_ar = fields.Char(default='ساعة')
    hours_label_en = fields.Char(default='Hours')
    mins_label_ar = fields.Char(default='دقيقة')
    mins_label_en = fields.Char(default='Minutes')

    # ============================================================
    # ANALYTICS & TRACKING
    # ============================================================

    view_count = fields.Integer(
        string='View Count',
        readonly=True,
        default=0,
        copy=False,
        help='Number of times Pop-up was displayed'
    )

    lead_count = fields.Integer(
        string='Lead Count',
        compute='_compute_lead_count',
        help='Number of Leads from this offer'
    )

    conversion_rate = fields.Float(
        string='WhatsApp Click Rate',
        compute='_compute_conversion_rate',
        digits=(5, 4),
        help='WhatsApp clicks / views'
    )

    # ============================================================
    # STATE & STATUS
    # ============================================================

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ], string='Status', compute='_compute_state', store=True, tracking=True,
        help='Offer status (calculated automatically)')

    # ============================================================
    # RELATIONS
    # ============================================================

    # ✅ تم تغيير الـ One2many لتكون computed بدلاً من inverse
    # هذا يحل مشكلة ترتيب التحميل
    lead_ids = fields.One2many(
        'crm.lead',
        'x_popup_offer_id',
        string='Registrations',
        help='All Leads from this offer'
    )

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    @api.depends('start_date', 'end_date', 'active')
    def _compute_state(self):
        """Calculate offer status automatically based on date and activation"""
        now = fields.Datetime.now()

        for offer in self:
            if not offer.active:
                offer.state = 'paused'
            elif not offer.start_date:
                offer.state = 'draft'
            elif offer.start_date > now:
                offer.state = 'scheduled'
            elif offer.end_date and offer.end_date < now:
                offer.state = 'expired'
            else:
                offer.state = 'active'

    @api.depends('end_date')
    def _compute_countdown_days(self):
        """Calculate remaining days for the offer"""
        now = fields.Datetime.now()

        for offer in self:
            if offer.end_date:
                delta = offer.end_date - now
                offer.countdown_days = max(0, delta.days)
            else:
                offer.countdown_days = 0

    def _compute_lead_count(self):
        """Calculate number of registrations from this offer"""
        for offer in self:
            offer.lead_count = self.env['crm.lead'].sudo().search_count([
                ('x_popup_offer_id', '=', offer.id)
            ])

    @api.depends('click_count', 'view_count')
    def _compute_conversion_rate(self):
        """نسبة نقرات الواتساب من المشاهدات (widget percentage بيضرب بـ 100)"""
        for offer in self:
            offer.conversion_rate = (offer.click_count / offer.view_count) if offer.view_count else 0.0

    @api.onchange('target_page')
    def _onchange_target_page(self):
        """اسم الكورس الافتراضي حسب الصفحة (إذا فاضي أو لسا الافتراضي القديم)."""
        defaults_ar = {v[1] for v in OFFER_TARGET_PAGES.values()}
        defaults_en = {v[2] for v in OFFER_TARGET_PAGES.values()}
        page = OFFER_TARGET_PAGES.get(self.target_page)
        if not page:
            return
        if not self.course_label_ar or self.course_label_ar in defaults_ar:
            self.course_label_ar = page[1]
        if not self.course_label_en or self.course_label_en in defaults_en:
            self.course_label_en = page[2]

    # ============================================================
    # BUSINESS METHODS
    # ============================================================

    # ------------------------------------------------------------
    # اختيار العرض للصفحة
    # ------------------------------------------------------------

    def _target_normalized_path(self):
        self.ensure_one()
        if self.target_type != 'page':
            return False
        if self.target_page == 'custom':
            return normalize_offer_path(self.target_path) if self.target_path else False
        page = OFFER_TARGET_PAGES.get(self.target_page)
        return page[0] if page else False

    @api.model
    def _running_offers_domain(self):
        now = fields.Datetime.now()
        return [
            ('active', '=', True),
            ('start_date', '<=', now),
            '|', ('end_date', '=', False), ('end_date', '>=', now),
        ]

    @api.model
    def get_offer_for_path(self, path):
        """العرض الخاص بالصفحة أولاً، وإذا ما في، العرض العام. (ما بيعدّ مشاهدة)"""
        norm = normalize_offer_path(path)
        offers = self.search(self._running_offers_domain(), order='sequence, id desc')
        for offer in offers:
            if offer.target_type == 'page' and offer._target_normalized_path() == norm:
                return offer
        return offers.filtered(lambda o: o.target_type == 'all')[:1]

    @api.model
    def get_active_offer(self):
        """Legacy: أول عرض عام شغال (بدون عدّ مشاهدة)."""
        return self.search(self._running_offers_domain() + [('target_type', '=', 'all')],
                           order='sequence, id desc', limit=1)

    def _increment_counter(self, field_name):
        """زيادة عداد بـ SQL مباشرة (بدون write كامل على السجل مع كل زيارة)."""
        if field_name not in ('view_count', 'click_count') or not self.ids:
            return
        self.env.cr.execute(
            f'UPDATE popup_offer SET {field_name} = COALESCE({field_name}, 0) + 1 WHERE id IN %s',
            (tuple(self.ids),))
        self.invalidate_recordset([field_name])

    def _increment_view(self):
        self._increment_counter('view_count')

    # ------------------------------------------------------------
    # النصوص
    # ------------------------------------------------------------

    def _offer_highlight(self, is_english):
        self.ensure_one()
        lang = 'en' if is_english else 'ar'
        course = (getattr(self, f'course_label_{lang}') or '').strip()
        value = _fmt_number(self.discount_value or 0)
        if self.offer_type == 'buy_x_get_y':
            text = (f'Buy {self.buy_quantity} Get {self.get_quantity} FREE' if is_english
                    else f'اشترِ {self.buy_quantity} واحصل على {self.get_quantity} مجاناً')
            if course:
                text += f' — {course}'
        elif self.offer_type == 'discount_percentage':
            if is_english:
                text = f'{value}% OFF {course}' if course else f'{value}% OFF'
            else:
                text = f'خصم {value}% على {course}' if course else f'خصم {value}%'
        elif self.offer_type == 'discount_fixed':
            if is_english:
                text = f'AED {value} OFF {course}' if course else f'AED {value} OFF'
            else:
                text = f'خصم {value} درهم على {course}' if course else f'خصم {value} درهم'
        elif self.offer_type == 'free_consultation':
            text = 'Free Consultation' if is_english else 'استشارة مجانية'
            if course:
                text += f' — {course}'
        else:
            text = getattr(self, f'title_{lang}') or self.title_ar
        return text

    def _whatsapp_url(self, is_english, highlight):
        self.ensure_one()
        lang = 'en' if is_english else 'ar'
        number = (self.env['ir.config_parameter'].sudo().get_param('alomran.offers_whatsapp') or '').strip()
        if not re.fullmatch(r'\d{8,15}', number):
            number = OFFER_WHATSAPP_NUMBER
        message = (getattr(self, f'whatsapp_message_{lang}') or '').strip()
        if not message:
            message = (f'Hello, I would like to get the offer: {highlight}' if is_english
                       else f'مرحباً، أريد الاستفادة من العرض: {highlight}')
        return f'https://wa.me/{number}?text={quote(message)}'

    def get_offer_data_localized(self, is_english=False):
        """بيانات العرض للـ popup باللغة الحالية."""
        self.ensure_one()
        lang = 'en' if is_english else 'ar'
        highlight = self._offer_highlight(is_english)
        end_ms = False
        if self.end_date:
            # Odoo بيخزن UTC بدون timezone — منبعت epoch ms منشان المتصفح ما يقراه كوقت محلي
            from datetime import timezone
            end_ms = int(self.end_date.replace(tzinfo=timezone.utc).timestamp() * 1000)
        badge_color = self.badge_color if _HEX_COLOR_RE.match(self.badge_color or '') else '#ff6b6b'
        return {
            'id': self.id,
            'offer_type': self.offer_type,
            'highlight': highlight,
            'title': getattr(self, f'title_{lang}') or self.title_ar or '',
            'subtitle': getattr(self, f'subtitle_{lang}') or self.subtitle_ar or '',
            'description': getattr(self, f'description_{lang}') or self.description_ar or '',
            'badge_text': getattr(self, f'badge_text_{lang}') or self.badge_text_ar or '',
            'badge_color': badge_color,
            'show_countdown': bool(self.show_countdown and end_ms),
            'end_ms': end_ms,
            'countdown_title': getattr(self, f'countdown_title_{lang}') or '',
            'days_label': getattr(self, f'days_label_{lang}') or '',
            'hours_label': getattr(self, f'hours_label_{lang}') or '',
            'mins_label': getattr(self, f'mins_label_{lang}') or '',
            'terms': getattr(self, f'terms_{lang}') or self.terms_ar or '',
            'social_proof': getattr(self, f'social_proof_{lang}') or '',
            'whatsapp_url': self._whatsapp_url(is_english, highlight),
            'whatsapp_btn': getattr(self, f'whatsapp_btn_{lang}') or (
                'Get the Offer on WhatsApp' if is_english else 'احصل على العرض عبر واتساب'),
            'close_btn': getattr(self, f'close_btn_{lang}') or ('Maybe Later' if is_english else 'ربما لاحقاً'),
            'delay_seconds': max(0, self.delay_seconds or 0),
            'exit_intent': self.exit_intent,
            'display_frequency': self.display_frequency or 'every_page',
            'cookie_duration': max(1, self.cookie_duration or 1),
        }

    def get_offer_data(self):
        """Legacy method - returns Arabic content by default"""
        return self.get_offer_data_localized(is_english=False)

    def action_view_leads(self):
        """Open list of Leads from this offer"""
        self.ensure_one()
        return {
            'name': f'Registrations: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('x_popup_offer_id', '=', self.id)],
            'context': {
                'default_x_popup_offer_id': self.id,
                'default_x_source_type': 'popup',
            },
        }

    # ============================================================
    # CONSTRAINTS & VALIDATIONS
    # ============================================================

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate dates"""
        for offer in self:
            if offer.end_date and offer.start_date:
                if offer.end_date < offer.start_date:
                    raise models.ValidationError(
                        _('End date must be after start date!')
                    )

    @api.constrains('target_type', 'target_page', 'target_path')
    def _check_target(self):
        for offer in self:
            if offer.target_type != 'page':
                continue
            if not offer.target_page:
                raise ValidationError(_('Please choose the course page for this offer.'))
            if offer.target_page == 'custom':
                path = (offer.target_path or '').strip()
                if not path.startswith('/') or path.startswith('//') or len(path) > 200:
                    raise ValidationError(_('Page path must start with "/" (e.g. /it-programs).'))

    @api.constrains('delay_seconds')
    def _check_delay(self):
        """Validate delay value"""
        for offer in self:
            if offer.delay_seconds < 0:
                raise models.ValidationError(
                    _('Delay cannot be negative!')
                )

    @api.constrains('cookie_duration')
    def _check_cookie_duration(self):
        """Validate cookie duration"""
        for offer in self:
            if offer.cookie_duration < 1:
                raise models.ValidationError(
                    _('Cookie duration must be at least 1 day!')
                )