# -*- coding: utf-8 -*-
"""
ريدايركت لمرة وحدة لزوار السعودية → صفحة التعلم أونلاين (/saudi-online)
======================================================================
- أول زيارة لأي صفحة بالموقع من السعودية: 302 لـ /saudi-online + cookie.
- بعدها (أو إذا دخل /saudi-online مباشرة) ما في ريدايركت أبداً — بيتنقل بالموقع عادي.
- الدولة: هيدر Cloudflare (CF-IPCountry) إذا موجود، وإلا GeoIP تبع Odoo (request.geoip).
- ما بيشتغل على: البوتات (منشان SEO)، المستخدمين الداخليين، طلبات غير GET،
  الروابط اللي فيها gclid/utm (نقرات إعلانات على صفحة محددة).
- إيقاف/تشغيل: System Parameter alomran.saudi_geo_redirect = 0 / 1 (الافتراضي شغال).
"""
import logging

import werkzeug

from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)

SAUDI_URL = '/saudi-online'
COOKIE_NAME = 'alomran_sa_seen'
COOKIE_MAX_AGE = 365 * 24 * 3600   # سنة
_BOT_MARKERS = ('bot', 'crawl', 'spider', 'slurp', 'lighthouse', 'headless', 'facebookexternalhit',
                'whatsapp', 'telegram', 'preview')
_AD_PARAMS = ('gclid', 'gbraid', 'wbraid', 'fbclid', 'utm_source', 'utm_campaign')
# مسارات ما بتنحسب "زيارة صفحة"
_SKIP_PREFIXES = ('/web', '/odoo', '/website/', '/longpolling', '/websocket', '/mail/', '/my',
                  '/shop/cart', '/payment', '/robots.txt', '/sitemap', '/favicon', '/@')


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _frontend_pre_dispatch(cls):
        super()._frontend_pre_dispatch()
        try:
            cls._alomran_saudi_redirect()
        except werkzeug.exceptions.HTTPException:
            raise
        except Exception:
            # أي خطأ بالفحص ما لازم يوقف الموقع
            _logger.exception('Saudi geo redirect check failed')

    @classmethod
    def _alomran_country_code(cls):
        code = (request.httprequest.headers.get('CF-IPCountry') or '').strip().upper()
        if code:
            return code
        geoip = getattr(request, 'geoip', None)
        return ((geoip and geoip.country_code) or '').upper()

    @classmethod
    def _alomran_saudi_redirect(cls):
        httpreq = request.httprequest
        if httpreq.method != 'GET' or request.httprequest.cookies.get(COOKIE_NAME):
            return
        path = httpreq.path or '/'
        if path.startswith(_SKIP_PREFIXES) or '/static/' in path:
            return
        if (request.env['ir.config_parameter'].sudo()
                .get_param('alomran.saudi_geo_redirect', '1') or '1').strip() == '0':
            return
        # المستخدمين الداخليين (المحررين/الموظفين) ما بيتحولوا
        if not request.env.user._is_public():
            return
        ua = (httpreq.headers.get('User-Agent') or '').lower()
        if not ua or any(m in ua for m in _BOT_MARKERS):
            return
        # طلبات صفحات HTML بس
        if 'text/html' not in (httpreq.headers.get('Accept') or ''):
            return
        if any(p in httpreq.args for p in _AD_PARAMS):
            return
        if cls._alomran_country_code() != 'SA':
            return

        # من هون: زائر من السعودية لأول مرة
        on_saudi_page = path.rstrip('/').endswith(SAUDI_URL)
        if on_saudi_page:
            # فات على الصفحة مباشرة — منسجّل إنه شافها وما منحوّله أبداً
            request.future_response.set_cookie(COOKIE_NAME, '1', max_age=COOKIE_MAX_AGE,
                                               httponly=True, samesite='Lax', secure=httpreq.scheme == 'https')
            return

        try:
            target = cls._url_for(SAUDI_URL)   # بيحافظ على بادئة اللغة (/en/...)
        except Exception:
            target = SAUDI_URL
        response = request.redirect(target, code=302, local=True)
        response.set_cookie(COOKIE_NAME, '1', max_age=COOKIE_MAX_AGE,
                            httponly=True, samesite='Lax', secure=httpreq.scheme == 'https')
        # ما بيتخزن بأي كاش (الريدايركت خاص بالزائر)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Cookie, CF-IPCountry'
        werkzeug.exceptions.abort(response)
