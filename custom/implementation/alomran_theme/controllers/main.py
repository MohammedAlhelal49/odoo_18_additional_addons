# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.tools import plaintext2html
from markupsafe import Markup
from datetime import datetime, timedelta
from .openai_ads import send_lead_created, lead_event_id, pixel_id as openai_pixel_id
from . import english_landing_content as english_content
from . import tutoring_landing_content as tutoring_content
from . import women_landing_content as women_content
from . import home_content
from . import branches_content
from . import site_facts
from . import about_content
from . import courses_content
from . import contact_content
from urllib.parse import quote, urlencode as url_encode
import json
import re
import logging

_logger = logging.getLogger(__name__)

# ============================================================
# SECURITY HELPERS
# ============================================================
RATE_LIMIT_COUNT = 10           # أقصى عدد طلبات من نفس الـ IP (كل فورمات الموقع)
RATE_LIMIT_WINDOW_MIN = 60      # خلال هالمدة (دقائق)

_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_UTM_RE = re.compile(r'^[\w.\-]{1,50}$')
_YT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')
_CLICK_ID_RE = re.compile(r'^[A-Za-z0-9_\-]{10,200}$')
_WA_NUMBER_RE = re.compile(r'^\d{8,15}$')
# فيديو الهيرو: ملف محلي (/...mp4|webm) أو مرفق Odoo (/web/content/<id>) أو https
_HERO_VIDEO_URL_RE = re.compile(
    r'^(?:/web/content/\d+(?:[/?][^\s"\'<>]*)?'
    r'|(?:/(?!/)|https://)[^\s"\'<>]+\.(?:mp4|webm)(?:\?[^\s"\'<>]*)?)$', re.I)
_HERO_POSTER_URL_RE = re.compile(
    r'^(?:/web/(?:content|image)/\d+(?:[/?][^\s"\'<>]*)?'
    r'|(?:/(?!/)|https://)[^\s"\'<>]+\.(?:jpe?g|png|webp)(?:\?[^\s"\'<>]*)?)$', re.I)
# الأماكن الافتراضية إذا رفعت الفيديو جوا المويول
ENGLISH_HERO_VIDEO_FILES = ('alomran_theme/static/src/video/english_hero.mp4',
                            'alomran_theme/static/src/video/english_hero.webm')
ENGLISH_HERO_POSTER_FILES = ('alomran_theme/static/src/video/english_hero_poster.webp',
                             'alomran_theme/static/src/video/english_hero_poster.jpg')
TUTORING_HERO_VIDEO_FILES = ('alomran_theme/static/src/video/tutoring_hero.mp4',
                             'alomran_theme/static/src/video/tutoring_hero.webm')
TUTORING_HERO_POSTER_FILES = ('alomran_theme/static/src/video/tutoring_hero_poster.webp',
                              'alomran_theme/static/src/video/tutoring_hero_poster.jpg')
# فيديو هيرو الصفحة الرئيسية (اختياري — بدونه الهيرو متل ما كان)
HOME_HERO_VIDEO_FILES = ('alomran_theme/static/src/video/home_hero.mp4',
                         'alomran_theme/static/src/video/home_hero.webm')
HOME_HERO_POSTER_FILES = ('alomran_theme/static/src/video/home_hero_poster.webp',
                          'alomran_theme/static/src/video/home_hero_poster.jpg')
WOMEN_HERO_VIDEO_FILES = ('alomran_theme/static/src/video/women_hero.mp4',
                          'alomran_theme/static/src/video/women_hero.webm')
WOMEN_HERO_POSTER_FILES = ('alomran_theme/static/src/video/women_hero_poster.webp',
                           'alomran_theme/static/src/video/women_hero_poster.jpg')

# ------------------------------------------------------------
# الفروع: قيمة الفرع بالفورم -> اسم الشركة بـ Odoo
# نفس القيم والتجميع بفورم تواصل معنا وصفحة الإنجليزي وفورم حماة الوطن.
# القيم مربوطة بالـ template المشترك alomran_theme.branch_select_options
# ------------------------------------------------------------
BRANCH_MAPPING = {
    'وسط المدينة - العين':    'Al Murabba',
    'اليحر مول - العين':      'Al Yahr Branch',
    'مكاني مول زاخر - العين': 'Zakhir Branch',
    'البراري مول - العين':    'Al Barari Mall Branch',
    'الفوعة مول - العين':     'Al Foaa Branch',
    'مزيد مول - ابوظبي':      'Mazyad Mall Branch',
    'شارع المرور - ابوظبي':   'Al Meroor Branch',
    'القرهود - دبي':          'Al Garhoud Branch',
    'البرشا - دبي':           'Al Barsha Branch',
    'سنترال مول - الشارقة':   'AL OMRAN EDUCATION LANGUAGES CENTER L.L.C',
    'راك مول - راس الخيمة':   'Ras Al Khaimah Branch',
    'برج العوضي - الفجيرة':   '-ALOMRAN FOR TRAINING AND DEVELOPING CENTER LLC-',
}

# الإمارة من الفرع (منشان حقل x_emirate والتقارير يضلوا شغالين)
_BRANCH_SUFFIX_EMIRATE = {
    'العين': 'al_ain',
    'ابوظبي': 'abu_dhabi',
    'دبي': 'dubai',
    'الشارقة': 'sharjah',
    'راس الخيمة': 'ras_al_khaimah',
    'الفجيرة': 'fujairah',
}


def _branch_emirate(branch):
    suffix = (branch or '').rsplit(' - ', 1)[-1].strip()
    return _BRANCH_SUFFIX_EMIRATE.get(suffix, False)


ENGLISH_LANDING_URL = '/english-ielts'
ENGLISH_DUPLICATE_HOURS = 24    # نفس الرقم + نفس البرنامج خلال هالمدة = طلب مكرر

# صفحة الدروس الخصوصية والمتابعة المدرسية والدعم الجامعي (نفس نمط صفحة الإنجليزي)
TUTORING_LANDING_URL = '/private-tutoring'
TUTORING_DUPLICATE_HOURS = 24

# صفحة الدورات المهنية والإبداعية للسيدات (نفس نمط صفحة الدروس الخصوصية)
WOMEN_LANDING_URL = '/women-courses'
WOMEN_DUPLICATE_HOURS = 24


def _clean(value, max_len=200, multiline=False):
    """تنظيف مدخلات الزائر للتخزين: نص بس، بدون محارف تحكم، بطول محدود.
    الـ escape بيصير وقت العرض (plaintext2html / Markup / t-esc)."""
    if value is None or isinstance(value, (dict, list, tuple, set, bool)):
        return ''
    value = _CTRL_RE.sub('', str(value))
    if not multiline:
        value = ' '.join(value.split())
    return value.strip()[:max_len]


def _valid_email(email):
    return bool(email) and len(email) <= 150 and bool(_EMAIL_RE.match(email))


def home_content_org_id():
    """@id المؤسسة بالـ JSON-LD (نفس الموجود بصفحات الهبوط)."""
    return english_content.ORG_ID


def _client_ip():
    # مع proxy_mode = True بـ odoo.conf بتكون remote_addr هي IP الزائر الحقيقي
    return request.httprequest.remote_addr or ''


def _rate_limited(ip):
    if not ip:
        return False
    try:
        since = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MIN)
        count = request.env['crm.lead'].sudo().with_context(active_test=False).search_count([
            ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            ('description', 'ilike', f'IP: {ip}'),
        ])
        return count >= RATE_LIMIT_COUNT
    except Exception as e:
        _logger.warning('Rate-limit check error: %s', e)
        return False


def _description(lines, ip):
    """وصف الـ lead كنص عادي -> HTML آمن (escape + أسطر)."""
    text = '\n'.join(lines + [f'IP: {ip}'])
    return plaintext2html(text)


class AlomranWebsite(http.Controller):

    def _get_current_lang(self):
        """Get current language code"""
        lang = request.env.lang or request.httprequest.cookies.get('frontend_lang') or 'ar_001'
        return lang

    def _is_english(self):
        """Check if current language is English"""
        return self._get_current_lang().startswith('en')

    # ============================================================
    # HELPER METHODS FOR POPUP
    # ============================================================

    def _clean_phone(self, phone):
        """Clean phone number from spaces and special characters"""
        if not phone:
            return ''
        return ''.join(filter(str.isdigit, phone.replace('+', '')))

    def _validate_phone(self, phone):
        """Validate phone number format"""
        if not phone:
            return False
        cleaned = self._clean_phone(phone)
        return len(cleaned) >= 9 and len(cleaned) <= 15

    def _is_duplicate_submission(self, phone, offer_id):
        """Check if same phone submitted in last 24 hours"""
        try:
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(hours=24)

            domain = [
                ('phone', '=', phone),
                ('create_date', '>=', yesterday.strftime('%Y-%m-%d %H:%M:%S')),
            ]

            if offer_id and 'x_popup_offer_id' in request.env['crm.lead']._fields:
                domain.append(('x_popup_offer_id', '=', int(offer_id)))

            existing = request.env['crm.lead'].sudo().search_count(domain)
            return existing > 0
        except Exception as e:
            _logger.warning(f"Error checking duplicate: {e}")
            return False

    def _get_error_message(self, error_type):
        """Get localized error message"""
        is_en = self._is_english()
        messages = {
            'name_required': 'Please enter your name' if is_en else 'الرجاء إدخال اسمك',
            'phone_required': 'Please enter your phone number' if is_en else 'الرجاء إدخال رقم الهاتف',
            'phone_invalid': 'Please enter a valid phone number' if is_en else 'الرجاء إدخال رقم هاتف صحيح',
            'duplicate': 'You have already registered for this offer' if is_en else 'لقد سجلت مسبقاً في هذا العرض',
            'general': 'An error occurred, please try again' if is_en else 'حدث خطأ، يرجى المحاولة مرة أخرى',
            'required': 'Missing required fields' if is_en else 'الحقول المطلوبة مفقودة',
            'email_invalid': 'Please enter a valid email address' if is_en else 'الرجاء إدخال بريد إلكتروني صحيح',
            'rate_limited': 'Too many attempts, please try again later' if is_en else 'تم تجاوز عدد المحاولات المسموح، يرجى المحاولة لاحقاً',
            'branch_required': 'Please select a branch' if is_en else 'الرجاء اختيار الفرع',
        }
        return messages.get(error_type, messages['general'])

    def _get_success_message(self, is_english):
        """Get localized success message"""
        if is_english:
            return 'Thank you for registering! We will contact you soon.'
        return 'شكراً لتسجيلك! سنتواصل معك قريباً.'

    def _build_lead_description(self, offer, is_english):
        """Build lead description"""
        if not offer:
            return 'Popup registration' if is_english else 'تسجيل من النافذة المنبثقة'

        offer_name = getattr(offer, 'name_en', None) if is_english else None
        if not offer_name:
            offer_name = getattr(offer, 'name', 'Offer')
        return f"{'Popup Offer' if is_english else 'عرض النافذة المنبثقة'}: {offer_name}"

    def _get_or_create_utm_source(self, source_name):
        """Get or create UTM source"""
        source_name = (source_name or '').strip()
        # بس أسماء نظيفة، منشان ما حدا يعبّي utm.source بقيم عشوائية
        if not _UTM_RE.match(source_name):
            return False
        try:
            utm_source = request.env['utm.source'].sudo().search([('name', '=', source_name)], limit=1)
            if not utm_source:
                utm_source = request.env['utm.source'].sudo().create({'name': source_name})
            return utm_source.id
        except Exception as e:
            _logger.warning(f"Error with UTM source: {e}")
            return False

    def _is_valid_selection_value(self, model_name, field_name, value):
        """Check if a value is valid for a selection field"""
        try:
            field = request.env[model_name]._fields.get(field_name)
            if not field:
                return False
            if field.type != 'selection':
                return True
            if callable(field.selection):
                selection_values = [s[0] for s in field.selection(request.env[model_name])]
            else:
                selection_values = [s[0] for s in field.selection]
            return value in selection_values
        except Exception as e:
            _logger.warning(f"Error checking selection value: {e}")
            return False

    def _safe_set_field(self, vals, model_name, field_name, value):
        """Safely set a field value only if it's valid"""
        try:
            if field_name not in request.env[model_name]._fields:
                _logger.debug(f"Field {field_name} not found in {model_name}")
                return False
            field = request.env[model_name]._fields[field_name]
            if field.type == 'selection':
                if not self._is_valid_selection_value(model_name, field_name, value):
                    _logger.warning(f"Invalid selection value '{value}' for {model_name}.{field_name}")
                    return False
            vals[field_name] = value
            return True
        except Exception as e:
            _logger.warning(f"Error setting field {field_name}: {e}")
            return False

    # ============================================================
    # MAIN PAGES
    # ============================================================

    @http.route('/', type='http', auth='public', website=True)
    def homepage(self, **kwargs):
        """الصفحة الرئيسية — النصوص من controllers/home_content.py"""
        is_en = self._is_english()
        content = home_content.get_content(is_en)

        # بطاقات الإمارات (دبي / أبوظبي / العين): الفروع من نفس بيانات صفحة الفروع
        all_branches = [self._branch_view_data(b) for b in self._get_branches_data(is_en)]
        home_cities = []
        for cfg in content['branches']['cities']:
            items = [b for b in all_branches if b['city'] == cfg['city']]
            if not items:
                continue
            home_cities.append({
                'icon': cfg['icon'],
                'city': cfg['city'],
                'title': content['branches']['city_title'].format(city=cfg['city']),
                'count': branches_content.count_label(len(items), is_en),
                'branches': items,
                'cta': content['branches']['city_cta'].format(city=cfg['city']),
                'url': '/branches?' + url_encode({'city': cfg['city']}) + '#branches-list',
            })

        return request.render('alomran_theme.homepage', {
            'home_cities': home_cities,
            'h': content,
            'is_en': is_en,
            # فيديو الهيرو: alomran.home_hero_video_url أو static/src/video/home_hero.mp4
            'hero_media': self._hero_media('alomran.home_hero', HOME_HERO_VIDEO_FILES, HOME_HERO_POSTER_FILES),
            # صور اختيارية: بس الملفات الموجودة فعلياً
            'home_images': {key: self._first_static_file(files)
                            for key, files in home_content.IMAGE_FILES.items()},
            'wa_link': self._whatsapp_link(content['wa_general'], 'alomran.home_whatsapp',
                                           home_content.WHATSAPP_NUMBER),
        })

    @http.route('/about', type='http', auth='public', website=True)
    def about(self, **kwargs):
        """About Us page — النصوص من controllers/about_content.py"""
        is_en = self._is_english()
        content = about_content.get_content(is_en)
        return request.render('alomran_theme.about_template', {
            'a': content,
            'is_en': is_en,
            'hero_photo': self._first_static_file(home_content.IMAGE_FILES['hero']),
            'story_image': self._first_static_file(home_content.IMAGE_FILES['logo']),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
        })

    @http.route('/courses', type='http', auth='public', website=True)
    def courses(self, **kwargs):
        """Courses page — النصوص والدورات من controllers/courses_content.py"""
        is_en = self._is_english()
        content = courses_content.get_content(is_en)
        return request.render('alomran_theme.courses_template', {
            'cc': content,
            'is_en': is_en,
            'hero_photo': self._first_static_file(home_content.IMAGE_FILES['hero']),
            'wa_link': self._whatsapp_link(content['wa_message'], 'alomran.home_whatsapp',
                                           home_content.WHATSAPP_NUMBER),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
        })

    def _get_branches_data(self, is_en):
        """Get all branches data - centralized for reuse"""
        return [
            {
                'slug': 'sharjah-central-mall',
                'name': 'Sharjah Branch | Central Mall' if is_en else 'فرع الشارقة | سنترال مول',
                'city': 'Sharjah' if is_en else 'الشارقة',
                'badge_class': 'bg-warning',
                'location': 'Sharjah - Central Mall - First floor' if is_en else 'الشارقة - سنترال مول - طـ 1',
                'phone': '+971 56 414 1409',
                'phone_link': '971564141409',
                'maps_link': 'https://maps.app.goo.gl/SqjyxrKBsU5LsyPN6',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1846252.4627421533!2d57.85537719726561!3d25.3390614588184!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e5f5987a4caac77%3A0xb875acbf965eb114!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2YTYtNin2LHZgtip!5e0!3m2!1sar!2slt!4v1771378619575!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/sharjah_center.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'alain-city-center',
                'name': 'Al Ain Branch | Downtown' if is_en else 'فرع العين | وسط المدينة',
                'city': 'Al Ain' if is_en else 'العين',
                'badge_class': 'bg-primary',
                'location': 'Al Ain - Downtown - Al Murabba' if is_en else 'العين - وسط المدينة - المربعة',
                'phone': '+971 56 434 2889',
                'phone_link': '971505829697',
                'maps_link': 'https://maps.app.goo.gl/CATYSRrQgXAEVbqy9',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1862946.6091659945!2d58.21243286132814!3d24.221919199872975!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e8ab78bb01d0847%3A0x402d1b2a947d37f1!2sAl%20Omran%20center%20for%20training%20and%20developing!5e0!3m2!1sar!2slt!4v1771377608099!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/alain_murbaa.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'alain-foah-mall',
                'name': 'Al Ain Branch | Al Foah Mall' if is_en else 'فرع العين | الفوعة مول',
                'city': 'Al Ain' if is_en else 'العين',
                'badge_class': 'bg-primary',
                'location': 'Al Ain - Al Foah Mall' if is_en else 'العين - الفوعة مول',
                'phone': '+971 56 573 3506',
                'phone_link': '971565733506',
                'maps_link': 'https://maps.app.goo.gl/zzUzT5iS8wZXjAVc7',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1861166.29000234!2d58.23165893554686!3d24.343343107244273!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ef54b16a9464c27%3A0x7c74d0bf4c530123!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2YTZgdmI2LnYqQ!5e0!3m2!1sar!2slt!4v1771377722255!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/alain_alfouaa.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'alain-barari-mall',
                'name': 'Al Ain Branch | Al Barari Mall' if is_en else 'فرع العين | البراري مول',
                'city': 'Al Ain' if is_en else 'العين',
                'badge_class': 'bg-primary',
                'location': 'Al Ain - Al Barari Mall' if is_en else 'العين - البراري مول',
                'phone': '+971 56 635 9986',
                'phone_link': '971566359986',
                'maps_link': 'https://maps.app.goo.gl/cxZwAUdZvCV33dnHA',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3642.4396765191404!2d55.8298772!3d24.086028799999998!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e8abf002a3c24e3%3A0x612b51ca0e6fedca!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2YTZiNix2KfYqiDZhdmI2YQ!5e0!3m2!1sar!2slt!4v1771377222330!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/alain_albrari.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'alain-yahar-mall',
                'name': 'Al Ain Branch | Al Yahar Mall' if is_en else 'فرع العين | اليحر مول',
                'city': 'Al Ain' if is_en else 'العين',
                'badge_class': 'bg-primary',
                'location': 'Al Ain - Al Yahar Mall' if is_en else 'العين - اليحر مول',
                'phone': '+971 54 247 6015',
                'phone_link': '971542476015',
                'maps_link': 'https://maps.app.goo.gl/wvRP9zkHkaLgHXuk8',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1862964.9282502981!2d57.98171997070311!3d24.220666802807237!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e8aab1b21a70995%3A0x8b4e507f5a233cac!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2YTYudin2YXYsdip!5e0!3m2!1sar!2slt!4v1771377929835!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/allain_alyaher.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'zakher-makani-mall',
                'name': 'Zakher Branch | Makani Mall' if is_en else 'فرع زاخر | مكاني مول',
                'city': 'Al Ain' if is_en else 'العين',
                'badge_class': 'bg-primary',
                'location': 'Zakher - Makani Mall' if is_en else 'زاخر - مكاني مول',
                'phone': '+971 56 434 2889',
                'phone_link': '971505829697',
                'maps_link': 'https://maps.app.goo.gl/x52eSzwpa7HPwbrbA',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1864592.4783181893!2d58.14102172851561!3d24.10915419847753!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e8abbbcfe88aafb%3A0x6f60a31b074fad23!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INmF2YPYp9mG2Yog2YXZiNmEINiy2KfYrtix!5e0!3m2!1sar!2slt!4v1771377839762!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/alain_zakher.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'abudhabi-mazyed-mall',
                'name': 'Abu Dhabi Branch | Mazyed Mall' if is_en else 'فرع أبوظبي | مزيد مول',
                'city': 'Abu Dhabi' if is_en else 'أبوظبي',
                'badge_class': 'bg-success',
                'location': 'Abu Dhabi - Mazyed Mall - Second floor' if is_en else 'أبوظبي - مزيد مول - طـ 2',
                'phone': '+971 56 659 9919',
                'phone_link': '971566599919',
                'maps_link': 'https://maps.app.goo.gl/2TZ819WHstLZwZXx7',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d232588.58344729056!2d54.845294952392585!3d24.374462733901805!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e5e4723b6b3e2ed%3A0x68af7c666c2da83c!2z2LTYp9ix2Lkg2LPZhNi32KfZhiDYqNmGINmF2K3ZhdivINin2YTZgtio2YrYs9mKIC8g2YXYstmK2K8g2YXZiNmE!5e0!3m2!1sar!2slt!4v1771378027540!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/abudhabi_mazyd.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'abudhabi-muroor',
                'name': 'Abu Dhabi Branch | Al Muroor' if is_en else 'فرع أبوظبي | المرور',
                'city': 'Abu Dhabi' if is_en else 'أبوظبي',
                'badge_class': 'bg-success',
                'location': 'Abu Dhabi - Al Muroor Street' if is_en else 'أبوظبي - شارع المرور',
                'phone': '+971 50 172 0927',
                'phone_link': '971501720927',
                'maps_link': 'https://maps.app.goo.gl/nezYWL2BYTEUHvbf9',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3631.2847310108154!2d54.3762301850047!3d24.475589484236885!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e5e67006bbe0b5f%3A0x97b4ffaefcae532a!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2KjZiNi42KjZiiDYtNin2LHYuSDYp9mE2YXYsdmI2LE!5e0!3m2!1sar!2slt!4v1771378199267!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/abudabi_almoror.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'dubai-garhoud',
                'name': 'Dubai Branch | Al Garhoud' if is_en else 'فرع دبي | القرهود',
                'city': 'Dubai' if is_en else 'دبي',
                'badge_class': 'bg-info',
                'location': 'Dubai - Al Garhoud' if is_en else 'دبي - القرهود',
                'phone': '+971 50 559 5228',
                'phone_link': '971505595228',
                'maps_link': 'https://maps.app.goo.gl/KPe6jwVUEFZJ9fKTA',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d923783.5359432719!2d56.56105041503905!3d25.252769556326484!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e5f5dcc0638abf3%3A0xf7abd5f5920bdc28!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INiv2KjZiiDYp9mE2YLYsdmH2YjYrw!5e0!3m2!1sar!2slt!4v1771378338236!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/dubai_alkarhod.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'dubai-barsha',
                'name': 'Dubai Branch | Al Barsha' if is_en else 'فرع دبي | البرشاء',
                'city': 'Dubai' if is_en else 'دبي',
                'badge_class': 'bg-info',
                'location': 'Dubai - Al Barsha' if is_en else 'دبي - البرشاء',
                'phone': '+971 50 610 8091',
                'phone_link': '971506108091',
                'maps_link': 'https://maps.app.goo.gl/f6kEvPw7FzKpSu3H8',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3612.7991416704585!2d55.184069699999995!3d25.1086597!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3e5f6bd7b2fe688d%3A0xbb00ef3993ecffcb!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INi02KfYsdi5INin2YTYtNmK2K4g2LLYp9mK2K8g2K_YqNmK!5e0!3m2!1sar!2slt!4v1771378453145!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/dubai_albarshaa.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'rak-rak-mall',
                'name': 'Ras Al Khaimah Branch | RAK Mall' if is_en else 'فرع رأس الخيمة | راك مول',
                'city': 'Ras Al Khaimah' if is_en else 'رأس الخيمة',
                'badge_class': 'bg-danger',
                'location': 'Ras Al Khaimah - RAK Mall' if is_en else 'رأس الخيمة - راك مول',
                'phone': '+971 52 862 0601',
                'phone_link': '971528620601',
                'maps_link': 'https://maps.app.goo.gl/pV2LmsL4NZCxzcrc9',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3592.9505634965103!2d55.95852920000001!3d25.772196399999995!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ef677f73614a557%3A0x85e8e4499d907f54!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INix2KPYsyDYp9mE2K7ZitmF2Kk!5e0!3m2!1sar!2slt!4v1771378535800!5m2!1sar!2slt',
                'image': '/alomran_theme/static/src/img/branches/rasalkhima_rakmall.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
            {
                'slug': 'fujairah-awadhi-tower',
                'name': 'Fujairah Branch | Al Awadhi Tower' if is_en else 'فرع الفجيرة | برج العوضي',
                'city': 'Fujairah' if is_en else 'الفجيرة',
                'badge_class': 'bg-secondary',
                'location': 'Fujairah - Al Awadhi Tower' if is_en else 'الفجيرة - برج العوضي',
                'phone': '+971 50 553 2260',
                'phone_link': '971505532260',
                'maps_link': 'https://share.google/llCYh8OFd8Dtd9QRx',
                'embed_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3849.3607877784775!2d56.325645059608775!3d25.122631035205597!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ef4f9e31bb74715%3A0x8a87bd3e2817d3b0!2z2YXYsdmD2LIg2KfZhNi52YXYsdin2YYg2YTZhNiq2K_YsdmK2Kgg2Ygg2KfZhNiq2LfZiNmK2LEg2YHYsdi5INin2YTZgdis2YrYsdip!5e0!3m2!1sar!2sus!4v1790759433887!5m2!1sar!2sus',
                'image': '/alomran_theme/static/src/img/hero-bg.jpg',
                'working_hours': 'Saturday - Thursday: 8:00 AM - 8:00 PM' if is_en else 'السبت - الخميس: 8:00 ص - 8:00 م',
            },
        ]

    @http.route('/branches', type='http', auth='public', website=True)
    def branches(self, **kwargs):
        """Branches page — النصوص من controllers/branches_content.py"""
        is_en = self._is_english()
        # الصورة بس إذا الملف موجود فعلياً، وإلا بيطلع البديل (لون + أيقونة)
        branches = [self._branch_view_data(b) for b in self._get_branches_data(is_en)]

        # التوزيع الجغرافي: بيتحسب من بيانات الفروع (بترتيب أول ظهور لكل إمارة)
        counts = {}
        for b in branches:
            counts[b['city']] = counts.get(b['city'], 0) + 1
        cities = [{'name': c, 'count': n, 'count_label': branches_content.count_label(n, is_en)}
                  for c, n in counts.items()]

        # العدد الرسمي (site_facts.BRANCHES) — مش عدد البطاقات
        content = branches_content.get_content(is_en, site_facts.BRANCHES)
        return request.render('alomran_theme.branches_template', {
            'hero_photo': self._first_static_file(home_content.IMAGE_FILES['hero']),
            'branches': branches,
            'cities': cities,
            'bc': content,
            'is_en': is_en,
            'wa_link': self._whatsapp_link(content['wa_message'], 'alomran.home_whatsapp',
                                           home_content.WHATSAPP_NUMBER),
        })

    def _branch_view_data(self, b):
        """تجهيز فرع للعرض: العنوان المختصر + الصورة بس إذا الملف موجود."""
        item = dict(b)
        # "فرع العين | البراري مول" → عنوان "البراري مول" + "فرع العين"
        parts = [p.strip() for p in b['name'].split('|')]
        item['title'] = parts[-1]
        item['prefix'] = parts[0] if len(parts) > 1 else ''
        image = (b.get('image') or '').lstrip('/')
        item['image_url'] = self._first_static_file((image,)) if image.startswith('alomran_theme/static/') else ''
        return item

    @http.route('/branch/<string:slug>', type='http', auth='public', website=True)
    def branch_detail(self, slug, **kwargs):
        """صفحة الفرع الواحد — النصوص من branches_content.get_detail_content"""
        is_en = self._is_english()
        all_branches = self._get_branches_data(is_en)
        branch = next((b for b in all_branches if b.get('slug') == slug), None)
        if not branch:
            return request.redirect('/branches')

        branch = self._branch_view_data(branch)
        content = branches_content.get_detail_content(is_en)

        # فروع تانية: نفس الإمارة أولاً، وإذا ما في منكمّل من باقي الفروع (حد أقصى 3)
        same_city = [self._branch_view_data(b) for b in all_branches
                     if b['slug'] != slug and b['city'] == branch['city']]
        others = same_city[:3]
        if len(others) < 3:
            others += [self._branch_view_data(b) for b in all_branches
                       if b['slug'] != slug and b['city'] != branch['city']][:3 - len(others)]
        others_title = (content['others_same'].format(city=branch['city']) if same_city
                        else content['others_any'])

        # JSON-LD: الفرع كموقع تابع للمؤسسة
        schema = self._json_ld({
            '@context': 'https://schema.org',
            '@type': 'EducationalOrganization',
            'name': branch['name'],
            'parentOrganization': {'@id': home_content_org_id()},
            'telephone': branch['phone'],
            'address': {
                '@type': 'PostalAddress',
                'streetAddress': branch['location'],
                'addressLocality': branch['city'],
                'addressCountry': 'AE',
            },
            'hasMap': branch.get('maps_link') or None,
            'url': request.httprequest.url_root.rstrip('/') + f'/branch/{slug}',
        })

        return request.render('alomran_theme.branch_detail_template', {
            'hero_photo': self._first_static_file(home_content.IMAGE_FILES['hero']),
            'branch': branch,
            'others': others,
            'others_title': others_title,
            'd': content,
            'is_en': is_en,
            'schema_json': schema,
            'wa_link': self._whatsapp_link(content['wa_message'].format(branch=branch['name']),
                                           'alomran.home_whatsapp', home_content.WHATSAPP_NUMBER),
            'alomran_page_title': content['page_title'].format(branch=branch['name']),
            'alomran_page_description': content['page_description'].format(
                branch=branch['name'], location=branch['location'],
                phone=branch['phone'], hours=branch.get('working_hours', '')),
        })

    @http.route('/contact', type='http', auth='public', website=True)
    def contact(self, **kwargs):
        """Contact Us page — النصوص من controllers/contact_content.py"""
        is_en = self._is_english()
        content = contact_content.get_content(is_en)
        return request.render('alomran_theme.custom_contact_template', {
            'ct': content,
            'is_en': is_en,
            'social': contact_content.SOCIAL,
            'phone_number': contact_content.PHONE_NUMBER,
            'phone_display': contact_content.PHONE_DISPLAY,
            'email': contact_content.EMAIL,
            'hero_photo': self._first_static_file(home_content.IMAGE_FILES['hero']),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
        })

    @http.route('/contact/submit', type='http', auth='public', methods=['POST'], csrf=True, website=True)
    def contact_submit(self, **post):
        """Process contact form - Stores in CRM + sends email"""
        is_en = self._is_english()
        ip = _client_ip()

        def _error(key='general'):
            return request.render('alomran_theme.contact_error', {
                'error': self._get_error_message(key),
                'cr': contact_content.get_result_content(is_en),
            })

        # Honeypot: البوت بيعبّي الحقل المخفي — منرجّع نجاح وهمي بدون lead
        if post.get('website_url'):
            _logger.info('Contact form: honeypot triggered (ip=%s)', ip)
            return request.render('alomran_theme.contact_success', {
                'name': '', 'cr': contact_content.get_result_content(is_en)})

        name = _clean(post.get('name'), 100)
        email = _clean(post.get('email_from'), 150)
        phone = _clean(post.get('phone'), 20)
        subject = _clean(post.get('subject'), 150)
        message = _clean(post.get('body_html'), 3000, multiline=True)
        branch = _clean(post.get('branch'), 100)

        if not name or not phone or not message:
            return _error('required')
        if not self._validate_phone(phone):
            return _error('phone_invalid')
        if email and not _valid_email(email):
            return _error('email_invalid')
        if branch not in BRANCH_MAPPING:
            return _error('branch_required')
        if _rate_limited(ip):
            _logger.warning('Contact form: rate limit hit (ip=%s)', ip)
            return _error('rate_limited')

        try:
            # 1. Create CRM Lead
            lead_values = {
                'name': name,
                'contact_name': name,
                'phone': phone,
                'email_from': email or False,
                'description': _description([
                    f"{'Subject' if is_en else 'الموضوع'}: {subject}",
                    f"{'Branch' if is_en else 'الفرع'}: {branch}",
                    '',
                    f"{'Message' if is_en else 'الرسالة'}:",
                    message,
                    '',
                    f"{'Source' if is_en else 'المصدر'}: {'Contact Us Page' if is_en else 'صفحة اتصل بنا'}",
                ], ip),
                'type': 'opportunity',
            }

            # الشركة والـ Sales Admin حسب الفرع
            company_id, default_salesperson_id = self._branch_assignment(branch)
            lead_values['company_id'] = company_id
            lead_values['user_id'] = default_salesperson_id
            self._apply_branch_fields(lead_values, branch)

            self._safe_set_field(lead_values, 'crm.lead', 'x_source_type', 'contact')
            lead = request.env['crm.lead'].sudo().create(lead_values)
            _logger.info('Contact form lead created: id=%s', lead.id)
            send_lead_created(lead)

            # 2. Send email notification
            # كل مدخلات الزائر بتنعمل escape (Markup.format) — ما في HTML injection بإيميل الموظفين.
            # المرسل هو إيميل الشركة (مش إيميل الزائر) منشان ما يصير spoofing؛ إيميل الزائر بالـ Reply-To.
            label = (lambda en, ar: en if is_en else ar)
            body_html = Markup(
                '<h3>{title}</h3>'
                '<p><strong>{l_name}:</strong> {name}</p>'
                '<p><strong>{l_email}:</strong> {email}</p>'
                '<p><strong>{l_phone}:</strong> {phone}</p>'
                '<p><strong>{l_branch}:</strong> {branch}</p>'
                '<p><strong>{l_subject}:</strong> {subject}</p>'
                '<p><strong>{l_message}:</strong></p>'
                '{message}'
                '<hr/><p><small>Lead ID: {lead_id}</small></p>'
            ).format(
                title=label('New inquiry from website', 'استفسار جديد من الموقع'),
                l_name=label('Name', 'الاسم'), name=name,
                l_email=label('Email', 'البريد الإلكتروني'), email=email,
                l_phone=label('Phone', 'الهاتف'), phone=phone,
                l_branch=label('Branch', 'الفرع'), branch=branch,
                l_subject=label('Subject', 'الموضوع'), subject=subject,
                l_message=label('Message', 'الرسالة'),
                message=plaintext2html(message),
                lead_id=lead.id,
            )
            mail_values = {
                'subject': (f'New inquiry from {name} - {subject}' if is_en
                            else f'استفسار جديد من {name} - {subject}'),
                'email_to': 'alomran.td@gmail.com',
                'body_html': body_html,
            }
            company_email = request.env.company.sudo().email_formatted
            if company_email:
                mail_values['email_from'] = company_email
            if email:
                mail_values['reply_to'] = email
            request.env['mail.mail'].sudo().create(mail_values)

            return request.render('alomran_theme.contact_success', {
                'name': name, 'oai_event_id': lead_event_id(lead),
                'cr': contact_content.get_result_content(is_en)})

        except Exception:
            _logger.exception('Contact form error (ip=%s)', ip)
            return _error('general')

    # ============================================================
    # POP-UP OFFER ENDPOINTS
    # ============================================================

    @http.route('/popup/settings', type='json', auth='public', website=True)
    def get_popup_settings(self, path=None, **kwargs):
        """العرض المناسب للصفحة: العرض الخاص بصفحة الكورس أولاً، وإلا العرض العام.
        ما بيعدّ مشاهدة — العدّ بيصير من /popup/track لما ينعرض فعلاً."""
        try:
            if 'popup.offer' not in request.env:
                return {'active': False}
            path = path if isinstance(path, str) else '/'
            offer = request.env['popup.offer'].sudo().get_offer_for_path(path[:300])
            if not offer:
                return {'active': False}
            is_english = self._is_english()
            data = offer.get_offer_data_localized(is_english)
            data.update({'active': True, 'is_english': is_english})
            return data
        except Exception:
            _logger.exception('Error getting popup settings')
            return {'active': False}

    @http.route('/popup/track', type='json', auth='public', methods=['POST'], website=True)
    def track_popup(self, offer_id=None, event=None, **kwargs):
        """عدّاد مشاهدات العرض ونقرات الواتساب."""
        field_name = {'view': 'view_count', 'click': 'click_count'}.get(event)
        try:
            offer_id = int(offer_id)
        except (TypeError, ValueError):
            return {'ok': False}
        if not field_name or offer_id <= 0:
            return {'ok': False}
        Offer = request.env['popup.offer'].sudo()
        offer = Offer.search(Offer._running_offers_domain() + [('id', '=', offer_id)], limit=1)
        if not offer:
            return {'ok': False}
        offer._increment_counter(field_name)
        return {'ok': True}

    # ملاحظة: /popup/submit انشال — التواصل بالعروض صار مباشرة عبر واتساب (بلا فورم).

    # ============================================================
    # SHARED REGISTRATION HANDLER (teachers / languages / it / courses)
    # ============================================================

    def _register_lead(self, post, label, source, require_course=False):
        is_en = self._is_english()
        ip = _client_ip()
        pick = (lambda pair: pair[0] if is_en else pair[1])
        try:
            name = _clean(post.get('name'), 100)
            phone = _clean(post.get('phone'), 20)
            email = _clean(post.get('email'), 150)
            course_name = _clean(post.get('course_name'), 200)
            branch = _clean(post.get('branch'), 100)

            if not name or not phone or (require_course and not course_name):
                return {'success': False, 'error': self._get_error_message('required')}
            # كل تسجيل لازم يكون مربوط بفرع من القائمة
            if branch not in BRANCH_MAPPING:
                return {'success': False, 'error': self._get_error_message('branch_required')}
            if not self._validate_phone(phone):
                return {'success': False, 'error': self._get_error_message('phone_invalid')}
            if email and not _valid_email(email):
                return {'success': False, 'error': self._get_error_message('email_invalid')}
            if _rate_limited(ip):
                _logger.warning('Registration form: rate limit hit (ip=%s)', ip)
                return {'success': False, 'error': self._get_error_message('rate_limited')}

            lead_values = {
                'name': name,
                'contact_name': name,
                'phone': phone,
                'email_from': email or False,
                'description': _description([
                    f"{pick(label)}: {course_name}",
                    f"{pick(('Branch', 'الفرع'))}: {branch}",
                    f"{pick(('Source', 'المصدر'))}: {pick(source)}",
                ], ip),
                'type': 'opportunity',
            }

            self._safe_set_field(lead_values, 'crm.lead', 'x_source_type', 'course')
            self._safe_set_field(lead_values, 'crm.lead', 'x_course_interest', course_name)
            self._apply_branch_fields(lead_values, branch)
            # الشركة والـ Sales Admin حسب الفرع (user_id دايماً صريح:
            # بدونه Odoo بيعيّن الزائر نفسه Public user كمندوب مبيعات)
            company_id, user_id = self._branch_assignment(branch)
            if company_id:
                lead_values['company_id'] = company_id
            lead_values['user_id'] = user_id or False
            lead = request.env['crm.lead'].sudo().create(lead_values)
            _logger.info('Registration lead created: id=%s source=%s', lead.id, source[0])
            send_lead_created(lead)
            return {'success': True, 'lead_id': lead.id, 'event_id': lead_event_id(lead)}

        except Exception:
            _logger.exception('Registration error (%s, ip=%s)', source[0], ip)
            return {'success': False, 'error': self._get_error_message('general')}

    # ============================================================
    # TEACHERS PAGE
    # ============================================================

    @http.route('/teachers', type='http', auth='public', website=True)
    def teachers(self, **kwargs):
        """Professional Teacher Training Programs page"""
        return request.render('alomran_theme.teachers_page', {})

    @http.route('/teachers/register', type='json', auth='public', methods=['POST'], website=True)
    def teachers_register(self, **post):
        """Process registration (Teachers page)"""
        return self._register_lead(
            post,
            label=('Registration for program', 'تسجيل في برنامج'),
            source=('Teachers page', 'صفحة المعلمين'),
            require_course=False,
        )

    # ============================================================
    # LANGUAGES PAGE
    # ============================================================

    @http.route('/languages', type='http', auth='public', website=True)
    def languages(self, **kwargs):
        """Language Courses page"""
        is_en = self._is_english()
        return request.render('alomran_theme.languages_page', {
            'english_landing_url': ENGLISH_LANDING_URL,
            'alomran_page_title': ('Foreign Language Courses in the UAE: French, Spanish, Chinese & More | Al Omran'
                                   if is_en else
                                   'دورات اللغات الأجنبية في الإمارات: فرنسي، إسباني، صيني وأكثر | مركز العمران'),
            'alomran_page_description': (
                'Learn French, Spanish, Italian, Chinese, Turkish, Russian or Korean with professional trainers '
                'at Al Omran Training Center in the UAE.'
                if is_en else
                'تعلّم الفرنسية أو الإسبانية أو الإيطالية أو الصينية أو التركية أو الروسية أو الكورية مع مدربين '
                'محترفين في مركز العمران للتدريب بالإمارات.'),
        })

    @http.route('/languages/register', type='json', auth='public', methods=['POST'], website=True)
    def languages_register(self, **post):
        """Process registration (Languages page)"""
        return self._register_lead(
            post,
            label=('Registration for language course', 'تسجيل في دورة لغة'),
            source=('Languages page', 'صفحة اللغات'),
            require_course=False,
        )

    # ============================================================
    # IT PROGRAMS PAGE
    # ============================================================

    @http.route('/it-programs', type='http', auth='public', website=True)
    def it_programs(self, **kwargs):
        """Information Technology Programs page"""
        return request.render('alomran_theme.it_programs_page', {})

    @http.route('/it-programs/register', type='json', auth='public', methods=['POST'], website=True)
    def it_programs_register(self, **post):
        """Process registration (IT Programs page)"""
        return self._register_lead(
            post,
            label=('Registration for IT program', 'تسجيل في برنامج تقنية المعلومات'),
            source=('IT Programs page', 'صفحة تقنية المعلومات'),
            require_course=False,
        )

    # ============================================================
    # GENERAL COURSE REGISTRATION
    # ============================================================

    @http.route('/course/register', type='json', auth='public', methods=['POST'], website=True)
    def course_register(self, **post):
        """Process registration (Courses page)"""
        return self._register_lead(
            post,
            label=('Course inquiry', 'استفسار عن دورة'),
            source=('Courses page', 'صفحة الدورات'),
            require_course=True,
        )

    # ============================================================
    # ENGLISH & STANDARDIZED TESTS LANDING PAGE (Google Ads)
    # ============================================================

    def _branch_assignment(self, branch):
        """(company_id, user_id) للفرع: الشركة من BRANCH_MAPPING وأول Sales Admin فيها."""
        if not branch or branch not in BRANCH_MAPPING:
            return False, False
        company = request.env['res.company'].sudo().search([('name', '=', BRANCH_MAPPING[branch])], limit=1)
        if not company:
            return False, False
        user_id = False
        sales_admin_group = request.env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
        if sales_admin_group:
            admin_user = request.env['res.users'].sudo().search([
                ('groups_id', 'in', sales_admin_group.id),
                ('company_ids', 'in', company.id),
                ('active', '=', True),
            ], limit=1)
            user_id = admin_user.id or False
        return company.id, user_id

    def _apply_branch_fields(self, lead_values, branch):
        """x_preferred_branch + x_emirate (من اسم الفرع)."""
        self._safe_set_field(lead_values, 'crm.lead', 'x_preferred_branch', branch)
        emirate = _branch_emirate(branch)
        if emirate:
            self._safe_set_field(lead_values, 'crm.lead', 'x_emirate', emirate)

    def _whatsapp_link(self, message, param_key, default_number):
        """رابط wa.me: الرقم من System Parameter إذا شكله صحيح، وإلا الافتراضي."""
        number = (request.env['ir.config_parameter'].sudo().get_param(param_key) or '').strip()
        if not _WA_NUMBER_RE.match(number):
            number = default_number
        return f'https://wa.me/{number}?text={quote(message)}'

    def _english_whatsapp_link(self, message):
        return self._whatsapp_link(message, 'alomran.english_whatsapp', english_content.WHATSAPP_NUMBER)

    def _tutoring_whatsapp_link(self, message):
        return self._whatsapp_link(message, 'alomran.tutoring_whatsapp', tutoring_content.WHATSAPP_NUMBER)

    def _women_whatsapp_link(self, message):
        return self._whatsapp_link(message, 'alomran.women_whatsapp', women_content.WHATSAPP_NUMBER)

    def _english_video_ids(self, param_key, limit):
        """IDs يوتيوب من System Parameters — بس اللي شكلها صحيح."""
        raw = request.env['ir.config_parameter'].sudo().get_param(param_key) or ''
        ids = [v.strip() for v in raw.split(',')]
        return [v for v in ids if _YT_ID_RE.match(v)][:limit]

    def _first_static_file(self, candidates):
        """أول ملف موجود فعلياً من القائمة كرابط /module/static/...، وإلا ''."""
        try:
            from odoo.tools.misc import file_path
        except ImportError:
            return ''
        for rel in candidates:
            try:
                file_path(rel)
                return '/' + rel
            except (FileNotFoundError, ValueError):
                continue
        return ''

    def _english_hero_media(self):
        return self._hero_media('alomran.english_hero', ENGLISH_HERO_VIDEO_FILES, ENGLISH_HERO_POSTER_FILES)

    def _hero_media(self, param_prefix, video_files, poster_files):
        """فيديو الهيرو: System Parameter أولاً (<prefix>_video_url / <prefix>_poster_url)،
        وإلا الملف داخل المويول إذا موجود."""
        icp = request.env['ir.config_parameter'].sudo()
        video = (icp.get_param(f'{param_prefix}_video_url') or '').strip()
        if not _HERO_VIDEO_URL_RE.match(video):
            video = self._first_static_file(video_files)
        if not video:
            return {}
        poster = (icp.get_param(f'{param_prefix}_poster_url') or '').strip()
        if not _HERO_POSTER_URL_RE.match(poster):
            poster = self._first_static_file(poster_files)
        return {
            'url': video,
            'type': 'video/webm' if video.lower().split('?')[0].endswith('.webm') else 'video/mp4',
            'poster': poster,
        }

    def _english_schema(self, content):
        """JSON-LD لقائمة البرامج (Course) مربوطة بالـ EducationalOrganization الموجود."""
        provider = {
            '@type': 'EducationalOrganization',
            '@id': english_content.ORG_ID,
            'name': content['org_name'],
            'sameAs': 'https://alomrantd.com',
        }
        items = []
        for position, prog in enumerate(content['programs']['items'], start=1):
            description = ' '.join(filter(None, [prog['intro'], ', '.join(prog['skills']), prog['note']]))
            items.append({
                '@type': 'ListItem',
                'position': position,
                'item': {
                    '@type': 'Course',
                    'name': prog['headline'],
                    'description': description,
                    'provider': provider,
                },
            })
        data = {
            '@context': 'https://schema.org',
            '@type': 'ItemList',
            'name': content['programs']['title'],
            'itemListElement': items,
        }
        # محتوانا نحن (مش مدخلات زائر)، وبنمنع أي </script> احتياطاً
        raw = json.dumps(data, ensure_ascii=False)
        raw = raw.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        return Markup(raw)

    def _find_or_create_utm(self, model_name, name):
        try:
            mixin = request.env['utm.mixin'].sudo()
            if hasattr(mixin, '_find_or_create_record'):
                return mixin._find_or_create_record(model_name, name).id
            model = request.env[model_name].sudo().with_context(active_test=False)
            record = model.search([('name', '=', name)], limit=1) or model.create({'name': name})
            return record.id
        except Exception as e:
            _logger.warning('UTM %s error: %s', model_name, e)
            return False

    @http.route(ENGLISH_LANDING_URL, type='http', auth='public', website=True, sitemap=True)
    def english_landing(self, program=None, mode=None, **kwargs):
        """صفحة هبوط اللغة الإنجليزية والاختبارات القياسية.
        ?program=ielts و ?mode=online بيختاروا مسبقاً بالفورم (من whitelist بس)."""
        is_en = self._is_english()
        content = english_content.get_content(is_en)

        program = program if program in english_content.PROGRAM_KEYS else ''
        mode = mode if mode in english_content.MODE_KEYS else ''
        hero_program = next((p for p in content['programs']['items'] if p['key'] == program), None)

        program_labels = dict(content['program_options'])
        wa_program_links = {
            key: self._english_whatsapp_link(content['wa_program'].format(program=program_labels[key]))
            for key in english_content.CARD_PROGRAM_KEYS
        }
        hero_videos = self._english_video_ids('alomran.english_hero_video', 1)

        return request.render('alomran_theme.english_landing_page', {
            'c': content,
            'preselect_program': program,
            'preselect_mode': mode,
            'hero_program': hero_program,
            'wa_link': self._english_whatsapp_link(
                content['wa_program'].format(program=program_labels[program])
                if program and program != 'unsure' else content['wa_general']),
            'wa_program_links': wa_program_links,
            'hero_video': hero_videos[0] if hero_videos else '',
            'hero_media': self._english_hero_media(),
            'testimonial_videos': self._english_video_ids('alomran.english_testimonial_videos', 3),
            'testimonials': english_content.TESTIMONIALS,
            'gallery': english_content.GALLERY,
            'more_testimonials_url': english_content.MORE_TESTIMONIALS_URL,
            'phone_number': english_content.PHONE_NUMBER,
            'phone_display': english_content.PHONE_DISPLAY,
            'is_en': is_en,
            'schema_json': self._english_schema(content),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
            # Pixel حملة ChatGPT الخاصة بالإنجليزي بدل Pixel الموقع العام
            'alomran_oai_pixel_override': openai_pixel_id('english'),
        })

    @http.route(f'{ENGLISH_LANDING_URL}/submit', type='json', auth='public', methods=['POST'], website=True)
    def english_landing_submit(self, **post):
        """فورم الاستشارة بصفحة الإنجليزي → crm.lead"""
        is_en = self._is_english()
        ip = _client_ip()

        # Honeypot: نجاح وهمي بدون lead وبدون conversion
        if post.get('website_url'):
            _logger.info('English landing: honeypot triggered (ip=%s)', ip)
            return {'success': True, 'event_id': False}

        name = _clean(post.get('name'), 100)
        phone = _clean(post.get('phone'), 20)
        branch = _clean(post.get('branch'), 100)
        program = _clean(post.get('program'), 30)
        mode = _clean(post.get('mode'), 30)

        if (not name or not phone
                or branch not in BRANCH_MAPPING
                or program not in english_content.PROGRAM_KEYS
                or mode not in english_content.MODE_KEYS):
            return {'success': False, 'error': self._get_error_message('required')}
        if not self._validate_phone(phone):
            return {'success': False, 'error': self._get_error_message('phone_invalid')}
        if _rate_limited(ip):
            _logger.warning('English landing: rate limit hit (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('rate_limited')}

        content = english_content.get_content(is_en)
        labels = content['lead_labels']
        crm_course = english_content.PROGRAM_CRM_NAMES[program]

        try:
            Lead = request.env['crm.lead'].sudo().with_context(active_test=False)

            # طلب مكرر: منرجّع نجاح بس بدون event_id، فما بتنحسب conversion مرتين
            since = datetime.now() - timedelta(hours=ENGLISH_DUPLICATE_HOURS)
            if 'x_source_type' in Lead._fields and Lead.search_count([
                ('phone', '=', phone),
                ('x_source_type', '=', 'landing_english'),
                ('x_course_interest', '=', crm_course),
                ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            ]):
                _logger.info('English landing: duplicate request ignored (ip=%s)', ip)
                return {'success': True, 'event_id': False}

            # UTM: القيم من الرابط إذا نظيفة، وإذا في gclid بلا utm منعتبرها google / cpc
            utm_vals = {}
            for key, model_name, field_name in (
                ('utm_source', 'utm.source', 'source_id'),
                ('utm_medium', 'utm.medium', 'medium_id'),
                ('utm_campaign', 'utm.campaign', 'campaign_id'),
            ):
                value = _clean(post.get(key), 50)
                if value and _UTM_RE.match(value):
                    utm_vals[field_name] = (model_name, value)

            click_ids = {}
            for key in ('gclid', 'gbraid', 'wbraid'):
                value = _clean(post.get(key), 200)
                if value and _CLICK_ID_RE.match(value):
                    click_ids[key] = value
            if click_ids:
                utm_vals.setdefault('source_id', ('utm.source', 'google'))
                utm_vals.setdefault('medium_id', ('utm.medium', 'cpc'))

            program_label = dict(content['program_options'])[program]
            lines = [
                f"{labels['program']}: {program_label}",
                f"{labels['branch']}: {branch}",
                f"{labels['mode']}: {dict(content['mode_options'])[mode]}",
                f"{labels['source']}: {labels['source_value']}",
            ]
            if 'campaign_id' in utm_vals:
                lines.append(f"{labels['campaign']}: {utm_vals['campaign_id'][1]}")
            for key in ('gbraid', 'wbraid'):
                if key in click_ids:
                    lines.append(f"{labels['click_id']} ({key}): {click_ids[key]}")

            lead_values = {
                'name': name,
                'contact_name': name,
                'phone': phone,
                'description': _description(lines, ip),
                'type': 'opportunity',
            }
            for field_name, (model_name, value) in utm_vals.items():
                if field_name in Lead._fields:
                    record_id = self._find_or_create_utm(model_name, value)
                    if record_id:
                        lead_values[field_name] = record_id

            self._safe_set_field(lead_values, 'crm.lead', 'x_source_type', 'landing_english')
            self._safe_set_field(lead_values, 'crm.lead', 'x_course_interest', crm_course)
            self._apply_branch_fields(lead_values, branch)
            # نفس توزيع فورم تواصل معنا: الشركة والـ Sales Admin حسب الفرع
            # user_id دايماً صريح: بدونه Odoo بيعيّن الزائر نفسه (Public user)
            company_id, user_id = self._branch_assignment(branch)
            if company_id:
                lead_values['company_id'] = company_id
            lead_values['user_id'] = user_id or False
            self._safe_set_field(lead_values, 'crm.lead', 'x_training_mode', mode)
            if click_ids.get('gclid'):
                self._safe_set_field(lead_values, 'crm.lead', 'x_gclid', click_ids['gclid'])

            lead = request.env['crm.lead'].sudo().create(lead_values)
            _logger.info('English landing lead created: id=%s program=%s', lead.id, program)
            send_lead_created(lead, pixel='english')
            return {'success': True, 'event_id': lead_event_id(lead)}

        except Exception:
            _logger.exception('English landing error (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('general')}

    # ============================================================
    # PRIVATE TUTORING / SCHOOL FOLLOW-UP / UNIVERSITY SUPPORT LANDING
    # نفس نمط صفحة الإنجليزي: نفس الـ ale- classes ونفس الـ JS
    # ============================================================

    def _json_ld(self, data):
        """JSON-LD آمن داخل <script>: محتوانا نحن، وبنمنع أي </script> احتياطاً."""
        raw = json.dumps(data, ensure_ascii=False)
        raw = raw.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        return Markup(raw)

    def _tutoring_schema(self, content):
        """JSON-LD لقائمة الخدمات (Service) مربوطة بالـ EducationalOrganization الموجود."""
        provider = {
            '@type': 'EducationalOrganization',
            '@id': tutoring_content.ORG_ID,
            'name': content['org_name'],
            'sameAs': 'https://alomrantd.com',
        }
        items = []
        for position, svc in enumerate(content['services']['items'], start=1):
            items.append({
                '@type': 'ListItem',
                'position': position,
                'item': {
                    '@type': 'Service',
                    'name': svc['title'],
                    'description': svc['text'],
                    'serviceType': svc['title'],
                    'areaServed': {'@type': 'Country', 'name': 'United Arab Emirates'},
                    'provider': provider,
                },
            })
        return self._json_ld({
            '@context': 'https://schema.org',
            '@type': 'ItemList',
            'name': content['services']['title'],
            'itemListElement': items,
        })

    def _tutoring_pixel(self):
        """Pixel حملة خاصة إذا انعرّف alomran.openai_tutoring_pixel_id، وإلا Pixel الموقع العام."""
        return 'tutoring' if openai_pixel_id('tutoring') else 'default'

    @http.route(TUTORING_LANDING_URL, type='http', auth='public', website=True, sitemap=True)
    def tutoring_landing(self, service=None, mode=None, **kwargs):
        """صفحة الدروس الخصوصية والمتابعة المدرسية والدعم الأكاديمي الجامعي.
        ?service=school و ?mode=online بيختاروا مسبقاً بالفورم (من whitelist بس)."""
        is_en = self._is_english()
        content = tutoring_content.get_content(is_en)

        service = service if service in tutoring_content.SERVICE_KEYS else ''
        mode = mode if mode in tutoring_content.MODE_KEYS else ''
        hero_service = next((s for s in content['services']['items'] if s['key'] == service), None)

        service_labels = dict(content['service_options'])
        wa_service_links = {
            key: self._tutoring_whatsapp_link(content['wa_service'].format(service=service_labels[key]))
            for key in tutoring_content.CARD_SERVICE_KEYS
        }
        pixel = self._tutoring_pixel()

        return request.render('alomran_theme.tutoring_landing_page', {
            'c': content,
            'preselect_service': service,
            'preselect_mode': mode,
            'hero_service': hero_service,
            'wa_link': self._tutoring_whatsapp_link(
                content['wa_service'].format(service=service_labels[service])
                if service and service != 'unsure' else content['wa_general']),
            'wa_details_link': self._tutoring_whatsapp_link(content['wa_details']),
            'wa_service_links': wa_service_links,
            'hero_media': self._hero_media('alomran.tutoring_hero',
                                           TUTORING_HERO_VIDEO_FILES, TUTORING_HERO_POSTER_FILES),
            # صور الخدمات والفورم: بس الملفات الموجودة فعلياً، وإلا '' (بيطلع البديل)
            'images': {key: self._first_static_file(files)
                       for key, files in tutoring_content.IMAGE_FILES.items()},
            'phone_number': tutoring_content.PHONE_NUMBER,
            'phone_display': tutoring_content.PHONE_DISPLAY,
            'submit_url': f'{TUTORING_LANDING_URL}/submit',
            'is_en': is_en,
            'schema_json': self._tutoring_schema(content),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
            # فاضي = Pixel الموقع العام
            'alomran_oai_pixel_override': openai_pixel_id(pixel) if pixel != 'default' else False,
        })

    @http.route(f'{TUTORING_LANDING_URL}/submit', type='json', auth='public', methods=['POST'], website=True)
    def tutoring_landing_submit(self, **post):
        """فورم الاستشارة بصفحة الدروس الخصوصية → crm.lead"""
        is_en = self._is_english()
        ip = _client_ip()

        # Honeypot: نجاح وهمي بدون lead وبدون conversion
        if post.get('website_url'):
            _logger.info('Tutoring landing: honeypot triggered (ip=%s)', ip)
            return {'success': True, 'event_id': False}

        name = _clean(post.get('name'), 100)
        phone = _clean(post.get('phone'), 20)
        branch = _clean(post.get('branch'), 100)
        service = _clean(post.get('program'), 30)
        stage = _clean(post.get('stage'), 30)
        mode = _clean(post.get('mode'), 30)
        subjects = _clean(post.get('subjects'), 150)

        if (not name or not phone
                or branch not in BRANCH_MAPPING
                or service not in tutoring_content.SERVICE_KEYS
                or stage not in tutoring_content.STAGE_KEYS
                or mode not in tutoring_content.MODE_KEYS):
            return {'success': False, 'error': self._get_error_message('required')}
        if not self._validate_phone(phone):
            return {'success': False, 'error': self._get_error_message('phone_invalid')}
        if _rate_limited(ip):
            _logger.warning('Tutoring landing: rate limit hit (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('rate_limited')}

        content = tutoring_content.get_content(is_en)
        labels = content['lead_labels']
        crm_service = tutoring_content.SERVICE_CRM_NAMES[service]

        try:
            Lead = request.env['crm.lead'].sudo().with_context(active_test=False)

            # طلب مكرر: منرجّع نجاح بس بدون event_id، فما بتنحسب conversion مرتين
            since = datetime.now() - timedelta(hours=TUTORING_DUPLICATE_HOURS)
            if 'x_source_type' in Lead._fields and Lead.search_count([
                ('phone', '=', phone),
                ('x_source_type', '=', 'landing_tutoring'),
                ('x_course_interest', '=', crm_service),
                ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            ]):
                _logger.info('Tutoring landing: duplicate request ignored (ip=%s)', ip)
                return {'success': True, 'event_id': False}

            # UTM: القيم من الرابط إذا نظيفة، وإذا في gclid بلا utm منعتبرها google / cpc
            utm_vals = {}
            for key, model_name, field_name in (
                ('utm_source', 'utm.source', 'source_id'),
                ('utm_medium', 'utm.medium', 'medium_id'),
                ('utm_campaign', 'utm.campaign', 'campaign_id'),
            ):
                value = _clean(post.get(key), 50)
                if value and _UTM_RE.match(value):
                    utm_vals[field_name] = (model_name, value)

            click_ids = {}
            for key in ('gclid', 'gbraid', 'wbraid'):
                value = _clean(post.get(key), 200)
                if value and _CLICK_ID_RE.match(value):
                    click_ids[key] = value
            if click_ids:
                utm_vals.setdefault('source_id', ('utm.source', 'google'))
                utm_vals.setdefault('medium_id', ('utm.medium', 'cpc'))

            lines = [
                f"{labels['service']}: {dict(content['service_options'])[service]}",
                f"{labels['stage']}: {dict(content['stage_options'])[stage]}",
            ]
            if subjects:
                lines.append(f"{labels['subjects']}: {subjects}")
            lines += [
                f"{labels['branch']}: {branch}",
                f"{labels['mode']}: {dict(content['mode_options'])[mode]}",
                f"{labels['source']}: {labels['source_value']}",
            ]
            if 'campaign_id' in utm_vals:
                lines.append(f"{labels['campaign']}: {utm_vals['campaign_id'][1]}")
            for key in ('gbraid', 'wbraid'):
                if key in click_ids:
                    lines.append(f"{labels['click_id']} ({key}): {click_ids[key]}")

            lead_values = {
                'name': name,
                'contact_name': name,
                'phone': phone,
                'description': _description(lines, ip),
                'type': 'opportunity',
            }
            for field_name, (model_name, value) in utm_vals.items():
                if field_name in Lead._fields:
                    record_id = self._find_or_create_utm(model_name, value)
                    if record_id:
                        lead_values[field_name] = record_id

            self._safe_set_field(lead_values, 'crm.lead', 'x_source_type', 'landing_tutoring')
            self._safe_set_field(lead_values, 'crm.lead', 'x_course_interest', crm_service)
            self._safe_set_field(lead_values, 'crm.lead', 'x_study_stage', stage)
            if subjects:
                self._safe_set_field(lead_values, 'crm.lead', 'x_subjects', subjects)
            self._apply_branch_fields(lead_values, branch)
            # نفس توزيع فورم تواصل معنا: الشركة والـ Sales Admin حسب الفرع
            # user_id دايماً صريح: بدونه Odoo بيعيّن الزائر نفسه (Public user)
            company_id, user_id = self._branch_assignment(branch)
            if company_id:
                lead_values['company_id'] = company_id
            lead_values['user_id'] = user_id or False
            self._safe_set_field(lead_values, 'crm.lead', 'x_training_mode', mode)
            if click_ids.get('gclid'):
                self._safe_set_field(lead_values, 'crm.lead', 'x_gclid', click_ids['gclid'])

            lead = request.env['crm.lead'].sudo().create(lead_values)
            _logger.info('Tutoring landing lead created: id=%s service=%s', lead.id, service)
            send_lead_created(lead, pixel=self._tutoring_pixel())
            return {'success': True, 'event_id': lead_event_id(lead)}

        except Exception:
            _logger.exception('Tutoring landing error (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('general')}

    # ============================================================
    # WOMEN'S PROFESSIONAL & CREATIVE COURSES LANDING
    # نفس نمط صفحة الدروس الخصوصية: نفس الـ ale-/alt- classes ونفس الـ JS
    # ============================================================

    def _landing_tracking(self, post):
        """UTM + معرفات النقر من الفورم (بس القيم النظيفة).
        إذا في gclid/gbraid/wbraid بلا utm منعتبرها google / cpc."""
        utm_vals = {}
        for key, model_name, field_name in (
            ('utm_source', 'utm.source', 'source_id'),
            ('utm_medium', 'utm.medium', 'medium_id'),
            ('utm_campaign', 'utm.campaign', 'campaign_id'),
        ):
            value = _clean(post.get(key), 50)
            if value and _UTM_RE.match(value):
                utm_vals[field_name] = (model_name, value)
        click_ids = {}
        for key in ('gclid', 'gbraid', 'wbraid'):
            value = _clean(post.get(key), 200)
            if value and _CLICK_ID_RE.match(value):
                click_ids[key] = value
        if click_ids:
            utm_vals.setdefault('source_id', ('utm.source', 'google'))
            utm_vals.setdefault('medium_id', ('utm.medium', 'cpc'))
        return utm_vals, click_ids

    def _women_schema(self, content):
        """JSON-LD لقائمة الدورات (Course) مربوطة بالـ EducationalOrganization الموجود."""
        provider = {
            '@type': 'EducationalOrganization',
            '@id': women_content.ORG_ID,
            'name': content['org_name'],
            'sameAs': 'https://alomrantd.com',
        }
        items = []
        for position, course in enumerate(content['courses']['items'], start=1):
            items.append({
                '@type': 'ListItem',
                'position': position,
                'item': {
                    '@type': 'Course',
                    'name': course['title'],
                    'description': ' '.join([course['lead'], ', '.join(course['points'])]),
                    'provider': provider,
                },
            })
        return self._json_ld({
            '@context': 'https://schema.org',
            '@type': 'ItemList',
            'name': content['courses']['title'],
            'itemListElement': items,
        })

    def _women_pixel(self):
        """Pixel حملة خاصة إذا انعرّف alomran.openai_women_pixel_id، وإلا Pixel الموقع العام."""
        return 'women' if openai_pixel_id('women') else 'default'

    @http.route(WOMEN_LANDING_URL, type='http', auth='public', website=True, sitemap=True)
    def women_landing(self, course=None, mode=None, **kwargs):
        """صفحة الدورات المهنية والإبداعية للسيدات.
        ?course=makeup و ?mode=online بيختاروا مسبقاً بالفورم (من whitelist بس)."""
        is_en = self._is_english()
        content = women_content.get_content(is_en)

        course = course if course in women_content.COURSE_KEYS else ''
        mode = mode if mode in women_content.MODE_KEYS else ''
        hero_course = next((c for c in content['courses']['items'] if c['key'] == course), None)

        course_labels = dict(content['course_options'])
        wa_course_links = {
            key: self._women_whatsapp_link(content['wa_course'].format(course=course_labels[key]))
            for key in women_content.CARD_COURSE_KEYS
        }
        pixel = self._women_pixel()

        # آراء الطالبات (من ملف المحتوى) — الصورة بس من static الموديول
        testimonials = []
        for item in women_content.TESTIMONIALS:
            photo = item.get('photo') or ''
            testimonials.append({
                'name': (item.get('name_en') if is_en else None) or item.get('name', ''),
                'text': (item.get('text_en') if is_en else item.get('text_ar')) or '',
                'course': course_labels.get(item.get('course'), ''),
                'photo': photo if photo.startswith('/alomran_theme/static/') else '',
            })

        return request.render('alomran_theme.women_landing_page', {
            'c': content,
            'preselect_course': course,
            'preselect_mode': mode,
            'hero_course': hero_course,
            'wa_link': self._women_whatsapp_link(
                content['wa_course'].format(course=course_labels[course])
                if course and course != 'unsure' else content['wa_general']),
            'wa_details_link': self._women_whatsapp_link(content['wa_details']),
            'wa_course_links': wa_course_links,
            'testimonials': testimonials,
            'hero_media': self._hero_media('alomran.women_hero',
                                           WOMEN_HERO_VIDEO_FILES, WOMEN_HERO_POSTER_FILES),
            # الصور: أول ملف موجود (صورة حقيقية webp/jpg، وإلا رسمة SVG الجاهزة)
            'images': {key: self._first_static_file(files)
                       for key, files in women_content.IMAGE_FILES.items()},
            'phone_number': women_content.PHONE_NUMBER,
            'phone_display': women_content.PHONE_DISPLAY,
            'submit_url': f'{WOMEN_LANDING_URL}/submit',
            'is_en': is_en,
            'schema_json': self._women_schema(content),
            'alomran_page_title': content['page_title'],
            'alomran_page_description': content['page_description'],
            # فاضي = Pixel الموقع العام
            'alomran_oai_pixel_override': openai_pixel_id(pixel) if pixel != 'default' else False,
        })

    @http.route(f'{WOMEN_LANDING_URL}/submit', type='json', auth='public', methods=['POST'], website=True)
    def women_landing_submit(self, **post):
        """فورم صفحة دورات السيدات → crm.lead"""
        is_en = self._is_english()
        ip = _client_ip()

        # Honeypot: نجاح وهمي بدون lead وبدون conversion
        if post.get('website_url'):
            _logger.info('Women landing: honeypot triggered (ip=%s)', ip)
            return {'success': True, 'event_id': False}

        name = _clean(post.get('name'), 100)
        phone = _clean(post.get('phone'), 20)
        branch = _clean(post.get('branch'), 100)
        course = _clean(post.get('program'), 30)
        mode = _clean(post.get('mode'), 30)
        notes = _clean(post.get('notes'), 500, multiline=True)

        if (not name or not phone
                or branch not in BRANCH_MAPPING
                or course not in women_content.COURSE_KEYS
                or mode not in women_content.MODE_KEYS):
            return {'success': False, 'error': self._get_error_message('required')}
        if not self._validate_phone(phone):
            return {'success': False, 'error': self._get_error_message('phone_invalid')}
        if _rate_limited(ip):
            _logger.warning('Women landing: rate limit hit (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('rate_limited')}

        content = women_content.get_content(is_en)
        labels = content['lead_labels']
        crm_course = women_content.COURSE_CRM_NAMES[course]

        try:
            Lead = request.env['crm.lead'].sudo().with_context(active_test=False)

            # طلب مكرر: منرجّع نجاح بس بدون event_id، فما بتنحسب conversion مرتين
            since = datetime.now() - timedelta(hours=WOMEN_DUPLICATE_HOURS)
            if 'x_source_type' in Lead._fields and Lead.search_count([
                ('phone', '=', phone),
                ('x_source_type', '=', 'landing_women'),
                ('x_course_interest', '=', crm_course),
                ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            ]):
                _logger.info('Women landing: duplicate request ignored (ip=%s)', ip)
                return {'success': True, 'event_id': False}

            utm_vals, click_ids = self._landing_tracking(post)

            lines = [
                f"{labels['course']}: {dict(content['course_options'])[course]}",
                f"{labels['branch']}: {branch}",
                f"{labels['mode']}: {dict(content['mode_options'])[mode]}",
            ]
            if notes:
                lines.append(f"{labels['notes']}: {notes}")
            lines.append(f"{labels['source']}: {labels['source_value']}")
            if 'campaign_id' in utm_vals:
                lines.append(f"{labels['campaign']}: {utm_vals['campaign_id'][1]}")
            for key in ('gbraid', 'wbraid'):
                if key in click_ids:
                    lines.append(f"{labels['click_id']} ({key}): {click_ids[key]}")

            lead_values = {
                'name': name,
                'contact_name': name,
                'phone': phone,
                'description': _description(lines, ip),
                'type': 'opportunity',
            }
            for field_name, (model_name, value) in utm_vals.items():
                if field_name in Lead._fields:
                    record_id = self._find_or_create_utm(model_name, value)
                    if record_id:
                        lead_values[field_name] = record_id

            self._safe_set_field(lead_values, 'crm.lead', 'x_source_type', 'landing_women')
            self._safe_set_field(lead_values, 'crm.lead', 'x_course_interest', crm_course)
            self._apply_branch_fields(lead_values, branch)
            # نفس توزيع فورم تواصل معنا: الشركة والـ Sales Admin حسب الفرع
            # user_id دايماً صريح: بدونه Odoo بيعيّن الزائر نفسه (Public user)
            company_id, user_id = self._branch_assignment(branch)
            if company_id:
                lead_values['company_id'] = company_id
            lead_values['user_id'] = user_id or False
            self._safe_set_field(lead_values, 'crm.lead', 'x_training_mode', mode)
            if click_ids.get('gclid'):
                self._safe_set_field(lead_values, 'crm.lead', 'x_gclid', click_ids['gclid'])

            lead = request.env['crm.lead'].sudo().create(lead_values)
            _logger.info('Women landing lead created: id=%s course=%s', lead.id, course)
            send_lead_created(lead, pixel=self._women_pixel())
            return {'success': True, 'event_id': lead_event_id(lead)}

        except Exception:
            _logger.exception('Women landing error (ip=%s)', ip)
            return {'success': False, 'error': self._get_error_message('general')}