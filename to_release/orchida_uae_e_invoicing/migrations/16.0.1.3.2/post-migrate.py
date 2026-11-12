from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    attempts = env['api.sent.invoice'].search([
        ('success', '=', True),
        ('outcome', '!=', 'valid'),
    ])
    attempts.write({'outcome': 'valid'})
    attempts.mapped('move_id')._compute_orchida_submission_state()
