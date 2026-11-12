import json
import time

import requests

from .payload_mapper import build_submit_context


POST_TIMEOUT = 30
STATUS_TIMEOUT = 30
RETRY_DELAY = 1
TRANSITIONAL_STATUSES = {'pending', 'submitted', 'accepted', 'cleared', 'reported', 'processing'}


def _json_response(response):
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _response_text(response, data):
    return json.dumps(data, ensure_ascii=False) if data else (response.text or '')


def _failure_message(response, data):
    details = [f'HTTP status: {response.status_code}']
    if data.get('status'):
        details.append(f"API status: {data['status']}")
    if data.get('message'):
        details.append(str(data['message']))
    for error in data.get('errors') or []:
        if isinstance(error, dict) and error.get('message'):
            details.append(f"- {error['message']}")
    if len(details) == 1 and response.text:
        details.append(response.text[:2000])
    return '\n'.join(details)


def classify_failure(result):
    """Classify a failed attempt for the next user action."""
    if result.get('outcome') == 'unknown' or result.get('http_status', 0) >= 500:
        return 'technical'
    if result.get('http_status') in (401, 403) or any(
        marker in (result.get('error_message') or '').lower()
        for marker in ('base url', 'api token', 'company id', 'authorization', 'company-id')
    ):
        return 'configuration'
    return 'document'


def _is_transient_status(status_code):
    return status_code in (408, 429) or status_code >= 500


def check_status(company, internal_code):
    _, headers, _ = build_submit_context(company)
    url = f"{(company.orchida_base_url or '').rstrip('/')}/GetInvStatus"
    try:
        response = requests.get(
            url,
            headers=headers,
            params={'invoiceId': internal_code},
            timeout=STATUS_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        return {
            'state': 'unknown',
            'response_text': f'Status request error: {exc}',
        }

    data = _json_response(response)
    response_text = _response_text(response, data)
    if response.status_code == 404:
        return {'state': 'not_found', 'response_text': response_text}
    if response.status_code != 200:
        return {'state': 'unknown', 'response_text': response_text}

    invoices = data.get('invoices') if data else None
    if not isinstance(invoices, list):
        return {'state': 'unknown', 'response_text': response_text}
    invoice = next(
        (
            item for item in invoices
            if isinstance(item, dict) and item.get('invoiceId') == internal_code
        ),
        None,
    )
    if not invoice:
        return {'state': 'unknown', 'response_text': response_text}

    status = str(invoice.get('status') or '')
    state = 'valid' if status == 'valid' else (
        'failed' if status in ('invalid', 'rejected', 'error') else 'unknown'
    )
    return {
        'state': state,
        'response_text': response_text,
        'tax_status': invoice.get('taxAuthStatus') or status or 'unknown',
        'receiver_status': invoice.get('receiverStatus') or status or 'unknown',
    }


def _initial_result(payload):
    return {
        'success': False,
        'outcome': 'failed',
        'response_text': '',
        'status_response': '',
        'tax_status': 'invalid',
        'receiver_status': 'invalid',
        'error_message': '',
        'http_status': 0,
        'attempt_count': 0,
        'internal_code': str(payload.get('internalCode') or ''),
        'request_payload': json.dumps(payload, ensure_ascii=False),
        'api_uuid': '',
    }


def _post_once(company, payload, result):
    url, headers, params = build_submit_context(company)
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            params=params,
            timeout=POST_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        message = f'API request error: {exc}'
        result.update(
            outcome='unknown',
            response_text=message,
            error_message=message,
        )
        return True

    data = _json_response(response)
    status = str(data.get('status') or '')
    response_code = data.get('invInternalCode')
    code_matches = not response_code or response_code == result['internal_code']
    success = response.status_code in (200, 201) and status == 'valid' and code_matches
    result.update(
        success=success,
        outcome='valid' if success else (
            'unknown' if status.lower() in TRANSITIONAL_STATUSES else 'failed'
        ),
        response_text=_response_text(response, data),
        tax_status='valid' if success else status or 'invalid',
        receiver_status='valid' if success else status or 'invalid',
        error_message='' if success else _failure_message(response, data),
        http_status=response.status_code,
        api_uuid=str(data.get('UUID') or ''),
    )
    return not success and _is_transient_status(response.status_code)


def submit_payload(company, payload):
    result = _initial_result(payload)
    for attempt in range(1, 3):
        result['attempt_count'] = attempt
        transient = _post_once(company, payload, result)
        if result['success']:
            return result
        if result['http_status'] == 500:
            # A 500 is not a confirmed invoice state; leave it failed for user retry.
            result.update(
                outcome='failed',
                tax_status='invalid',
                receiver_status='invalid',
            )
            return result

        if result['outcome'] != 'unknown' and not transient:
            return result

        status = check_status(company, result['internal_code'])
        result['status_response'] = status['response_text']
        if status['state'] == 'valid':
            result.update(
                success=True,
                outcome='valid',
                tax_status=status['tax_status'],
                receiver_status=status['receiver_status'],
                error_message='',
            )
            return result
        if status['state'] != 'not_found':
            result['outcome'] = status['state']
            if status['state'] == 'failed':
                result.update(
                    tax_status=status['tax_status'],
                    receiver_status=status['receiver_status'],
                )
            result['error_message'] = status['response_text'] or result['error_message']
            return result
        if attempt == 2:
            result['outcome'] = 'unknown'
            return result
        time.sleep(RETRY_DELAY)
    return result
