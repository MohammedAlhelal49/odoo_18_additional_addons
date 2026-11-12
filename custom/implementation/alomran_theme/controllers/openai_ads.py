# -*- coding: utf-8 -*-
"""
ChatGPT Ads (OpenAI) — Pixel + Conversions API
===============================================
System Parameters (Settings > Technical > System Parameters):
    alomran.openai_pixel_id     Pixel ID (الافتراضي: Hq3DiNGCoatRs8hZmvdVuz)
    alomran.openai_capi_key     مفتاح الـ Conversions API — إذا فاضي، السيرفر ما بيبعت شي
    alomran.openai_pixel_debug  True / False — لوغ الـ Pixel بـ console المتصفح

حملة الإنجليزي (Pixel منفصل — صفحة /english-ielts وليداتها بس):
    alomran.openai_english_pixel_id   (الافتراضي: Bn3JpbQDUJ8nmWfxbrKYht)
    alomran.openai_english_capi_key   مفتاح CAPI لـ Pixel الإنجليزي — إذا فاضي
                                       منجرب المفتاح العام alomran.openai_capi_key

حملة الدروس الخصوصية (/private-tutoring) — اختياري:
    alomran.openai_tutoring_pixel_id   إذا فاضي، الصفحة وليداتها على Pixel الموقع العام
    alomran.openai_tutoring_capi_key   إذا فاضي منجرب المفتاح العام

حملة دورات السيدات (/women-courses) — اختياري:
    alomran.openai_women_pixel_id      إذا فاضي، الصفحة وليداتها على Pixel الموقع العام
    alomran.openai_women_capi_key      إذا فاضي منجرب المفتاح العام

نفس الـ event_id (lead_<id>) بينبعت من المتصفح ومن السيرفر،
وOpenAI بتحسب الحدث مرة وحدة (Pixel ID + event name + event_id).

ما بينبعت أي بيانات شخصية: بس oppref (معرّف النقرة على الإعلان)
و obref (معرّف متصفح عشوائي بيعمله الـ Pixel نفسه).
"""
import json
import logging
import threading
import time
from urllib.parse import urlsplit, urlunsplit

import requests

from odoo.http import request

_logger = logging.getLogger(__name__)

DEFAULT_PIXEL_ID = 'Hq3DiNGCoatRs8hZmvdVuz'
ENGLISH_PIXEL_ID = 'Bn3JpbQDUJ8nmWfxbrKYht'

# كل Pixel: (param الـ ID، الافتراضي، param مفتاح CAPI)
PIXELS = {
    'default': ('alomran.openai_pixel_id', DEFAULT_PIXEL_ID, 'alomran.openai_capi_key'),
    'english': ('alomran.openai_english_pixel_id', ENGLISH_PIXEL_ID, 'alomran.openai_english_capi_key'),
    # صفحة الدروس الخصوصية: بلا Pixel افتراضي — إذا ما انعرّف بتستخدم Pixel الموقع العام
    'tutoring': ('alomran.openai_tutoring_pixel_id', '', 'alomran.openai_tutoring_capi_key'),
    'women': ('alomran.openai_women_pixel_id', '', 'alomran.openai_women_capi_key'),
    'saudi': ('alomran.openai_saudi_pixel_id', '', 'alomran.openai_saudi_capi_key'),
}
CAPI_URL = 'https://bzr.openai.com/v1/events'
CAPI_TIMEOUT = 5
PIXEL_SDK_URL = 'https://bzrcdn.openai.com/sdk/oaiq.min.js'


def _param(key, default=''):
    value = request.env['ir.config_parameter'].sudo().get_param(key, default)
    return (value or default or '').strip()


def pixel_id(pixel='default'):
    id_param, default, _key_param = PIXELS.get(pixel, PIXELS['default'])
    return _param(id_param, default)


def capi_key(pixel='default'):
    _id_param, _default, key_param = PIXELS.get(pixel, PIXELS['default'])
    return _param(key_param) or _param(PIXELS['default'][2])


def pixel_debug():
    return _param('alomran.openai_pixel_debug', 'False').lower() in ('true', '1', 'yes')


def lead_event_id(lead):
    return f'lead_{lead.id}'


def pixel_head_snippet():
    """كود الـ Pixel للصفحات اللي ما بتستخدم website.layout."""
    pid = pixel_id()
    if not pid:
        return ''
    init = json.dumps({'pixelId': pid, 'debug': pixel_debug()})
    return (
        '<script>'
        '!function(w,d,s,u){if(w.oaiq)return;var q=function(){q.q.push(arguments)};q.q=[];w.oaiq=q;'
        'var j=d.createElement(s);j.async=1;j.src=u;var f=d.getElementsByTagName(s)[0];'
        f'f.parentNode.insertBefore(j,f)}}(window,document,"script","{PIXEL_SDK_URL}");'
        f'oaiq("init",{init});'
        'window.alomranTrackLead=function(eventId){if(!eventId||!window.oaiq)return;'
        'try{oaiq("measure","lead_created",{type:"customer_action"},{event_id:String(eventId)});}catch(e){}};'
        '</script>'
    )


def pixel_lead_script(event_id):
    """استدعاء حدث lead_created بصفحة نجاح (إرسال فورم عادي بدون AJAX)."""
    if not event_id:
        return ''
    return (
        '<script>if(window.alomranTrackLead){window.alomranTrackLead('
        + json.dumps(str(event_id)) + ');}</script>'
    )


def _source_url():
    # الدومين من طلبنا نحن (مش من الـ Referer)، والمسار من الصفحة اللي انبعت منها الفورم
    base = urlsplit(request.httprequest.url_root)
    ref = urlsplit(request.httprequest.referrer or '')
    path = ref.path if ref.netloc == base.netloc and ref.path else '/'
    return urlunsplit((base.scheme, base.netloc, path, '', ''))


def send_lead_created(lead, pixel='default'):
    """يبعت lead_created للـ Conversions API بعد الـ commit، بخيط منفصل.
    pixel: 'default' للموقع، 'english' لصفحة حملة الإنجليزي.
    أي خطأ هون ما بيأثر على الفورم ولا على إنشاء الـ lead."""
    try:
        api_key = capi_key(pixel)
        pid = pixel_id(pixel)
        if not api_key or not pid:
            return

        cookies = request.httprequest.cookies
        event = {
            'id': lead_event_id(lead),
            'type': 'lead_created',
            'timestamp_ms': int(time.time() * 1000),
            'action_source': 'web',
            'source_url': _source_url(),
            'data': {'type': 'customer_action'},
        }
        # الـ Pixel بيحفظ oppref بكوكي __oppref — منبعته متل ما هو بدون تعديل
        oppref = cookies.get('__oppref') or request.httprequest.args.get('oppref')
        if oppref and oppref.strip() and len(oppref) <= 1024:
            event['oppref'] = oppref.strip()
        # obref: معرّف متصفح عشوائي من الـ Pixel، لربط حدث السيرفر بحدث المتصفح
        obref = cookies.get('__obref')
        if obref and obref.strip() and len(obref) <= 256:
            event['user'] = {'obref': obref.strip()}

        body = json.dumps({'events': [event]})
        event_id = event['id']
    except Exception:
        _logger.exception('OpenAI CAPI: failed to build event')
        return

    def _post():
        try:
            resp = requests.post(
                CAPI_URL,
                params={'pid': pid},
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                data=body,
                timeout=CAPI_TIMEOUT,
            )
            if resp.status_code >= 300:
                _logger.warning('OpenAI CAPI rejected %s (pixel %s): HTTP %s %s',
                                event_id, pid, resp.status_code, resp.text[:300])
            else:
                _logger.info('OpenAI CAPI sent %s (pixel %s)', event_id, pid)
        except Exception as e:
            _logger.warning('OpenAI CAPI error for %s (pixel %s): %s', event_id, pid, e)

    def _start():
        threading.Thread(target=_post, name='openai-capi', daemon=True).start()

    # بعد الـ commit بس: إذا الطلب فشل وانعمل rollback، ما منبعت حدث لـ lead مش موجود
    request.env.cr.postcommit.add(_start)