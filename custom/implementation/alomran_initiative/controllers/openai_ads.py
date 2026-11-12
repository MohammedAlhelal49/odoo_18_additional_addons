# -*- coding: utf-8 -*-
"""
ChatGPT Ads (OpenAI) — Pixel + Conversions API
===============================================
System Parameters (Settings > Technical > System Parameters):
    alomran.openai_pixel_id     Pixel ID (الافتراضي: Hq3DiNGCoatRs8hZmvdVuz)
    alomran.openai_capi_key     مفتاح الـ Conversions API — إذا فاضي، السيرفر ما بيبعت شي
    alomran.openai_pixel_debug  True / False — لوغ الـ Pixel بـ console المتصفح

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
CAPI_URL = 'https://bzr.openai.com/v1/events'
CAPI_TIMEOUT = 5
PIXEL_SDK_URL = 'https://bzrcdn.openai.com/sdk/oaiq.min.js'


def _param(key, default=''):
    value = request.env['ir.config_parameter'].sudo().get_param(key, default)
    return (value or default or '').strip()


def pixel_id():
    return _param('alomran.openai_pixel_id', DEFAULT_PIXEL_ID)


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


def send_lead_created(lead):
    """يبعت lead_created للـ Conversions API بعد الـ commit، بخيط منفصل.
    أي خطأ هون ما بيأثر على الفورم ولا على إنشاء الـ lead."""
    try:
        api_key = _param('alomran.openai_capi_key')
        pid = pixel_id()
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
                _logger.warning('OpenAI CAPI rejected %s: HTTP %s %s',
                                event_id, resp.status_code, resp.text[:300])
            else:
                _logger.info('OpenAI CAPI sent %s', event_id)
        except Exception as e:
            _logger.warning('OpenAI CAPI error for %s: %s', event_id, e)

    def _start():
        threading.Thread(target=_post, name='openai-capi', daemon=True).start()

    # بعد الـ commit بس: إذا الطلب فشل وانعمل rollback، ما منبعت حدث لـ lead مش موجود
    request.env.cr.postcommit.add(_start)
