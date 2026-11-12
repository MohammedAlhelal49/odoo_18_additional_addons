# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from .openai_ads import send_lead_created, lead_event_id, pixel_head_snippet, pixel_lead_script
from odoo.tools import plaintext2html
from odoo.tools.misc import hmac as odoo_hmac
from datetime import datetime, timedelta
import ipaddress
from urllib.parse import quote
import hmac as py_hmac
import time
import re
import json
import logging

_logger = logging.getLogger(__name__)

BRANCH_COMPANY_MAPPING = {
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

# ============================================================
# HELPERS
# ============================================================

PAGE_PATH = '/homat-alwatan'
GA4_ID = 'G-9DGH1G5YEY'   # نفس خاصية GA4 تبع الموقع الرئيسي
TAG_NAME = 'مبادرة حماة الوطن'

# حماية من السبام
FORM_TOKEN_SCOPE = 'alomran-homat-alwatan-form'
FORM_MIN_SECONDS = 3            # أي إرسال أسرع من هيك = بوت
FORM_MAX_AGE = 24 * 3600        # التوكن صالح 24 ساعة
# حد لكل IP عام. كان 5 — قليل كتير: شبكات الموبايل بالإمارات (اتصالات/du) بتشارك نفس الـ IP
# بين كتير مستخدمين (CGNAT)، فكان عم يمنع ناس حقيقيين يسجلوا. التكرار لنفس الشخص
# (نفس الهاتف أو الهوية خلال 24 ساعة) بيوقفه _is_duplicate.
RATE_LIMIT_COUNT = 30           # أقصى عدد طلبات من نفس الـ IP العام
RATE_LIMIT_WINDOW_MIN = 60      # خلال هالمدة (دقائق)

MESSAGES = {
    'ar': {
        'required': 'يرجى ملء جميع الحقول المطلوبة',
        'eid': 'رقم الهوية الإماراتية غير صحيح — يجب أن يبدأ بـ 784 ويتكون من 15 رقم',
        'phone': 'رقم الهاتف غير صحيح — يرجى إدخال رقم إماراتي صحيح',
        'email': 'البريد الإلكتروني غير صحيح',
        'branch': 'يرجى اختيار فرع صحيح',
        'duplicate': 'لقد قدمت طلباً مسبقاً في المبادرة خلال الـ 24 ساعة الماضية',
        'expired': 'انتهت صلاحية الصفحة، يرجى تحديث الصفحة والمحاولة مرة أخرى',
        'rate_limited': 'تم تجاوز عدد المحاولات المسموح، يرجى المحاولة لاحقاً',
        'generic': 'حدث خطأ، يرجى المحاولة مرة أخرى',
    },
    'en': {
        'required': 'Please fill in all required fields',
        'eid': 'Invalid Emirates ID — it must start with 784 and contain 15 digits',
        'phone': 'Invalid phone number — please enter a valid UAE number',
        'email': 'Invalid email address',
        'branch': 'Please select a valid branch',
        'duplicate': 'You have already applied to the initiative within the last 24 hours',
        'expired': 'This page has expired, please refresh and try again',
        'rate_limited': 'Too many attempts, please try again later',
        'generic': 'Something went wrong, please try again',
    },
}

_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_UTM_RE = re.compile(r'^[\w.\-]{1,50}$')

# ============================================================
# HELPERS
# ============================================================

def _sanitize(value, max_len=500, multiline=False):
    """تنظيف للتخزين: إزالة محارف التحكم والقص.
    ما منعمل HTML escape هون، لأن Odoo بيعمل escape وقت العرض، والوصف
    بيتحول لـ HTML آمن عن طريق plaintext2html. الـ escape المسبق كان
    بيخزن &lt; و &quot; كنص حرفي بالحقول."""
    if not value:
        return ''
    value = _CTRL_RE.sub('', str(value))
    if not multiline:
        value = ' '.join(value.split())
    return value.strip()[:max_len]

def _is_ar():
    lang = request.env.lang or ''
    return lang.startswith('ar')

def _client_ip():
    # مع proxy_mode = True بـ odoo.conf بتكون remote_addr هي IP الزائر الحقيقي
    return request.httprequest.remote_addr or ''

def _make_form_token():
    ts = str(int(time.time()))
    sig = odoo_hmac(request.env(su=True), FORM_TOKEN_SCOPE, ts)
    return f'{ts}.{sig}'

def _check_form_token(token):
    try:
        ts, sig = (token or '').split('.', 1)
        ts_int = int(ts)
    except ValueError:
        return 'invalid'
    expected = odoo_hmac(request.env(su=True), FORM_TOKEN_SCOPE, ts)
    if not py_hmac.compare_digest(sig, expected):
        return 'invalid'
    age = time.time() - ts_int
    if age < FORM_MIN_SECONDS:
        return 'too_fast'
    if age > FORM_MAX_AGE:
        return 'expired'
    return 'ok'

def _public_ip(ip):
    """True إذا الـ IP عام فعلاً. IP داخلي/محلي معناه إن Odoo ورا proxy بدون proxy_mode،
    فكل الزوار بيطلعوا بنفس الـ IP — وقتها ما منحسب عليه (كان بيسكّر الفورم عالكل)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)

def _rate_limited(ip):
    if not ip:
        return False
    if not _public_ip(ip):
        _logger.warning('Homat rate limit: non-public client IP %s — check proxy_mode in odoo.conf; '
                        'IP limit skipped', ip)
        return False
    try:
        since = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MIN)
        count = request.env['crm.lead'].sudo().with_context(active_test=False).search_count([
            ('tag_ids.name', '=', TAG_NAME),
            ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            # مطابقة دقيقة: "IP: 1.2.3.4" ما بتطابق "IP: 1.2.3.45" (بعد الـ IP دايماً <br> أو </p>)
            ('description', 'ilike', f'IP: {ip}<'),
        ])
        return count >= RATE_LIMIT_COUNT
    except Exception as e:
        _logger.warning('Homat rate-limit check error: %s', e)
        return False

def _secure_headers(response):
    # الصفحة فيها توكنات خاصة بالجلسة، فما لازم تنكاش بكاش عام (CDN/proxy)
    response.headers['Cache-Control'] = 'private, no-cache, max-age=0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def _json_response(payload, status=200):
    response = Response(json.dumps(payload), status=status, content_type='application/json')
    return _secure_headers(response)

def _head_extra(lang):
    # تتبّع GA4 فقط (بدون تعديلات SEO)
    return f'''
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA4_ID}');
    </script>''' + pixel_head_snippet()

def _success_event(lang, event_id=None):
    # GA4 + ChatGPT Ads (lead_created بنفس event_id تبع السيرفر)
    return pixel_lead_script(event_id) + (
        "<script>if (window.gtag) { gtag('event', 'generate_lead', "
        f"{{form_name: 'homat_alwatan', language: '{lang}'}}); }}</script>"
    )

def _validate_emirates_id(eid):
    cleaned = re.sub(r'[-\s]', '', eid)
    return bool(re.match(r'^784\d{12}$', cleaned)), cleaned

def _validate_phone(phone):
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if cleaned.startswith('+971'):
        cleaned = '0' + cleaned[4:]
    elif cleaned.startswith('971'):
        cleaned = '0' + cleaned[3:]
    return bool(re.match(r'^0[0-9]{9}$', cleaned)), cleaned

def _validate_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

def _is_duplicate(phone, emirates_id):
    try:
        yesterday = datetime.now() - timedelta(hours=24)
        domain = [
            ('tag_ids.name', '=', TAG_NAME),
            ('create_date', '>=', yesterday.strftime('%Y-%m-%d %H:%M:%S')),
            '|',
            ('phone', '=', phone),
            ('description', 'ilike', emirates_id),
        ]
        return request.env['crm.lead'].sudo().search_count(domain) > 0
    except Exception as e:
        _logger.warning('Homat duplicate check error: %s', e)
        return False

def _get_utm_source(source_name):
    try:
        utm = request.env['utm.source'].sudo().search(
            [('name', '=', source_name)], limit=1)
        if not utm:
            utm = request.env['utm.source'].sudo().create({'name': source_name})
        return utm.id
    except Exception:
        return False


class HomatAlWatanController(http.Controller):

    def _get_company_and_salesperson(self, branch):
        company_id = False
        salesperson_id = False
        company_name = BRANCH_COMPANY_MAPPING.get(branch)
        if not company_name:
            return company_id, salesperson_id
        company = request.env['res.company'].sudo().search(
            [('name', '=', company_name)], limit=1)
        if not company:
            return company_id, salesperson_id
        company_id = company.id
        sales_admin_group = request.env.ref(
            'sales_team.group_sale_manager', raise_if_not_found=False)
        if sales_admin_group:
            admin_user = request.env['res.users'].sudo().search([
                ('groups_id', 'in', sales_admin_group.id),
                ('company_ids', 'in', company_id),
                ('active', '=', True),
            ], limit=1)
            if admin_user:
                salesperson_id = admin_user.id
        return company_id, salesperson_id

    def _render_page(self, success=False, error='', event_id=None):
        try:
            csrf = request.csrf_token()
        except Exception:
            csrf = ''
        form_token = _make_form_token()
        head_extra = _head_extra('ar')
        success_event = _success_event('ar', event_id) if success else ''

        error_html = ''
        if error:
            error_html = (
                f'<div style="background:#ffebee;color:#c62828;padding:1rem 2rem;'
                f'text-align:center;border-radius:8px;margin-bottom:1rem;">⚠️ {error}</div>'
            )

        success_html = ''
        if success:
            success_html = '''
            <div class="success-state">
                <div class="success-state__icon">
                    <svg viewBox="0 0 48 48" fill="none">
                        <circle cx="24" cy="24" r="23" stroke="#406AB3" stroke-width="2"/>
                        <path d="M14 24l7 7 13-13" stroke="#406AB3" stroke-width="2.5"
                              stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <h3 class="success-state__title">بعد إرسال الطلب</h3>
                <p class="success-state__text">شكراً لاهتمامك بمبادرة حماة الوطن.</p>
                <p class="success-state__text">سيقوم فريق مركز العمران بمراجعة الطلبات وفق شروط المبادرة وآلية الاختيار المعتمدة.</p>
                <p class="success-state__text">في حال استيفاء الشروط وترشيحك للاستفادة، سيتواصل معك فريق المبادرة لاستكمال إجراءات القبول والتسجيل.</p>
                <p class="success-state__text success-state__text--note">
                    يرجى العلم أن تعبئة نموذج التقديم لا تعني القبول النهائي في المبادرة، وأن عدد المقاعد محدود.
                </p>
            </div>'''

        form_html = '' if success else f'''
        {error_html}
        <form class="application-form__form" action="/homat-alwatan/apply" method="post">
            <input type="hidden" name="csrf_token" value="{csrf}">
            <input type="hidden" name="_lang" value="ar">
            <input type="hidden" name="_ft" value="{form_token}">
            <input type="text" name="_trap" value="" style="display:none!important" tabindex="-1" autocomplete="off">
            <div class="form-grid">
                <div class="form-field">
                    <label class="form-field__label">الاسم الكامل <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="fullName" class="form-field__input" required maxlength="100" autocomplete="name">
                </div>
                <div class="form-field">
                    <label class="form-field__label">رقم الهوية الإماراتية <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="emiratesId" class="form-field__input" required
                           inputmode="numeric" placeholder="784-XXXX-XXXXXXX-X" maxlength="20">
                </div>
                <div class="form-field">
                    <label class="form-field__label">رقم الهاتف <span style="color:#e53e3e">*</span></label>
                    <input type="tel" name="phone" class="form-field__input" required
                           dir="ltr" placeholder="05X XXX XXXX" maxlength="15" autocomplete="tel">
                </div>
                <div class="form-field">
                    <label class="form-field__label">البريد الإلكتروني <span style="color:#e53e3e">*</span></label>
                    <input type="email" name="email" class="form-field__input" required
                           dir="ltr" maxlength="150" autocomplete="email">
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">الفرع المفضل لحضور البرامج <span style="color:#e53e3e">*</span></label>
                    <select name="branch" class="form-field__select" required>
                        <option value="" disabled selected>اختر الفرع</option>
                        <optgroup label="العين">
                            <option value="وسط المدينة - العين">وسط المدينة</option>
                            <option value="اليحر مول - العين">اليحر مول</option>
                            <option value="مكاني مول زاخر - العين">مكاني مول زاخر</option>
                            <option value="البراري مول - العين">البراري مول</option>
                            <option value="الفوعة مول - العين">الفوعة مول</option>
                        </optgroup>
                        <optgroup label="أبوظبي">
                            <option value="مزيد مول - ابوظبي">مزيد مول</option>
                            <option value="شارع المرور - ابوظبي">شارع المرور</option>
                        </optgroup>
                        <optgroup label="دبي">
                            <option value="القرهود - دبي">القرهود</option>
                            <option value="البرشا - دبي">البرشا</option>
                        </optgroup>
                        <optgroup label="الشارقة">
                            <option value="سنترال مول - الشارقة">سنترال مول</option>
                        </optgroup>
                        <optgroup label="رأس الخيمة">
                            <option value="راك مول - راس الخيمة">راك مول</option>
                        </optgroup>
                        <optgroup label="الفجيرة">
                            <option value="برج العوضي - الفجيرة">برج العوضي</option>
                        </optgroup>
                    </select>
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">لماذا ترغب في المشاركة في مبادرة حماة الوطن؟ <span style="color:#e53e3e">*</span></label>
                    <textarea name="reason" class="form-field__textarea" rows="4" required maxlength="1000"></textarea>
                </div>
                <div class="form-field">
                    <label class="form-field__label">هل يمكنك الالتزام بحضور البرامج التدريبية وفق الجدول المعلن؟</label>
                    <div class="form-field__radio-group">
                        <label class="form-field__radio">
                            <input type="radio" name="timeCommitment" value="yes" required>
                            <span class="form-field__radio-mark"></span><span>نعم / Yes</span>
                        </label>
                        <label class="form-field__radio">
                            <input type="radio" name="timeCommitment" value="no">
                            <span class="form-field__radio-mark"></span><span>لا / No</span>
                        </label>
                    </div>
                </div>
                <div class="form-field">
                    <label class="form-field__label">هل أنت مستعد للالتزام بالحضور والمشاركة طوال فترة البرنامج؟</label>
                    <div class="form-field__radio-group">
                        <label class="form-field__radio">
                            <input type="radio" name="fullProgram" value="yes" required>
                            <span class="form-field__radio-mark"></span><span>نعم / Yes</span>
                        </label>
                        <label class="form-field__radio">
                            <input type="radio" name="fullProgram" value="no">
                            <span class="form-field__radio-mark"></span><span>لا / No</span>
                        </label>
                    </div>
                </div>
            </div>
            <fieldset class="form-confirmations">
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm1" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>أقر بأنني من أبناء الإمارات، وأن البيانات التي قدمتها صحيحة.</span>
                    </label>
                </div>
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm2" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>أوافق على شروط وأحكام المبادرة وآلية اختيار المشاركين.</span>
                    </label>
                </div>
            </fieldset>
            <div class="form-actions">
                <button type="submit" class="btn btn--primary btn--lg btn--full">
                    إرسال طلب المشاركة
                </button>
            </div>
        </form>'''

        html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مبادرة حماة الوطن | مركز العمران للتدريب والتطوير</title>
    <meta name="description" content="مبادرة وطنية مجتمعية من مركز العمران للتدريب والتطوير لتكريم أبناء الإمارات الذين يخدمون الوطن ودعمهم ببرامج تدريب وتطوير مجانية.">
    <meta property="og:title" content="مبادرة حماة الوطن | مركز العمران للتدريب والتطوير">
    <meta property="og:description" content="مبادرة وطنية مجتمعية بقيمة 1,000,000 درهم لتكريم أبناء الإمارات الذين يخدمون الوطن.">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ar_AE">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Alexandria:wght@300;400;500;600;700;800&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="/alomran_homat_alwatan/static/src/img/favicon.png">
    <link rel="stylesheet" href="/alomran_homat_alwatan/static/src/css/homat.css">
{head_extra}
</head>
<body>

<header class="site-header">
    <div class="container">
        <a href="#hero" class="logo" aria-label="مركز العمران للتدريب والتطوير">
            <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png"
                 alt="شعار مركز العمران للتدريب والتطوير" width="240" height="60">
        </a>
        <nav class="main-nav" aria-label="التنقل الرئيسي">
            <ul class="nav-list">
                <li><a href="#provide" class="nav-link">ماذا نقدم</a></li>
                <li><a href="#why" class="nav-link">لماذا المبادرة</a></li>
                <li><a href="#requirements" class="nav-link">الشروط</a></li>
                <li><a href="#locations" class="nav-link">الفروع</a></li>
                <li><a href="#apply" class="nav-link nav-cta">قدم طلبك الآن</a></li>
                <li><a href="/website/lang/en?r=/homat-alwatan" class="lang-switch" style="background:#60BB46;border:2px solid #60BB46;color:#fff;font-weight:700;border-radius:6px;padding:5px 12px;">EN</a></li>
                <li><a href="/ar" class="nav-link" style="display:flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,0.4);border-radius:50px;padding:6px 14px;font-size:0.85rem;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    الموقع الرئيسي
                </a></li>
            </ul>
        </nav>
        <button class="mobile-menu-toggle" aria-label="فتح القائمة" aria-expanded="false">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
        </button>
    </div>
</header>

<main>

    <!-- HERO -->
    <section class="hero" id="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <div class="container">
            <div class="hero-content">
                <div class="hero-badge">
                    <svg class="icon" width="20" height="20" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    <span>تفانٍ في خدمة الوطن وانتماء يستحق التقدير</span>
                </div>
                <h1 class="hero-title">مبادرة حماة الوطن</h1>
                <p class="hero-subtitle">تكريم التفاني والانتماء في خدمة الوطن الغالي</p>
                <div class="hero-copy">
                    <p>بكل فخر واعتزاز، يطلق مركز العمران للتدريب والتطوير مبادرة حماة الوطن، وهي مبادرة وطنية مجتمعية بقيمة 1,000,000 درهم، لتكريم أبناء الإمارات الذين يكرسون وقتهم وعطاءهم في خدمة الوطن، وتقديم برامج تدريبية مجانية تطور من قدراتهم وترفع من مستوى عطائهم.</p>
                    <p class="hero-statement">لأن خدمة الوطن مسؤولية نعتز بها جميعاً، ولأن عطاء أبناء الإمارات يستحق أن يجد من يدعمه.</p>
                </div>
                <div class="hero-actions">
                    <a href="#apply" class="btn btn-primary">قدم طلبك الآن</a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-image-frame">
                    <img src="/alomran_homat_alwatan/static/src/img/homat-hero.jpg"
                         alt="أبناء الإمارات في خدمة الوطن" loading="eager" width="800" height="600">
                </div>
                <div class="hero-image-badge">
                    <span class="badge-number">1,000</span>
                    <span class="badge-text">فرصة وطنية</span>
                </div>
            </div>
        </div>
    </section>

    <!-- VIDEO -->
    <section class="video-section">
        <div class="container">
            <div class="video-wrapper">
                <video autoplay muted loop playsinline id="heroVideo" width="1280" height="720">
                    <source src="/alomran_homat_alwatan/static/src/img/homat-video.mp4" type="video/mp4">
                    المتصفح لا يدعم تشغيل الفيديو.
                </video>
                <button class="video-sound-btn" id="soundToggle" aria-label="تشغيل/إيقاف الصوت">
                    <svg class="icon-sound-on" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                    <svg class="icon-sound-off" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2" style="display:none">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <line x1="23" y1="9" x2="17" y2="15"/>
                        <line x1="17" y1="9" x2="23" y2="15"/>
                    </svg>
                </button>
            </div>
        </div>
    </section>

    <!-- STATISTICS -->
    <section class="statistics" id="statistics">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>
                    <div class="stat-number">1,000,000</div>
                    <div class="stat-label">درهم قيمة المبادرة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
                    <div class="stat-number">1,000</div>
                    <div class="stat-label">فرصة تدريبية</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
                    <div class="stat-number">12 شهراً</div>
                    <div class="stat-label">من التدريب والتطوير</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <div class="stat-number">بدون رسوم</div>
                    <div class="stat-label">برامج تدريب متكاملة</div>
                </div>
            </div>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="features" id="provide">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">ماذا نقدم؟</h2>
                <p class="section-subtitle">برامج تدريب وتطوير مجانية لخدمة الوطن بكفاءة</p>
                <p class="section-intro">من خلال المبادرة سيحصل كل مشارك يتم قبوله على:</p>
            </div>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div>
                    <h3 class="feature-title">برامج تدريبية متكاملة</h3>
                    <p class="feature-text">برامج تدريبية نوعية في القيادة والتطوير المهني تعزز من قدرات المشاركين.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
                    <h3 class="feature-title">مهارات قيادية</h3>
                    <p class="feature-text">بناء مهارات القيادة والعمل الجماعي التي تمكن المشاركين من أداء رسالتهم بكفاءة.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div>
                    <h3 class="feature-title">تدريب حضوري ميداني</h3>
                    <p class="feature-text">تدريب حضوري في أحد فروع مركز العمران للتدريب والتطوير في مختلف إمارات الدولة.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <h3 class="feature-title">بدون رسوم</h3>
                    <p class="feature-text">تتحمل المبادرة كامل تكلفة البرامج التدريبية للمشاركين المقبولين.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- WHY -->
    <section class="why" id="why">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">لماذا أطلقنا مبادرة حماة الوطن؟</h2>
            </div>
            <div class="why-content">
                <div class="why-text">
                    <p>نؤمن في مركز العمران أن الاستثمار الحقيقي هو الاستثمار في الإنسان، وأن خدمة الوطن من أسمى القيم.</p>
                    <p>وأبناء الإمارات كانوا ولا يزالون درع الوطن وصنّاع مستقبله، وقدموا أصدق الأمثلة في التفاني والعطاء.</p>
                    <p>لذلك أطلقنا مبادرة حماة الوطن لنكرم من يخدمون الوطن ونمنحهم فرصة لتطوير مهاراتهم وقدراتهم.</p>
                </div>
                <div class="why-stats">
                    <div class="why-stat"><div class="why-stat-number">1,000,000 درهم</div><div class="why-stat-label">في التدريب والتطوير</div></div>
                    <div class="why-stat"><div class="why-stat-number">1,000 فرصة</div><div class="why-stat-label">وطنية حقيقية</div></div>
                    <div class="why-stat"><div class="why-stat-number">7 إمارات</div><div class="why-stat-label">نصل إليها معاً</div></div>
                </div>
            </div>
        </div>
    </section>

    <!-- REQUIREMENTS -->
    <section class="requirements" id="requirements">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">من يمكنه التقديم؟</h2>
                <p class="section-intro">المبادرة مخصصة لأبناء الإمارات الذين تنطبق عليهم الشروط التالية:</p>
            </div>
            <div class="requirements-list">
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن يكون المتقدم من أبناء الإمارات أصحاب الجنسية الإماراتية.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن يكون ملتزماً بإحدى مبادرات خدمة الوطن أو متطوعاً في جهة وطنية معتمدة.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن يكون قادراً على حضور البرامج التدريبية وفق الجدول المعلن.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن يكون جاداً وقادراً على الالتزام بالحضور والمشاركة طوال فترة البرنامج.</p></div>
            </div>
            <div class="requirements-cta">
                <p>إذا كنت مستعداً لاستثمار وقتك في خدمة الوطن وتطوير قدراتك، فهذه الفرصة لك.</p>
                <a href="#apply" class="btn btn-primary">أريد التقديم على المبادرة</a>
            </div>
        </div>
    </section>

    <!-- SELECTION -->
    <section class="selection" id="selection">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">كيف يتم اختيار المشاركين؟</h2>
                <p class="section-intro">حرصاً على تحقيق أكبر أثر ممكن، لن يتم قبول جميع الطلبات تلقائياً.</p>
            </div>
            <div class="process-timeline">
                <div class="process-step"><div class="step-number">01</div><div class="step-content"><h3>مطابقة شروط المبادرة</h3><p>التأكد من استيفاء المتقدم لجميع الشروط المطلوبة.</p></div></div>
                <div class="process-step"><div class="step-number">02</div><div class="step-content"><h3>أولوية التقديم</h3><p>تُؤخذ أولوية التقديم بعين الاعتبار ضمن آلية اختيار المشاركين.</p></div></div>
                <div class="process-step"><div class="step-number">03</div><div class="step-content"><h3>ترشيحات الجهات الوطنية</h3><p>سيتم استكمال العدد المستهدف من خلال ترشيحات الجهات والمؤسسات الوطنية في مختلف إمارات الدولة.</p></div></div>
            </div>
            <div class="process-highlight">
                <p>الهدف النهائي: الوصول إلى 1,000 مشارك عبر إمارات الدولة ومنحهم فرصة حقيقية لتطوير قدراتهم ومهاراتهم.</p>
            </div>
        </div>
    </section>

    <!-- LOCATIONS -->
    <section class="locations" id="locations">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">أين ستكون البرامج التدريبية؟</h2>
                <p class="section-intro">تتوفر البرامج التدريبية من خلال فروع مركز العمران في مختلف إمارات دولة الإمارات العربية المتحدة.</p>
                <p class="section-intro">عند تقديم الطلب، يمكنك اختيار الإمارة والفرع الأنسب لك، وسيتم التواصل مع المتقدمين المقبولين لاستكمال إجراءات التسجيل.</p>
            </div>
            <div class="emirates-grid">
                {''.join([
                    f'<div class="emirate-chip">'
                    f'<svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                    f'<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
                    f'<circle cx="12" cy="10" r="3"/></svg>'
                    f'<span>{e}</span></div>'
                    for e in ['أبوظبي','دبي','الشارقة','عجمان','أم القيوين','رأس الخيمة','الفجيرة']
                ])}
            </div>
        </div>
    </section>

    <!-- EMOTIONAL CTA -->
    <section class="emotional-cta" id="emotional-cta">
        <div class="container">
            <div class="emotional-content">
                <h2 class="emotional-title">هل أنت مستعد لتبدأ؟</h2>
                <div class="emotional-text">
                    <p>قد تكون ساعات التدريب الأسبوعية هي الوقت الذي تستثمره اليوم، لكن المهارات التي تكتسبها قد يرافقك أثرها في خدمة وطنك لسنوات قادمة.</p>
                    <p>لا نعدك بتغيير حياتك في يوم واحد.</p>
                    <p class="emotional-highlight">لكننا نعدك بفرصة حقيقية لتبدأ العطاء.</p>
                </div>
                <a href="#apply" class="btn btn-primary btn-large">قدم طلبك الآن</a>
            </div>
        </div>
    </section>

    <!-- APPLICATION FORM -->
    <section class="application-form" id="apply">
        <div class="container">
            <div class="section-header">
                <h2 class="section-header__title">قدم طلبك للمشاركة</h2>
                <p class="section-header__subtitle">املأ البيانات التالية وسيتواصل معك فريق المبادرة</p>
            </div>
            {success_html if success else form_html}
        </div>
    </section>

    <!-- FINAL STATEMENT -->
    <section class="final-statement">
        <div class="container">
            <div class="statement-content">
                <div class="statement-amount">1,000,000 درهم</div>
                <h2 class="statement-heading">استثمار في الإنسان، وفاءً لأبناء الإمارات</h2>
                <div class="statement-brand">
                    <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png"
                         alt="مركز العمران للتدريب والتطوير" width="240" height="60">
                    <p class="statement-name">مركز العمران للتدريب والتطوير</p>
                </div>
                <p class="statement-text">نؤمن أن التدريب لا يمنحك مهارة فقط، بل يمنحك فرصة جديدة لخدمة وطنك.</p>
                <a href="#apply" class="btn btn-primary">قدم طلبك الآن</a>
            </div>
            <div class="statement-decoration" aria-hidden="true">
                <div class="decoration-circle decoration-blue"></div>
                <div class="decoration-circle decoration-green"></div>
                <div class="decoration-circle decoration-orange"></div>
                <div class="decoration-circle decoration-yellow"></div>
            </div>
        </div>
    </section>

</main>

<!-- FOOTER -->
<footer class="site-footer">
    <div class="container">
        <div class="footer-content">
            <div class="footer-brand">
                <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png"
                     alt="مركز العمران للتدريب والتطوير" width="240" height="60">
                <p class="footer-name">مركز العمران للتدريب والتطوير</p>
                <p class="footer-tagline">نصنع قادة الغد منذ 2010</p>
                <div class="footer-contact">
                    <a href="tel:+971505829697" class="footer-contact-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.19 11.8 19.79 19.79 0 0 1 1.12 3.13 2 2 0 0 1 3.1 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                        +971505829697
                    </a>
                    <a href="mailto:alomran.td@gmail.com" class="footer-contact-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                        alomran.td@gmail.com
                    </a>
                    <p class="footer-contact-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        السبت - الخميس: 8:00 ص - 8:00 م
                    </p>
                </div>
                <div class="footer-social">
                    <a href="https://www.facebook.com/alomran.td/" target="_blank" rel="noopener" aria-label="فيسبوك"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg></a>
                    <a href="https://www.instagram.com/alomran.td/" target="_blank" rel="noopener" aria-label="انستغرام"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg></a>
                    <a href="https://www.tiktok.com/@alomran.td" target="_blank" rel="noopener" aria-label="تيك توك"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1 0-5.78 2.92 2.92 0 0 1 .88.13V9a6.34 6.34 0 1 0 5.45 6.28V9.13a8.16 8.16 0 0 0 4.77 1.52V7.2a4.85 4.85 0 0 1-.7-.51z"/></svg></a>
                    <a href="https://wa.me/971505829697" target="_blank" rel="noopener" aria-label="واتساب"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>
                </div>
            </div>
            <nav class="footer-nav" aria-label="تنقل التذييل">
                <h4 class="footer-nav-title">مبادراتنا</h4>
                <ul class="footer-links">
                    <li><a href="#hero">مبادرة حماة الوطن</a></li>
                    <li><a href="#provide">ماذا نقدم</a></li>
                    <li><a href="#locations">فروعنا</a></li>
                </ul>
            </nav>
            <nav class="footer-nav" aria-label="روابط سريعة">
                <h4 class="footer-nav-title">روابط سريعة</h4>
                <ul class="footer-links">
                    <li><a href="#hero">الرئيسية</a></li>
                    <li><a href="#why">لماذا المبادرة</a></li>
                    <li><a href="#requirements">الشروط</a></li>
                    <li><a href="#locations">الفروع</a></li>
                    <li><a href="#apply">قدم طلبك الآن</a></li>
                </ul>
            </nav>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 مركز العمران للتدريب والتطوير. جميع الحقوق محفوظة.</p>
            <p class="footer-made-in">صُنع بـ ❤️ في الإمارات العربية المتحدة</p>
        </div>
    </div>
</footer>

<!-- WHATSAPP FLOAT -->
<a href="https://wa.me/971505829697?text=مرحباً، أود الاستفسار عن مبادرة حماة الوطن"
   class="whatsapp-float" target="_blank" rel="noopener"
   aria-label="تواصل عبر واتساب" id="whatsapp-float-btn">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>

<!-- POPUP -->
<div id="homat-popup" style="
    display:none;position:fixed;inset:0;
    background:rgba(0,0,0,0.6);z-index:9999;
    align-items:center;justify-content:center;">
    <div style="
        background:#fff;border-radius:20px;padding:2.5rem;
        max-width:480px;width:90%;text-align:center;
        font-family:Alexandria,sans-serif;direction:rtl;
        box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:popupIn 0.3s ease;">
        <div id="popup-icon" style="font-size:3.5rem;margin-bottom:1rem;"></div>
        <h3 id="popup-title" style="margin-bottom:0.75rem;font-size:1.3rem;"></h3>
        <p id="popup-msg" style="color:#555;margin-bottom:1.5rem;line-height:1.7;white-space:pre-line;"></p>
        <button onclick="closePopup()" style="
            background:linear-gradient(135deg,#406AB2,#60BB46);
            color:#fff;border:none;border-radius:50px;
            padding:0.75rem 2.5rem;font-size:1rem;
            font-family:Alexandria,sans-serif;cursor:pointer;">
            حسناً
        </button>
    </div>
</div>

<style>
@keyframes popupIn {{
    from {{ opacity:0; transform:scale(0.85); }}
    to   {{ opacity:1; transform:scale(1); }}
}}
</style>

{success_event}
<script src="/alomran_homat_alwatan/static/src/js/homat.js"></script>
</body>
</html>'''

        response = Response(html, content_type='text/html;charset=utf-8')
        return _secure_headers(response)

    # website=True: الصفحة بتمشي مع نظام اللغة تبع Odoo
    #   /homat-alwatan     -> إنكليزي (اللغة الافتراضية)
    #   /ar/homat-alwatan  -> عربي
    @http.route('/homat-alwatan', type='http', auth='public', website=True, sitemap=True)
    def homat_page(self, **kwargs):
        if _is_ar():
            return self._render_page()
        return self._render_page_en()

    def _render_page_en(self, success=False, error='', event_id=None):
        try:
            csrf = request.csrf_token()
        except Exception:
            csrf = ''
        form_token = _make_form_token()
        head_extra = _head_extra('en')
        success_event = _success_event('en', event_id) if success else ''

        error_html = ''
        if error:
            error_html = (
                f'<div style="background:#ffebee;color:#c62828;padding:1rem 2rem;'
                f'text-align:center;border-radius:8px;margin-bottom:1rem;">⚠️ {error}</div>'
            )

        success_html = ''
        if success:
            success_html = '''
            <div class="success-state">
                <div class="success-state__icon">
                    <svg viewBox="0 0 48 48" fill="none">
                        <circle cx="24" cy="24" r="23" stroke="#406AB3" stroke-width="2"/>
                        <path d="M14 24l7 7 13-13" stroke="#406AB3" stroke-width="2.5"
                              stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <h3 class="success-state__title">After Submission</h3>
                <p class="success-state__text">Thank you for your interest in the Homeland Protectors Initiative.</p>
                <p class="success-state__text">The Al Omran team will review applications according to the initiative\'s criteria and the approved selection process.</p>
                <p class="success-state__text">If you meet the criteria and are nominated, our team will contact you to complete the admission and registration process.</p>
                <p class="success-state__text success-state__text--note">Please note that submitting an application does not guarantee acceptance into the initiative, as seats are limited.</p>
            </div>'''

        form_html = '' if success else f'''
        {error_html}
        <form class="application-form__form" action="/homat-alwatan/apply" method="post">
            <input type="hidden" name="csrf_token" value="{csrf}">
            <input type="hidden" name="_lang" value="en">
            <input type="hidden" name="_ft" value="{form_token}">
            <input type="text" name="_trap" value="" style="display:none!important" tabindex="-1" autocomplete="off">
            <div class="form-grid">
                <div class="form-field">
                    <label class="form-field__label">Full Name <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="fullName" class="form-field__input" required maxlength="100" autocomplete="name">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Emirates ID Number <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="emiratesId" class="form-field__input" required
                           inputmode="numeric" placeholder="784-XXXX-XXXXXXX-X" maxlength="20">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Phone Number <span style="color:#e53e3e">*</span></label>
                    <input type="tel" name="phone" class="form-field__input" required
                           dir="ltr" placeholder="05X XXX XXXX" maxlength="15" autocomplete="tel">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Email Address <span style="color:#e53e3e">*</span></label>
                    <input type="email" name="email" class="form-field__input" required
                           dir="ltr" maxlength="150" autocomplete="email">
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">Preferred Branch <span style="color:#e53e3e">*</span></label>
                    <select name="branch" class="form-field__select" required>
                        <option value="" disabled selected>Select Branch</option>
                        <optgroup label="Al Ain">
                            <option value="وسط المدينة - العين">City Center</option>
                            <option value="اليحر مول - العين">Al Yahar Mall</option>
                            <option value="مكاني مول زاخر - العين">Makani Mall Zakher</option>
                            <option value="البراري مول - العين">Al Barari Mall</option>
                            <option value="الفوعة مول - العين">Al Foah Mall</option>
                        </optgroup>
                        <optgroup label="Abu Dhabi">
                            <option value="مزيد مول - ابوظبي">Mazyad Mall</option>
                            <option value="شارع المرور - ابوظبي">Al Muroor Street</option>
                        </optgroup>
                        <optgroup label="Dubai">
                            <option value="القرهود - دبي">Al Garhoud</option>
                            <option value="البرشا - دبي">Al Barsha</option>
                        </optgroup>
                        <optgroup label="Sharjah">
                            <option value="سنترال مول - الشارقة">Central Mall</option>
                        </optgroup>
                        <optgroup label="Ras Al Khaimah">
                            <option value="راك مول - راس الخيمة">RAK Mall</option>
                        </optgroup>
                        <optgroup label="Fujairah">
                            <option value="برج العوضي - الفجيرة">Al Awadhi Tower</option>
                        </optgroup>
                    </select>
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">Why do you want to participate in the Homeland Protectors Initiative? <span style="color:#e53e3e">*</span></label>
                    <textarea name="reason" class="form-field__textarea" rows="4" required maxlength="1000"></textarea>
                </div>
                <div class="form-field">
                    <label class="form-field__label">Can you commit to attending the training programs as scheduled?</label>
                    <div class="form-field__radio-group">
                        <label class="form-field__radio">
                            <input type="radio" name="timeCommitment" value="yes" required>
                            <span class="form-field__radio-mark"></span><span>Yes</span>
                        </label>
                        <label class="form-field__radio">
                            <input type="radio" name="timeCommitment" value="no">
                            <span class="form-field__radio-mark"></span><span>No</span>
                        </label>
                    </div>
                </div>
                <div class="form-field">
                    <label class="form-field__label">Are you ready to commit to attending and participating throughout the program?</label>
                    <div class="form-field__radio-group">
                        <label class="form-field__radio">
                            <input type="radio" name="fullProgram" value="yes" required>
                            <span class="form-field__radio-mark"></span><span>Yes</span>
                        </label>
                        <label class="form-field__radio">
                            <input type="radio" name="fullProgram" value="no">
                            <span class="form-field__radio-mark"></span><span>No</span>
                        </label>
                    </div>
                </div>
            </div>
            <fieldset class="form-confirmations">
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm1" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>I confirm that I am a UAE national, and that the information provided is accurate.</span>
                    </label>
                </div>
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm2" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>I agree to the terms and conditions of the initiative and the participant selection process.</span>
                    </label>
                </div>
            </fieldset>
            <div class="form-actions">
                <button type="submit" class="btn btn--primary btn--lg btn--full">Submit Application</button>
            </div>
        </form>'''

        html = f'''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Homeland Protectors Initiative | Al Omran Training &amp; Development Center</title>
    <meta name="description" content="A community-wide national initiative by Al Omran Training &amp; Development Center honoring UAE nationals who serve the homeland with free training and development programs.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="/alomran_homat_alwatan/static/src/img/favicon.png">
    <link rel="stylesheet" href="/alomran_homat_alwatan/static/src/css/homat.css">
{head_extra}
</head>
<body>

<header class="site-header">
    <div class="container">
        <a href="#hero" class="logo">
            <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png"
                 alt="Al Omran Training &amp; Development Center" width="240" height="60">
        </a>
        <nav class="main-nav">
            <ul class="nav-list">
                <li><a href="#hero" class="nav-link">Home</a></li>
                <li><a href="#provide" class="nav-link">What We Provide</a></li>
                <li><a href="#why" class="nav-link">Why the Initiative</a></li>
                <li><a href="#requirements" class="nav-link">Eligibility</a></li>
                <li><a href="#selection" class="nav-link">Selection</a></li>
                <li><a href="#locations" class="nav-link">Locations</a></li>
                <li><a href="#apply" class="nav-link nav-cta">Apply Now</a></li>
                <li><a href="/website/lang/ar?r=/homat-alwatan" class="lang-switch" style="background:#60BB46;border:2px solid #60BB46;color:#fff;font-weight:700;border-radius:6px;padding:5px 12px;">ع</a></li>
                <li>
                    <a href="/" class="nav-link"
                       style="display:flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,0.4);border-radius:50px;padding:6px 16px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                        Main Website
                    </a>
                </li>
            </ul>
        </nav>
        <button class="mobile-menu-toggle" aria-label="Open menu" aria-expanded="false">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
        </button>
    </div>
</header>

<main>

    <section class="hero" id="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <div class="container">
            <div class="hero-content">
                <div class="hero-badge">
                    <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    <span>Dedication in Service of the Homeland and National Pride</span>
                </div>
                <h1 class="hero-title">Homeland Protectors Initiative</h1>
                <p class="hero-subtitle">Honoring Dedication and Belonging in Service of Our Beloved Homeland</p>
                <div class="hero-copy">
                    <p>With great pride, Al Omran Training &amp; Development Center launches the Homeland Protectors Initiative — a community-wide national initiative valued at AED 1,000,000 that honors the sons and daughters of the UAE who dedicate their time and efforts to serving the nation, offering free training programs that develop their capabilities.</p>
                    <p class="hero-statement">Because serving the homeland is a responsibility we all take pride in, and because the dedication of the UAE&apos;s sons and daughters deserves to be supported.</p>
                </div>
                <div class="hero-actions">
                    <a href="#apply" class="btn btn-primary">Apply Now</a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-image-frame">
                    <img src="/alomran_homat_alwatan/static/src/img/homat-hero.jpg"
                         alt="UAE nationals serving the homeland" loading="eager" width="800" height="600">
                </div>
                <div class="hero-image-badge">
                    <span class="badge-number">1,000</span>
                    <span class="badge-text">National Opportunities</span>
                </div>
            </div>
        </div>
    </section>

    <section class="video-section">
        <div class="container">
            <div class="video-wrapper">
                <video autoplay muted loop playsinline id="heroVideo" width="1280" height="720">
                    <source src="/alomran_homat_alwatan/static/src/img/homat-video.mp4" type="video/mp4">
                    Your browser does not support video playback.
                </video>
                <button class="video-sound-btn" id="soundToggle" aria-label="Toggle sound">
                    <svg class="icon-sound-on" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                    <svg class="icon-sound-off" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <line x1="23" y1="9" x2="17" y2="15"/>
                        <line x1="17" y1="9" x2="23" y2="15"/>
                    </svg>
                </button>
            </div>
        </div>
    </section>

    <section class="statistics" id="statistics">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div><div class="stat-number">1,000,000</div><div class="stat-label">AED Initiative Value</div></div>
                <div class="stat-card"><div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div class="stat-number">1,000</div><div class="stat-label">Training Opportunities</div></div>
                <div class="stat-card"><div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="stat-number">12 Months</div><div class="stat-label">of Training &amp; Development</div></div>
                <div class="stat-card"><div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-number">Free</div><div class="stat-label">Comprehensive Training Programs</div></div>
            </div>
        </div>
    </section>

    <section class="features" id="provide">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">What We Provide</h2>
                <p class="section-subtitle">Free training and development programs to serve the homeland with excellence</p>
                <p class="section-intro">Through this initiative, each accepted participant will receive:</p>
            </div>
            <div class="features-grid">
                <div class="feature-card"><div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div><h3 class="feature-title">Comprehensive Training Programs</h3><p class="feature-text">High-quality training programs in leadership and professional development that enhance participants&apos; capabilities.</p></div>
                <div class="feature-card"><div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div><h3 class="feature-title">Leadership Skills</h3><p class="feature-text">Building leadership and teamwork skills that enable participants to fulfill their mission with excellence.</p></div>
                <div class="feature-card"><div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div><h3 class="feature-title">In-Person Training</h3><p class="feature-text">Practical, in-person training at any Al Omran branch across the UAE.</p></div>
                <div class="feature-card"><div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><h3 class="feature-title">Completely Free</h3><p class="feature-text">The initiative covers the full cost of training programs for all accepted participants.</p></div>
            </div>
        </div>
    </section>

    <section class="why" id="why">
        <div class="container">
            <div class="section-header"><h2 class="section-title">Why Did We Launch the Homeland Protectors Initiative?</h2></div>
            <div class="why-content">
                <div class="why-text">
                    <p>At Al Omran, we believe that the true investment is in people, and that serving the homeland is among the highest values.</p>
                    <p>The sons and daughters of the UAE have always been the shield and builders of its future, setting the finest examples of dedication and giving.</p>
                    <p>That is why we launched the Homeland Protectors Initiative — to honor those who serve the nation and give them the opportunity to develop their skills and capabilities.</p>
                </div>
                <div class="why-stats">
                    <div class="why-stat"><div class="why-stat-number">AED 1,000,000</div><div class="why-stat-label">in Training &amp; Development</div></div>
                    <div class="why-stat"><div class="why-stat-number">1,000 Opportunities</div><div class="why-stat-label">Real National Chances</div></div>
                    <div class="why-stat"><div class="why-stat-number">7 Emirates</div><div class="why-stat-label">Reaching Them Together</div></div>
                </div>
            </div>
        </div>
    </section>

    <section class="requirements" id="requirements">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">Who Can Apply?</h2>
                <p class="section-intro">The initiative is open to UAE nationals who meet the following criteria:</p>
            </div>
            <div class="requirements-list">
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Must be a UAE national holding UAE citizenship.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Must be committed to a national service initiative or volunteering with an accredited national organization.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Must be able to attend training programs according to the announced schedule.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Must be committed to attending and participating throughout the entire program duration.</p></div>
            </div>
            <div class="requirements-cta">
                <p>If you are ready to invest your time in serving the homeland and developing your capabilities, this opportunity is for you.</p>
                <a href="#apply" class="btn btn-primary">Apply for the Initiative</a>
            </div>
        </div>
    </section>

    <section class="selection" id="selection">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">How Are Participants Selected?</h2>
                <p class="section-intro">To ensure maximum impact, not all applications will be automatically accepted.</p>
            </div>
            <div class="process-timeline">
                <div class="process-step"><div class="step-number">01</div><div class="step-content"><h3>Meeting Initiative Requirements</h3><p>Verifying that the applicant meets all required criteria.</p></div></div>
                <div class="process-step"><div class="step-number">02</div><div class="step-content"><h3>Application Priority</h3><p>Application priority is taken into account within the participant selection process.</p></div></div>
                <div class="process-step"><div class="step-number">03</div><div class="step-content"><h3>National Institution Nominations</h3><p>The target number will be completed through nominations from national institutions across the UAE.</p></div></div>
            </div>
            <div class="process-highlight">
                <p>Ultimate Goal: Reach 1,000 participants across the UAE and give them a real opportunity to develop their capabilities and skills.</p>
            </div>
        </div>
    </section>

    <section class="locations" id="locations">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">Where Will the Training Programs Be Held?</h2>
                <p class="section-intro">Training programs are available through Al Omran Training &amp; Development Center branches across all emirates of the UAE.</p>
                <p class="section-intro">When applying, you can choose the emirate and branch most suitable for you. Accepted applicants will be contacted to complete the registration process.</p>
            </div>
            <div class="emirates-grid">
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Abu Dhabi</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Dubai</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Sharjah</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Ajman</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Umm Al Quwain</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Ras Al Khaimah</span></div>
                <div class="emirate-chip"><svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Fujairah</span></div>
            </div>
        </div>
    </section>

    <section class="emotional-cta" id="emotional-cta">
        <div class="container">
            <div class="emotional-content">
                <h2 class="emotional-title">Are You Ready to Begin?</h2>
                <div class="emotional-text">
                    <p>The weekly training hours you invest today may have an impact that accompanies you in serving your homeland for years to come.</p>
                    <p>We do not promise to change your life in a single day.</p>
                    <p class="emotional-highlight">But we promise you a real opportunity to begin your journey of giving.</p>
                </div>
                <a href="#apply" class="btn btn-primary btn-large">Apply Now</a>
            </div>
        </div>
    </section>

    <section class="application-form" id="apply">
        <div class="container">
            <div class="section-header">
                <h2 class="section-header__title">Submit Your Application</h2>
                <p class="section-header__subtitle">Fill in the details below and our team will get in touch</p>
            </div>
            {success_html if success else form_html}
        </div>
    </section>

    <section class="final-statement">
        <div class="container">
            <div class="statement-content">
                <div class="statement-amount">AED 1,000,000</div>
                <h2 class="statement-heading">An Investment in People, in Honor of the UAE&apos;s Sons and Daughters</h2>
                <div class="statement-brand">
                    <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png" alt="Al Omran" width="240" height="60">
                    <p class="statement-name">Al Omran Training &amp; Development Center</p>
                </div>
                <p class="statement-text">We believe that training does not just give you a skill — it gives you a new opportunity to serve your homeland.</p>
                <a href="#apply" class="btn btn-primary">Apply Now</a>
            </div>
            <div class="statement-decoration" aria-hidden="true">
                <div class="decoration-circle decoration-blue"></div>
                <div class="decoration-circle decoration-green"></div>
                <div class="decoration-circle decoration-orange"></div>
                <div class="decoration-circle decoration-yellow"></div>
            </div>
        </div>
    </section>

</main>

<footer class="site-footer">
    <div class="container">
        <div class="footer-content">
            <div class="footer-brand">
                <img src="/alomran_homat_alwatan/static/src/img/omran-full-logo.png" alt="Al Omran Training &amp; Development Center" width="240" height="60">
                <p class="footer-name">Al Omran Training &amp; Development Center</p>
                <p class="footer-tagline">Shaping Tomorrow&apos;s Leaders Since 2010</p>
                <div class="footer-contact">
                    <a href="tel:+971505829697" class="footer-contact-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.19 11.8 19.79 19.79 0 0 1 1.12 3.13 2 2 0 0 1 3.1 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>+971505829697</a>
                    <a href="mailto:alomran.td@gmail.com" class="footer-contact-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>alomran.td@gmail.com</a>
                    <p class="footer-contact-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>Sat - Thu: 8:00 AM - 8:00 PM</p>
                </div>
                <div class="footer-social">
                    <a href="https://www.facebook.com/alomran.td/" target="_blank" rel="noopener" aria-label="Facebook"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg></a>
                    <a href="https://www.instagram.com/alomran.td/" target="_blank" rel="noopener" aria-label="Instagram"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg></a>
                    <a href="https://www.tiktok.com/@alomran.td" target="_blank" rel="noopener" aria-label="TikTok"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1 0-5.78 2.92 2.92 0 0 1 .88.13V9a6.34 6.34 0 1 0 5.45 6.28V9.13a8.16 8.16 0 0 0 4.77 1.52V7.2a4.85 4.85 0 0 1-.7-.51z"/></svg></a>
                    <a href="https://wa.me/971505829697" target="_blank" rel="noopener" aria-label="WhatsApp"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>
                </div>
            </div>
            <nav class="footer-nav">
                <h4 class="footer-nav-title">Our Initiatives</h4>
                <ul class="footer-links">
                    <li><a href="#hero">Homeland Protectors Initiative</a></li>
                    <li><a href="#provide">What We Provide</a></li>
                    <li><a href="#locations">Our Branches</a></li>
                </ul>
            </nav>
            <nav class="footer-nav">
                <h4 class="footer-nav-title">Quick Links</h4>
                <ul class="footer-links">
                    <li><a href="#hero">Home</a></li>
                    <li><a href="#why">Why the Initiative</a></li>
                    <li><a href="#requirements">Eligibility</a></li>
                    <li><a href="#locations">Branches</a></li>
                    <li><a href="#apply">Apply Now</a></li>
                </ul>
            </nav>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 Al Omran Training &amp; Development Center. All Rights Reserved.</p>
            <p class="footer-made-in">Made with ❤️ in the United Arab Emirates</p>
        </div>
    </div>
</footer>

<a href="https://wa.me/971505829697?text=Hello, I would like to inquire about the Homeland Protectors Initiative"
   class="whatsapp-float" target="_blank" rel="noopener"
   aria-label="Contact via WhatsApp" id="whatsapp-float-btn">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>

<div id="homat-popup" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;">
    <div style="background:#fff;border-radius:20px;padding:2.5rem;max-width:480px;width:90%;text-align:center;font-family:Inter,sans-serif;box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:popupIn 0.3s ease;">
        <div id="popup-icon" style="font-size:3.5rem;margin-bottom:1rem;"></div>
        <h3 id="popup-title" style="margin-bottom:0.75rem;font-size:1.3rem;"></h3>
        <p id="popup-msg" style="color:#555;margin-bottom:1.5rem;line-height:1.7;white-space:pre-line;"></p>
        <button onclick="closePopup()" style="background:linear-gradient(135deg,#406AB2,#60BB46);color:#fff;border:none;border-radius:50px;padding:0.75rem 2.5rem;font-size:1rem;font-family:Inter,sans-serif;cursor:pointer;">OK</button>
    </div>
</div>
<style>@keyframes popupIn {{ from {{ opacity:0;transform:scale(0.85); }} to {{ opacity:1;transform:scale(1); }} }}</style>
{success_event}
<script src="/alomran_homat_alwatan/static/src/js/homat.js"></script>
</body>
</html>'''

        response = Response(html, content_type='text/html;charset=utf-8')
        return _secure_headers(response)

    # الرابط القديم للنسخة الإنكليزية: تحويل دائم مع تثبيت الإنكليزي بالكوكي
    # (بيحافظ على gclid وباقي الـ query string)
    @http.route('/homat-alwatan/en', type='http', auth='public', website=False, sitemap=False)
    def homat_page_en(self, **kwargs):
        target = PAGE_PATH
        qs = request.httprequest.query_string.decode('utf-8', 'ignore')
        if qs:
            target += '?' + qs
        return request.redirect('/website/lang/en?r=' + quote(target, safe=''), code=301)

    @http.route('/homat-alwatan/apply', type='http', auth='public', website=False, methods=['POST'], csrf=False)
    def homat_apply(self, **post):
        lang = 'en' if post.get('_lang') == 'en' else 'ar'
        msg = MESSAGES[lang]
        is_ajax = request.httprequest.headers.get('X-Requested-With') == 'XMLHttpRequest'
        ip = _client_ip()

        def _render(success=False, error='', event_id=None):
            if lang == 'en':
                return self._render_page_en(success=success, error=error, event_id=event_id)
            return self._render_page(success=success, error=error, event_id=event_id)

        def _ok(event_id=None):
            # event_id بس للطلبات الحقيقية — الـ honeypot والبوتات ما بينحسبوا تحويل
            if is_ajax:
                payload = {'success': True}
                if event_id:
                    payload['event_id'] = event_id
                return _json_response(payload)
            return _render(success=True, event_id=event_id)

        def _fail(error_msg, status=200):
            if is_ajax:
                return _json_response({'success': False, 'error': error_msg}, status)
            return _render(error=error_msg)

        try:
            # CSRF: نفس أسلوب فورمات Odoo الرسمية — بيتفحص للمستخدم المسجّل دخول،
            # لأن جلسة الزائر المجهول مش ثابتة. للزوار الحماية من التوكن الموقّع تحت.
            if request.session.uid and not request.validate_csrf(post.get('csrf_token')):
                return _fail(msg['expired'], 400)

            # Honeypot
            if post.get('_trap'):
                _logger.info('Homat: honeypot triggered (ip=%s)', ip)
                return _ok()

            # توكن موقّع بوقت فتح الصفحة
            token_state = _check_form_token(post.get('_ft'))
            if token_state == 'too_fast':
                _logger.info('Homat: submission too fast (ip=%s)', ip)
                return _ok()
            if token_state != 'ok':
                return _fail(msg['expired'], 400)

            # Rate limit حسب الـ IP
            if _rate_limited(ip):
                _logger.warning('Homat: rate limit hit (ip=%s)', ip)
                return _fail(msg['rate_limited'], 429)

            # Sanitization
            full_name   = _sanitize(post.get('fullName'), 100)
            emirates_id = _sanitize(post.get('emiratesId'), 20)
            phone       = _sanitize(post.get('phone'), 15)
            email       = _sanitize(post.get('email'), 150)
            branch      = _sanitize(post.get('branch'), 100)
            reason      = _sanitize(post.get('reason'), 1000, multiline=True)
            time_commit = _sanitize(post.get('timeCommitment'), 3)
            full_prog   = _sanitize(post.get('fullProgram'), 3)

            if not all([full_name, emirates_id, phone, email, branch, reason]):
                return _fail(msg['required'])
            if time_commit not in ('yes', 'no') or full_prog not in ('yes', 'no'):
                return _fail(msg['required'])
            if not (post.get('confirm1') and post.get('confirm2')):
                return _fail(msg['required'])

            eid_valid, emirates_id_clean = _validate_emirates_id(emirates_id)
            if not eid_valid:
                return _fail(msg['eid'])

            phone_valid, phone_clean = _validate_phone(phone)
            if not phone_valid:
                return _fail(msg['phone'])

            if not _validate_email(email):
                return _fail(msg['email'])

            if branch not in BRANCH_COMPANY_MAPPING:
                return _fail(msg['branch'])

            if _is_duplicate(phone_clean, emirates_id_clean):
                return _fail(msg['duplicate'])

            # UTM: بس أسماء نظيفة، منشان ما حدا يعبّي utm.source بقيم عشوائية
            utm_source_id = False
            utm_source = (request.httprequest.cookies.get('utm_source')
                          or request.httprequest.args.get('utm_source', ''))
            utm_source = (utm_source or '').strip()
            if utm_source and _UTM_RE.match(utm_source):
                utm_source_id = _get_utm_source(utm_source)

            description_text = (
                "مبادرة حماة الوطن - طلب مشاركة\n"
                "=================================\n"
                f"الاسم الكامل:       {full_name}\n"
                f"رقم الهوية:         {emirates_id_clean}\n"
                f"الهاتف:             {phone_clean}\n"
                f"البريد الإلكتروني:  {email}\n"
                f"الفرع المفضل:       {branch}\n"
                f"الالتزام بالوقت:    {time_commit}\n"
                f"الالتزام بالبرنامج: {full_prog}\n"
                f"لغة النموذج:        {lang}\n"
                f"IP: {ip}\n"
                "\n"
                "سبب الرغبة في المشاركة:\n"
                f"{reason}"
            )

            env = request.env
            tag = env['crm.tag'].sudo().search([('name', '=', TAG_NAME)], limit=1)
            if not tag:
                tag = env['crm.tag'].sudo().create({'name': TAG_NAME})

            company_id, salesperson_id = self._get_company_and_salesperson(branch)
            stage = env['crm.stage'].sudo().search([], limit=1)

            lead_vals = {
                'name': f'حماة الوطن - {full_name}',
                'contact_name': full_name,
                'phone': phone_clean,
                'email_from': email,
                # plaintext2html بيعمل escape للمدخلات وبيحافظ على الأسطر
                'description': plaintext2html(description_text),
                'tag_ids': [(4, tag.id)],
                'partner_name': full_name,
                'type': 'lead',
                'company_id': company_id,
                'user_id': salesperson_id,
            }
            if stage:
                lead_vals['stage_id'] = stage.id
            if utm_source_id:
                lead_vals['source_id'] = utm_source_id

            lead = env['crm.lead'].sudo().create(lead_vals)
            send_lead_created(lead)
            # بدون بيانات شخصية باللوغ
            _logger.info('Homat lead created: id=%s branch=%s lang=%s', lead.id, branch, lang)
            return _ok(lead_event_id(lead))

        except Exception:
            _logger.exception('Homat apply error (ip=%s)', ip)
            return _fail(msg['generic'], 500)
