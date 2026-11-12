# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from .openai_ads import send_lead_created, lead_event_id, pixel_head_snippet, pixel_lead_script
from odoo.tools import plaintext2html
from odoo.tools.misc import hmac as odoo_hmac
from datetime import datetime, timedelta
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

PAGE_PATH = '/initiative'
GA4_ID = 'G-9DGH1G5YEY'   # نفس خاصية GA4 تبع الموقع الرئيسي
TAG_NAME = 'مبادرة المرأة الإماراتية'
ENGLISH_LEVELS = ('beginner', 'intermediate', 'good', 'advanced', 'unknown')

# حماية من السبام
FORM_TOKEN_SCOPE = 'alomran-women-initiative-form'
FORM_MIN_SECONDS = 3            # أي إرسال أسرع من هيك = بوت
FORM_MAX_AGE = 24 * 3600        # التوكن صالح 24 ساعة
RATE_LIMIT_COUNT = 5            # أقصى عدد طلبات من نفس الـ IP
RATE_LIMIT_WINDOW_MIN = 60      # خلال هالمدة (دقائق)

MESSAGES = {
    'ar': {
        'required': 'يرجى ملء جميع الحقول المطلوبة',
        'eid': 'رقم الهوية الإماراتية غير صحيح — يجب أن يبدأ بـ 784 ويتكون من 15 رقم',
        'phone': 'رقم الهاتف غير صحيح — يرجى إدخال رقم إماراتي صحيح',
        'email': 'البريد الإلكتروني غير صحيح',
        'branch': 'يرجى اختيار فرع صحيح',
        'duplicate': 'لقد سجّلتِ مسبقاً في المبادرة خلال الـ 24 ساعة الماضية',
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

LANG_SWITCH_STYLE = ('background:#60BB46;border:2px solid #60BB46;color:#fff;font-weight:700;'
                     'border-radius:6px;padding:5px 12px;text-decoration:none;')


def _sanitize(value, max_len=500, multiline=False):
    """تنظيف للتخزين: إزالة محارف التحكم والقص.
    ما منعمل HTML escape هون، لأن Odoo بيعمل escape وقت العرض، والوصف
    بيتحول لـ HTML آمن عن طريق plaintext2html."""
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

def _rate_limited(ip):
    if not ip:
        return False
    try:
        since = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MIN)
        count = request.env['crm.lead'].sudo().with_context(active_test=False).search_count([
            ('tag_ids.name', '=', TAG_NAME),
            ('create_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S')),
            ('description', 'ilike', f'IP: {ip}'),
        ])
        return count >= RATE_LIMIT_COUNT
    except Exception as e:
        _logger.warning('Initiative rate-limit check error: %s', e)
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
        f"{{form_name: 'women_initiative', language: '{lang}'}}); }}</script>"
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
        _logger.warning('Duplicate check error: %s', e)
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


class InitiativeController(http.Controller):

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
                <h3 class="success-state__title">شكراً لتقديمك!</h3>
                <p class="success-state__text">سيقوم فريق مركز العمران بمراجعة طلبك وفق شروط المبادرة.</p>
                <p class="success-state__text">في حال استيفاء الشروط وترشيحك للاستفادة، سيتواصل معك فريق المبادرة.</p>
                <p class="success-state__text success-state__text--note">
                    يرجى العلم أن تعبئة النموذج لا تعني القبول النهائي،
                    وأن عدد المقاعد محدود بـ500 مستفيدة.
                </p>
            </div>'''

        form_html = '' if success else f'''
        {error_html}
        <form class="application-form__form" action="/initiative/apply" method="post">
            <input type="hidden" name="csrf_token" value="{csrf}">
            <input type="hidden" name="_lang" value="ar">
            <input type="hidden" name="_ft" value="{form_token}">
            <input type="text" name="_trap" value="" style="display:none!important" tabindex="-1" autocomplete="off">
            <div class="form-grid">
                <div class="form-field">
                    <label class="form-field__label">الاسم الكامل <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="fullName" class="form-field__input" required maxlength="100">
                </div>
                <div class="form-field">
                    <label class="form-field__label">رقم الهوية الإماراتية <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="emiratesId" class="form-field__input" required
                           inputmode="numeric" placeholder="784-XXXX-XXXXXXX-X" maxlength="20">
                </div>
                <div class="form-field">
                    <label class="form-field__label">رقم الهاتف <span style="color:#e53e3e">*</span></label>
                    <input type="tel" name="phone" class="form-field__input" required
                           dir="ltr" placeholder="05X XXX XXXX" maxlength="15">
                </div>
                <div class="form-field">
                    <label class="form-field__label">البريد الإلكتروني <span style="color:#e53e3e">*</span></label>
                    <input type="email" name="email" class="form-field__input" required
                           dir="ltr" maxlength="150">
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">الفرع المفضل للدراسة <span style="color:#e53e3e">*</span></label>
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
                    <label class="form-field__label">مستوى اللغة الإنجليزية <span style="color:#e53e3e">*</span></label>
                    <select name="englishLevel" class="form-field__select" required>
                        <option value="" disabled selected>اختر المستوى</option>
                        <option value="beginner">مبتدئ / Beginner</option>
                        <option value="intermediate">متوسط / Intermediate</option>
                        <option value="good">جيد / Good</option>
                        <option value="advanced">متقدم / Advanced</option>
                        <option value="unknown">لا أعرف / Not Sure</option>
                    </select>
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">لماذا ترغبين في المشاركة؟ <span style="color:#e53e3e">*</span></label>
                    <textarea name="reason" class="form-field__textarea" rows="4" required maxlength="1000"></textarea>
                </div>
                <div class="form-field">
                    <label class="form-field__label">هل يمكنكِ الالتزام بساعة ونصف، ثلاثة أيام أسبوعياً؟</label>
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
                    <label class="form-field__label">هل أنتِ مستعدة للالتزام بالحضور طوال فترة البرنامج؟</label>
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
                        <span>أقر بأنني امرأة إماراتية وأبلغ من العمر 18 عاماً أو أكثر، وأن البيانات صحيحة.</span>
                    </label>
                </div>
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm2" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>أوافق على شروط وأحكام المبادرة وآلية اختيار المستفيدات.</span>
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
    <title>مبادرة العمران لتمكين المرأة الإماراتية | 500 فرصة تعليمية مجانية</title>
    <meta name="description" content="مبادرة مجتمعية بقيمة 5 ملايين درهم لتوفير سنة كاملة من تعلم اللغة الإنجليزية مجاناً لـ500 امرأة إماراتية.">
    <meta name="robots" content="index, follow">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Alexandria:wght@300;400;500;600;700;800&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="/alomran_initiative/static/src/img/favicon.png">
    <link rel="stylesheet" href="/alomran_initiative/static/src/css/initiative.css">
{head_extra}
</head>
<body>

<header class="site-header">
    <div class="container">
        <a href="/ar/initiative" class="logo">
            <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                 alt="مركز العمران للتدريب والتطوير" width="240" height="60">
        </a>
        <nav class="main-nav">
            <ul class="nav-list">
                <li><a href="#provide" class="nav-link">ماذا نقدم</a></li>
                <li><a href="#requirements" class="nav-link">الشروط</a></li>
                <li><a href="#selection" class="nav-link">آلية الاختيار</a></li>
                <li><a href="#locations" class="nav-link">الفروع</a></li>
                <li><a href="#apply" class="nav-link nav-cta">قدمي طلبك الآن</a></li>
                <li><a href="/website/lang/en?r=/initiative" class="lang-switch" style="{LANG_SWITCH_STYLE}">EN</a></li>
                <li>
                    <a href="/ar" class="nav-link"
                       style="display:flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,0.4);border-radius:50px;padding:6px 16px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                        الموقع الرئيسي
                    </a>
                </li>
            </ul>
        </nav>
    </div>
</header>

<main>

    <!-- HERO -->
    <section class="hero" id="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <div class="container">
            <div class="hero-content">
                <div class="hero-collab-logos">
                    <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                         alt="مركز العمران للتدريب والتطوير" class="collab-logo" width="180" height="45">
                    <span class="collab-x">×</span>
                    <img src="/alomran_initiative/static/src/img/ewd-logo.png"
                         alt="يوم المرأة الإماراتية" class="collab-logo collab-logo--partner" width="60" height="60">
                </div>
                <div class="hero-badge">
                    <svg class="icon" width="20" height="20" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    <span>تمكين المرأة الإماراتية بمناسبة يوم المرأة الإماراتية</span>
                </div>
                <h1 class="hero-title">مبادرة العمران لتمكين المرأة الإماراتية</h1>
                <p class="hero-subtitle">5 ملايين درهم لدعم تعليم المرأة الإماراتية</p>
                <div class="hero-copy">
                    <p>بمناسبة يوم المرأة الإماراتية، يطلق مركز العمران للتدريب والتطوير مبادرة
                       مجتمعية بقيمة 5,000,000 درهم، لتوفير فرصة تعليمية مجانية لـ 500 امرأة
                       إماراتية لتعلم اللغة الإنجليزية لمدة عام كامل.</p>
                    <p class="hero-statement">لأن تمكين المرأة يبدأ بالعلم، ولأن طموح المرأة
                       الإماراتية يستحق أن يجد من يدعمه.</p>
                </div>
                <div class="hero-actions">
                    <a href="#apply" class="btn btn-primary">قدمي طلبك الآن</a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-image-frame">
                    <img src="/alomran_initiative/static/src/img/emirati-woman.jpg"
                         alt="امرأة إماراتية في بيئة تعليمية" loading="eager" width="800" height="600">
                </div>
                <div class="hero-image-badge">
                    <span class="badge-number">500</span>
                    <span class="badge-text">فرصة تعليمية</span>
                </div>
            </div>
        </div>
    </section>

    <!-- VIDEO SECTION -->
    <section class="video-section">
        <div class="container">
            <div class="video-wrapper">
                <video autoplay muted loop playsinline id="heroVideo" width="1280" height="720">
                    <source src="/alomran_initiative/static/src/img/hero-video.mp4" type="video/mp4">
                    المتصفح لا يدعم تشغيل الفيديو.
                </video>
                <button class="video-sound-btn" id="soundToggle" aria-label="تشغيل/إيقاف الصوت">
                    <svg class="icon-sound-on" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <svg class="icon-sound-off" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2" style="display:none">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <line x1="23" y1="9" x2="17" y2="15"></line>
                        <line x1="17" y1="9" x2="23" y2="15"></line>
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
                    <div class="stat-number">5,000,000</div>
                    <div class="stat-label">درهم قيمة المبادرة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg></div>
                    <div class="stat-number">500</div>
                    <div class="stat-label">امرأة إماراتية</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
                    <div class="stat-number">سنة كاملة</div>
                    <div class="stat-label">من التعليم</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <div class="stat-number">بدون رسوم</div>
                    <div class="stat-label">دراسة اللغة الإنجليزية</div>
                </div>
            </div>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="features" id="provide">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">ماذا نقدم لكِ؟</h2>
                <p class="section-subtitle">سنة كاملة من تعلم اللغة الإنجليزية مجاناً</p>
                <p class="section-intro">من خلال المبادرة ستحصل كل مستفيدة يتم قبولها على:</p>
            </div>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div>
                    <h3 class="feature-title">سنة دراسية كاملة</h3>
                    <p class="feature-text">سنة دراسية كاملة لتعلم وتطوير مهارات اللغة الإنجليزية.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
                    <h3 class="feature-title">مهارات تواصل أقوى</h3>
                    <p class="feature-text">تطوير مهارات التواصل من خلال التدريب على المحادثة والاستماع والقراءة والكتابة.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div>
                    <h3 class="feature-title">دراسة حضورية</h3>
                    <p class="feature-text">دراسة حضورية في أحد فروع مركز العمران في مختلف إمارات الدولة.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <h3 class="feature-title">بدون رسوم دراسية</h3>
                    <p class="feature-text">تتحمل المبادرة تكلفة البرنامج التعليمي للمستفيدات المقبولات.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- WHY -->
    <section class="why" id="why">
        <div class="container">
            <div class="section-header"><h2 class="section-title">لماذا أطلقنا هذه المبادرة؟</h2></div>
            <div class="why-content">
                <div class="why-text">
                    <p>نؤمن في مركز العمران أن الاستثمار الحقيقي هو الاستثمار في الإنسان.</p>
                    <p>والمرأة الإماراتية كانت ولا تزال شريكاً أساسياً في مسيرة التنمية والنجاح.</p>
                    <p>لذلك، وبمناسبة يوم المرأة الإماراتية، أردنا أن نقدم مبادرة يكون أثرها عملياً ومستداماً.</p>
                </div>
                <div class="why-stats">
                    <div class="why-stat"><div class="why-stat-number">5 ملايين درهم</div><div class="why-stat-label">في التعليم</div></div>
                    <div class="why-stat"><div class="why-stat-number">500 فرصة</div><div class="why-stat-label">تعليمية حقيقية</div></div>
                    <div class="why-stat"><div class="why-stat-number">500 قصة نجاح</div><div class="why-stat-label">محتملة</div></div>
                </div>
            </div>
        </div>
    </section>

    <!-- REQUIREMENTS -->
    <section class="requirements" id="requirements">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">من يمكنها التقديم؟</h2>
                <p class="section-intro">المبادرة مخصصة للمرأة الإماراتية التي تنطبق عليها الشروط التالية:</p>
            </div>
            <div class="requirements-list">
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن تكون المتقدمة امرأة إماراتية.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن يكون عمرها 18 عاماً أو أكثر.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن تكون متفرغة لمدة ساعة ونصف، ثلاثة أيام أسبوعياً.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>أن تكون جادة وقادرة على الالتزام بالحضور والدوام طوال فترة البرنامج.</p></div>
            </div>
            <div class="requirements-cta">
                <p>إذا كنتِ مستعدة لاستثمار وقتك في نفسك وتطوير مستقبلك، فهذه الفرصة لكِ.</p>
                <a href="#apply" class="btn btn-primary">أريد التقديم على المبادرة</a>
            </div>
        </div>
    </section>

    <!-- SELECTION -->
    <section class="selection" id="selection">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">كيف يتم اختيار المستفيدات؟</h2>
                <p class="section-intro">حرصاً على تحقيق أكبر أثر ممكن، لن يتم قبول جميع الطلبات تلقائياً.</p>
            </div>
            <div class="process-timeline">
                <div class="process-step"><div class="step-number">01</div><div class="step-content"><h3>مطابقة شروط المبادرة</h3><p>التأكد من استيفاء المتقدمة لجميع الشروط المطلوبة.</p></div></div>
                <div class="process-step"><div class="step-number">02</div><div class="step-content"><h3>أولوية التقديم</h3><p>تُؤخذ أولوية التقديم بعين الاعتبار ضمن آلية اختيار المستفيدات.</p></div></div>
                <div class="process-step"><div class="step-number">03</div><div class="step-content"><h3>ترشيحات المؤسسات الداعمة للمرأة</h3><p>سيتم استكمال العدد المستهدف من خلال ترشيحات المؤسسات الحكومية الداعمة للمرأة.</p></div></div>
            </div>
            <div class="process-highlight">
                <p>الهدف النهائي: الوصول إلى 500 امرأة إماراتية ومنحهن فرصة حقيقية لتطوير اللغة الإنجليزية لمدة عام كامل.</p>
            </div>
        </div>
    </section>

    <!-- LOCATIONS -->
    <section class="locations" id="locations">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">أين ستكون الدراسة؟</h2>
                <p class="section-intro">تتوفر الدراسة من خلال فروع مركز العمران في مختلف إمارات دولة الإمارات العربية المتحدة.</p>
                <p class="section-intro">عند تقديم الطلب، يمكنك اختيار الإمارة والفرع الأنسب لكِ، وسيتم التواصل مع المتقدمات المقبولات لاستكمال إجراءات التسجيل.</p>
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
                <h2 class="emotional-title">هل أنتِ مستعدة لتبدئي؟</h2>
                <div class="emotional-text">
                    <p>قد تكون ساعة ونصف، ثلاثة أيام في الأسبوع، هي الوقت الذي تستثمرينه اليوم،
                       لكن المهارة قد ترافقك لسنوات قادمة.</p>
                    <p>لا نعدكِ بأن اللغة الإنجليزية ستغير حياتكِ في يوم واحد.</p>
                    <p class="emotional-highlight">لكننا نعدكِ بفرصة حقيقية لتبدئي التغيير.</p>
                </div>
                <a href="#apply" class="btn btn-primary btn-large">قدمي طلبك الآن</a>
            </div>
        </div>
    </section>

    <!-- APPLICATION FORM -->
    <section class="application-form" id="apply">
        <div class="container">
            <div class="section-header">
                <h2 class="section-header__title">قدمي طلبك للمشاركة</h2>
                <p class="section-header__subtitle">املئي البيانات التالية وسيتواصل معك فريق المبادرة</p>
            </div>
            {success_html if success else form_html}
        </div>
    </section>

    <!-- FINAL STATEMENT -->
    <section class="final-statement">
        <div class="container">
            <div class="statement-content">
                <div class="statement-amount">5,000,000 درهم</div>
                <h2 class="statement-heading">استثمار في الإنسان، احتفاءً بالمرأة الإماراتية</h2>
                <div class="statement-brand">
                    <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                         alt="مركز العمران" width="240" height="60">
                    <p class="statement-name">مركز العمران للتدريب والتطوير</p>
                </div>
                <p class="statement-text">نؤمن أن التعليم لا يمنحكِ مهارة فقط، بل يمنحكِ فرصة جديدة.</p>
                <a href="#apply" class="btn btn-primary">قدمي طلبك الآن</a>
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
                <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                     alt="مركز العمران للتدريب والتطوير" width="240" height="60">
                <p class="footer-name">مركز العمران للتدريب والتطوير</p>
                <p class="footer-initiative">المبادرة المجتمعية لتمكين المرأة الإماراتية</p>
            </div>
            <nav class="footer-nav" aria-label="تنقل التذييل">
                <ul class="footer-links">
                    <li><a href="#provide">ماذا نقدم</a></li>
                    <li><a href="#requirements">الشروط</a></li>
                    <li><a href="#selection">آلية الاختيار</a></li>
                    <li><a href="#locations">الفروع</a></li>
                    <li><a href="#apply">التقديم</a></li>
                </ul>
            </nav>
            <div class="footer-legal">
                <a href="#" class="footer-legal-link">سياسة الخصوصية</a>
                <a href="#" class="footer-legal-link">الشروط والأحكام</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 مركز العمران للتدريب والتطوير. جميع الحقوق محفوظة.</p>
        </div>
    </div>
</footer>

<!-- Popup -->
<div id="initiative-popup" style="
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
<script src="/alomran_initiative/static/src/js/initiative.js"></script>
</body>
</html>'''

        response = Response(html, content_type='text/html;charset=utf-8')
        return _secure_headers(response)

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
                <h3 class="success-state__title">Thank you for applying!</h3>
                <p class="success-state__text">The Al Omran team will review your application according to the initiative’s criteria.</p>
                <p class="success-state__text">If you meet the criteria and are nominated, the initiative team will contact you.</p>
                <p class="success-state__text success-state__text--note">
                    Please note that submitting the form does not guarantee final acceptance,
                    and seats are limited to 500 beneficiaries.
                </p>
            </div>'''

        form_html = '' if success else f'''
        {error_html}
        <form class="application-form__form" action="/initiative/apply" method="post">
            <input type="hidden" name="csrf_token" value="{csrf}">
            <input type="hidden" name="_lang" value="en">
            <input type="hidden" name="_ft" value="{form_token}">
            <input type="text" name="_trap" value="" style="display:none!important" tabindex="-1" autocomplete="off">
            <div class="form-grid">
                <div class="form-field">
                    <label class="form-field__label">Full Name <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="fullName" class="form-field__input" required maxlength="100">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Emirates ID Number <span style="color:#e53e3e">*</span></label>
                    <input type="text" name="emiratesId" class="form-field__input" required
                           inputmode="numeric" placeholder="784-XXXX-XXXXXXX-X" maxlength="20">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Phone Number <span style="color:#e53e3e">*</span></label>
                    <input type="tel" name="phone" class="form-field__input" required
                           dir="ltr" placeholder="05X XXX XXXX" maxlength="15">
                </div>
                <div class="form-field">
                    <label class="form-field__label">Email Address <span style="color:#e53e3e">*</span></label>
                    <input type="email" name="email" class="form-field__input" required
                           dir="ltr" maxlength="150">
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">Preferred Study Branch <span style="color:#e53e3e">*</span></label>
                    <select name="branch" class="form-field__select" required>
                        <option value="" disabled selected>Select a branch</option>
                        <optgroup label="Al Ain">
                            <option value="وسط المدينة - العين">City Centre</option>
                            <option value="اليحر مول - العين">Al Yahar Mall</option>
                            <option value="مكاني مول زاخر - العين">Makani Zakher Mall</option>
                            <option value="البراري مول - العين">Al Barari Mall</option>
                            <option value="الفوعة مول - العين">Al Foah Mall</option>
                        </optgroup>
                        <optgroup label="Abu Dhabi">
                            <option value="مزيد مول - ابوظبي">Mazyad Mall</option>
                            <option value="شارع المرور - ابوظبي">Muroor Road</option>
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
                            <option value="برج العوضي - الفجيرة">Al Awadi Tower</option>
                        </optgroup>
                    </select>
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">English Level <span style="color:#e53e3e">*</span></label>
                    <select name="englishLevel" class="form-field__select" required>
                        <option value="" disabled selected>Select your level</option>
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="good">Good</option>
                        <option value="advanced">Advanced</option>
                        <option value="unknown">Not Sure</option>
                    </select>
                </div>
                <div class="form-field form-field--full">
                    <label class="form-field__label">Why would you like to participate? <span style="color:#e53e3e">*</span></label>
                    <textarea name="reason" class="form-field__textarea" rows="4" required maxlength="1000"></textarea>
                </div>
                <div class="form-field">
                    <label class="form-field__label">Can you commit to 1.5 hours, three days a week?</label>
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
                    <label class="form-field__label">Are you ready to commit to attending for the full duration of the program?</label>
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
                        <span>I confirm that I am an Emirati woman aged 18 or older, and that the information provided is accurate.</span>
                    </label>
                </div>
                <div class="form-confirmation">
                    <label class="form-field__checkbox">
                        <input type="checkbox" name="confirm2" required>
                        <span class="form-field__checkbox-mark"></span>
                        <span>I agree to the initiative’s terms and conditions and the beneficiary selection process.</span>
                    </label>
                </div>
            </fieldset>
            <div class="form-actions">
                <button type="submit" class="btn btn--primary btn--lg btn--full">
                    Submit Application
                </button>
            </div>
        </form>'''

        html = f'''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Al Omran Initiative for Empowering Emirati Women | 500 Free Learning Opportunities</title>
    <meta name="description" content="A community initiative worth AED 5 million offering a full year of free English language learning to 500 Emirati women.">
    <meta name="robots" content="index, follow">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="/alomran_initiative/static/src/img/favicon.png">
    <link rel="stylesheet" href="/alomran_initiative/static/src/css/initiative.css">
{head_extra}
</head>
<body>

<header class="site-header">
    <div class="container">
        <a href="/initiative" class="logo">
            <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                 alt="Al Omran Training &amp; Development Center" width="240" height="60">
        </a>
        <nav class="main-nav">
            <ul class="nav-list">
                <li><a href="#provide" class="nav-link">What We Offer</a></li>
                <li><a href="#requirements" class="nav-link">Eligibility</a></li>
                <li><a href="#selection" class="nav-link">Selection</a></li>
                <li><a href="#locations" class="nav-link">Locations</a></li>
                <li><a href="#apply" class="nav-link nav-cta">Apply Now</a></li>
                <li><a href="/website/lang/ar?r=/initiative" class="lang-switch" style="{LANG_SWITCH_STYLE}">ع</a></li>
                <li>
                    <a href="/" class="nav-link"
                       style="display:flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,0.4);border-radius:50px;padding:6px 16px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                        Main Website
                    </a>
                </li>
            </ul>
        </nav>
    </div>
</header>

<main>

    <!-- HERO -->
    <section class="hero" id="hero">
        <div class="hero-bg" aria-hidden="true"></div>
        <div class="container">
            <div class="hero-content">
                <div class="hero-collab-logos">
                    <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                         alt="Al Omran Training &amp; Development Center" class="collab-logo" width="180" height="45">
                    <span class="collab-x">×</span>
                    <img src="/alomran_initiative/static/src/img/ewd-logo.png"
                         alt="Emirati Women’s Day" class="collab-logo collab-logo--partner" width="60" height="60">
                </div>
                <div class="hero-badge">
                    <svg class="icon" width="20" height="20" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    <span>Empowering Emirati women on Emirati Women’s Day</span>
                </div>
                <h1 class="hero-title">Al Omran Initiative for Empowering Emirati Women</h1>
                <p class="hero-subtitle">AED 5 million to support Emirati women’s education</p>
                <div class="hero-copy">
                    <p>On the occasion of Emirati Women’s Day, Al Omran Training &amp; Development Center
                       launches a community initiative worth AED 5,000,000, offering a free learning
                       opportunity to 500 Emirati women to study English for a full year.</p>
                    <p class="hero-statement">Because empowering women begins with education, and because the ambition
                       of Emirati women deserves someone to support it.</p>
                </div>
                <div class="hero-actions">
                    <a href="#apply" class="btn btn-primary">Apply Now</a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-image-frame">
                    <img src="/alomran_initiative/static/src/img/emirati-woman.jpg"
                         alt="An Emirati woman in a learning environment" loading="eager" width="800" height="600">
                </div>
                <div class="hero-image-badge">
                    <span class="badge-number">500</span>
                    <span class="badge-text">Learning Opportunities</span>
                </div>
            </div>
        </div>
    </section>

    <!-- VIDEO SECTION -->
    <section class="video-section">
        <div class="container">
            <div class="video-wrapper">
                <video autoplay muted loop playsinline id="heroVideo" width="1280" height="720">
                    <source src="/alomran_initiative/static/src/img/hero-video.mp4" type="video/mp4">
                    Your browser does not support video playback.
                </video>
                <button class="video-sound-btn" id="soundToggle" aria-label="Toggle sound">
                    <svg class="icon-sound-on" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                    <svg class="icon-sound-off" width="24" height="24" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2" style="display:none">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <line x1="23" y1="9" x2="17" y2="15"></line>
                        <line x1="17" y1="9" x2="23" y2="15"></line>
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
                    <div class="stat-number">5,000,000</div>
                    <div class="stat-label">AED initiative value</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg></div>
                    <div class="stat-number">500</div>
                    <div class="stat-label">Emirati women</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
                    <div class="stat-number">1 Full Year</div>
                    <div class="stat-label">of learning</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <div class="stat-number">Free</div>
                    <div class="stat-label">English language study</div>
                </div>
            </div>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="features" id="provide">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">What do we offer you?</h2>
                <p class="section-subtitle">A full year of free English language learning</p>
                <p class="section-intro">Through the initiative, every accepted beneficiary will receive:</p>
            </div>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg></div>
                    <h3 class="feature-title">A Full Academic Year</h3>
                    <p class="feature-text">A full academic year to learn and develop English language skills.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
                    <h3 class="feature-title">Stronger Communication Skills</h3>
                    <p class="feature-text">Develop your communication skills through speaking, listening, reading and writing practice.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div>
                    <h3 class="feature-title">In-Person Classes</h3>
                    <p class="feature-text">In-person classes at one of Al Omran’s branches across the UAE.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                    <h3 class="feature-title">No Tuition Fees</h3>
                    <p class="feature-text">The initiative covers the full program cost for accepted beneficiaries.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- WHY -->
    <section class="why" id="why">
        <div class="container">
            <div class="section-header"><h2 class="section-title">Why did we launch this initiative?</h2></div>
            <div class="why-content">
                <div class="why-text">
                    <p>At Al Omran, we believe the real investment is investing in people.</p>
                    <p>Emirati women have always been key partners in the journey of development and success.</p>
                    <p>That is why, on Emirati Women’s Day, we wanted to offer an initiative with a practical and lasting impact.</p>
                </div>
                <div class="why-stats">
                    <div class="why-stat"><div class="why-stat-number">AED 5 Million</div><div class="why-stat-label">in education</div></div>
                    <div class="why-stat"><div class="why-stat-number">500 Opportunities</div><div class="why-stat-label">for real learning</div></div>
                    <div class="why-stat"><div class="why-stat-number">500 Success Stories</div><div class="why-stat-label">in the making</div></div>
                </div>
            </div>
        </div>
    </section>

    <!-- REQUIREMENTS -->
    <section class="requirements" id="requirements">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">Who can apply?</h2>
                <p class="section-intro">The initiative is open to Emirati women who meet the following criteria:</p>
            </div>
            <div class="requirements-list">
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>The applicant must be an Emirati woman.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Aged 18 years or older.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Available for 1.5 hours, three days a week.</p></div>
                <div class="requirement-item"><div class="requirement-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div><p>Serious and able to commit to attending throughout the program.</p></div>
            </div>
            <div class="requirements-cta">
                <p>If you are ready to invest your time in yourself and your future, this opportunity is for you.</p>
                <a href="#apply" class="btn btn-primary">I want to apply</a>
            </div>
        </div>
    </section>

    <!-- SELECTION -->
    <section class="selection" id="selection">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">How are beneficiaries selected?</h2>
                <p class="section-intro">To achieve the greatest possible impact, not all applications will be accepted automatically.</p>
            </div>
            <div class="process-timeline">
                <div class="process-step"><div class="step-number">01</div><div class="step-content"><h3>Meeting the Initiative Criteria</h3><p>Verifying that the applicant meets all the required criteria.</p></div></div>
                <div class="process-step"><div class="step-number">02</div><div class="step-content"><h3>Application Priority</h3><p>Application order is taken into account in the selection process.</p></div></div>
                <div class="process-step"><div class="step-number">03</div><div class="step-content"><h3>Nominations from Women-Support Institutions</h3><p>The remaining seats will be filled through nominations from government institutions that support women.</p></div></div>
            </div>
            <div class="process-highlight">
                <p>Our ultimate goal: reaching 500 Emirati women and giving them a real opportunity to develop their English for a full year.</p>
            </div>
        </div>
    </section>

    <!-- LOCATIONS -->
    <section class="locations" id="locations">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">Where will classes take place?</h2>
                <p class="section-intro">Classes are available at Al Omran branches across the United Arab Emirates.</p>
                <p class="section-intro">When applying, you can choose the emirate and branch that suit you best. Accepted applicants will be contacted to complete registration.</p>
            </div>
            <div class="emirates-grid">
                {''.join([
                    f'<div class="emirate-chip">'
                    f'<svg class="chip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                    f'<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
                    f'<circle cx="12" cy="10" r="3"/></svg>'
                    f'<span>{e}</span></div>'
                    for e in ['Abu Dhabi','Dubai','Sharjah','Ajman','Umm Al Quwain','Ras Al Khaimah','Fujairah']
                ])}
            </div>
        </div>
    </section>

    <!-- EMOTIONAL CTA -->
    <section class="emotional-cta" id="emotional-cta">
        <div class="container">
            <div class="emotional-content">
                <h2 class="emotional-title">Are you ready to begin?</h2>
                <div class="emotional-text">
                    <p>An hour and a half, three days a week, may be the time you invest today,
                       but the skill can stay with you for years to come.</p>
                    <p>We don’t promise that English will change your life in a single day.</p>
                    <p class="emotional-highlight">But we promise you a real opportunity to start the change.</p>
                </div>
                <a href="#apply" class="btn btn-primary btn-large">Apply Now</a>
            </div>
        </div>
    </section>

    <!-- APPLICATION FORM -->
    <section class="application-form" id="apply">
        <div class="container">
            <div class="section-header">
                <h2 class="section-header__title">Apply to Participate</h2>
                <p class="section-header__subtitle">Fill in the details below and the initiative team will contact you</p>
            </div>
            {success_html if success else form_html}
        </div>
    </section>

    <!-- FINAL STATEMENT -->
    <section class="final-statement">
        <div class="container">
            <div class="statement-content">
                <div class="statement-amount">AED 5,000,000</div>
                <h2 class="statement-heading">Investing in people, celebrating Emirati women</h2>
                <div class="statement-brand">
                    <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                         alt="Al Omran" width="240" height="60">
                    <p class="statement-name">Al Omran Training &amp; Development Center</p>
                </div>
                <p class="statement-text">We believe education gives you more than a skill — it gives you a new opportunity.</p>
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
                <img src="/alomran_initiative/static/src/img/omran-full-logo.png"
                     alt="Al Omran Training &amp; Development Center" width="240" height="60">
                <p class="footer-name">Al Omran Training &amp; Development Center</p>
                <p class="footer-initiative">Community Initiative for Empowering Emirati Women</p>
            </div>
            <nav class="footer-nav" aria-label="Footer navigation">
                <ul class="footer-links">
                    <li><a href="#provide">What We Offer</a></li>
                    <li><a href="#requirements">Eligibility</a></li>
                    <li><a href="#selection">Selection</a></li>
                    <li><a href="#locations">Locations</a></li>
                    <li><a href="#apply">Apply</a></li>
                </ul>
            </nav>
            <div class="footer-legal">
                <a href="#" class="footer-legal-link">Privacy Policy</a>
                <a href="#" class="footer-legal-link">Terms &amp; Conditions</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 Al Omran Training &amp; Development Center. All rights reserved.</p>
        </div>
    </div>
</footer>

<!-- Popup -->
<div id="initiative-popup" style="
    display:none;position:fixed;inset:0;
    background:rgba(0,0,0,0.6);z-index:9999;
    align-items:center;justify-content:center;">
    <div style="
        background:#fff;border-radius:20px;padding:2.5rem;
        max-width:480px;width:90%;text-align:center;
        font-family:Inter,sans-serif;direction:ltr;
        box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:popupIn 0.3s ease;">
        <div id="popup-icon" style="font-size:3.5rem;margin-bottom:1rem;"></div>
        <h3 id="popup-title" style="margin-bottom:0.75rem;font-size:1.3rem;"></h3>
        <p id="popup-msg" style="color:#555;margin-bottom:1.5rem;line-height:1.7;white-space:pre-line;"></p>
        <button onclick="closePopup()" style="
            background:linear-gradient(135deg,#406AB2,#60BB46);
            color:#fff;border:none;border-radius:50px;
            padding:0.75rem 2.5rem;font-size:1rem;
            font-family:Inter,sans-serif;cursor:pointer;">
            OK
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
<script src="/alomran_initiative/static/src/js/initiative.js"></script>
</body>
</html>'''

        response = Response(html, content_type='text/html;charset=utf-8')
        return _secure_headers(response)

    # website=True: الصفحة بتمشي مع نظام اللغة تبع Odoo
    #   /initiative     -> إنكليزي (اللغة الافتراضية)
    #   /ar/initiative  -> عربي
    @http.route('/initiative', type='http', auth='public', website=True, sitemap=True)
    def initiative_page(self, **kwargs):
        if _is_ar():
            return self._render_page()
        return self._render_page_en()

    # رابط مباشر للإنكليزي (مفيد للإعلانات): بيثبّت الإنكليزي بالكوكي
    # وبيحافظ على gclid وباقي الـ query string
    @http.route('/initiative/en', type='http', auth='public', website=False, sitemap=False)
    def initiative_page_en(self, **kwargs):
        target = PAGE_PATH
        qs = request.httprequest.query_string.decode('utf-8', 'ignore')
        if qs:
            target += '?' + qs
        return request.redirect('/website/lang/en?r=' + quote(target, safe=''), code=301)

    @http.route('/initiative/apply', type='http', auth='public', website=False, methods=['POST'], csrf=False)
    def initiative_apply(self, **post):
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
                _logger.info('Initiative: honeypot triggered (ip=%s)', ip)
                return _ok()

            # توكن موقّع بوقت فتح الصفحة
            token_state = _check_form_token(post.get('_ft'))
            if token_state == 'too_fast':
                _logger.info('Initiative: submission too fast (ip=%s)', ip)
                return _ok()
            if token_state != 'ok':
                return _fail(msg['expired'], 400)

            # Rate limit حسب الـ IP
            if _rate_limited(ip):
                _logger.warning('Initiative: rate limit hit (ip=%s)', ip)
                return _fail(msg['rate_limited'], 429)

            # Sanitization
            full_name   = _sanitize(post.get('fullName'), 100)
            emirates_id = _sanitize(post.get('emiratesId'), 20)
            phone       = _sanitize(post.get('phone'), 15)
            email       = _sanitize(post.get('email'), 150)
            branch      = _sanitize(post.get('branch'), 100)
            english_lvl = _sanitize(post.get('englishLevel'), 20)
            reason      = _sanitize(post.get('reason'), 1000, multiline=True)
            time_commit = _sanitize(post.get('timeCommitment'), 3)
            full_prog   = _sanitize(post.get('fullProgram'), 3)

            if not all([full_name, emirates_id, phone, email, branch, english_lvl, reason]):
                return _fail(msg['required'])
            if english_lvl not in ENGLISH_LEVELS:
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
                "مبادرة المرأة الإماراتية - طلب مشاركة\n"
                "=======================================\n"
                f"الاسم الكامل:       {full_name}\n"
                f"رقم الهوية:         {emirates_id_clean}\n"
                f"الهاتف:             {phone_clean}\n"
                f"البريد الإلكتروني:  {email}\n"
                f"الفرع المفضل:       {branch}\n"
                f"مستوى اللغة:        {english_lvl}\n"
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
                'name': f'مبادرة المرأة - {full_name}',
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
            _logger.info('Initiative lead created: id=%s branch=%s lang=%s', lead.id, branch, lang)
            return _ok(lead_event_id(lead))

        except Exception:
            _logger.exception('Initiative apply error (ip=%s)', ip)
            return _fail(msg['generic'], 500)
