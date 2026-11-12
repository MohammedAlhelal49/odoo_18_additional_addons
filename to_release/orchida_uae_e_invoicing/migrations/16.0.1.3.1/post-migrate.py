import json

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    attempts = env['api.sent.invoice'].search([])
    transitional = {'', 'pending', 'unknown', 'submitted', 'accepted', 'cleared', 'reported'}
    for attempt in attempts:
        tax_status = (attempt.orchida_tax_status or '').lower()
        receiver_status = (attempt.orchida_receiver_status or '').lower()
        valid = attempt.outcome == 'valid' or bool(attempt.success)
        unknown = not valid and (tax_status in transitional or receiver_status in transitional)
        try:
            response = json.loads(attempt.response or '{}')
        except (TypeError, ValueError):
            response = {}
        attempt.write({
            'outcome': 'valid' if valid else ('unknown' if unknown else 'failed'),
            'internal_code': attempt.internal_code or (attempt.move_name or '').replace('/', '-'),
            'api_uuid': attempt.api_uuid or (
                response.get('UUID', '') if isinstance(response, dict) else ''
            ),
        })
    attempts.mapped('move_id')._compute_orchida_submission_state()
