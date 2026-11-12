from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    attempts = env['api.sent.invoice'].sudo().search([
        ('http_status', '=', 500),
        ('outcome', '=', 'valid'),
    ])
    attempts.write({
        'success': False,
        'outcome': 'failed',
        'failure_type': 'technical',
        'taxAuthStatus': 'invalid',
        'receiverStatus': 'invalid',
        'orchida_tax_status': 'invalid',
        'orchida_receiver_status': 'invalid',
    })
