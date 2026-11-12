from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    moves = env['account.move'].search([])
    moves._compute_orchida_is_export()
