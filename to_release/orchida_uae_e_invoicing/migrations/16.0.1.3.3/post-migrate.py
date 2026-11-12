from odoo import SUPERUSER_ID, api

from odoo.addons.orchida_uae_e_invoicing.services.submission_client import classify_failure


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    for move in env['account.move'].search([
        ('move_type', '=', 'out_refund'),
        ('reversed_entry_id', '!=', False),
        ('orchida_original_invoice_id', '=', False),
    ]):
        move.orchida_original_invoice_id = move.reversed_entry_id

    for attempt in env['api.sent.invoice'].search([
        ('success', '=', True),
        ('outcome', '!=', 'valid'),
    ]):
        attempt.write({'outcome': 'valid', 'failure_type': False})

    for attempt in env['api.sent.invoice'].search([
        ('failure_type', '=', False),
        ('outcome', '!=', 'valid'),
    ]):
        attempt.failure_type = classify_failure({
            'outcome': attempt.outcome,
            'http_status': attempt.http_status,
            'error_message': attempt.response or attempt.status_response,
        })
