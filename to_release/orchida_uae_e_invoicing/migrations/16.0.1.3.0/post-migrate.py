import json

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.company'].search([]).write({'orchida_auto_submit_einvoice': True})

    attempts = env['api.sent.invoice'].search([])
    for attempt in attempts:
        tax_status = (attempt.orchida_tax_status or '').lower()
        receiver_status = (attempt.orchida_receiver_status or '').lower()
        valid = bool(attempt.success)
        unknown = not valid and (
            tax_status in ('', 'pending', 'unknown', 'submitted', 'accepted', 'cleared', 'reported')
            or receiver_status in ('', 'pending', 'unknown', 'submitted', 'accepted', 'cleared', 'reported')
        )
        try:
            response = json.loads(attempt.response or '{}')
        except (TypeError, ValueError):
            response = {}
        attempt.write({
            'outcome': 'valid' if valid else ('unknown' if unknown else 'failed'),
            'source': 'legacy',
            'internal_code': (attempt.move_name or '').replace('/', '-'),
            'api_uuid': response.get('UUID', '') if isinstance(response, dict) else '',
        })

    eligible_moves = env['account.move'].search([
        ('move_type', 'in', ('out_invoice', 'out_refund')),
        ('journal_id.orchida_submit_einvoice', '=', True),
    ])
    eligible_moves._compute_orchida_submission_state()
