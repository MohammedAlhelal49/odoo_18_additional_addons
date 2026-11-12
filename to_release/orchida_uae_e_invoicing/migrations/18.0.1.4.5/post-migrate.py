from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['account.journal'].sudo().search([]).write({'orchida_submit_einvoice': True})
    # Work around Char->Selection upgrade bug (_process_ondelete
    # AttributeError 'Char' object has no attribute 'ondelete'): the stale
    # non-noupdate selection ir.model.data rows for cfg_buyer_agency_id are
    # reconciled during _process_end, which runs after this post-migrate.
    # Delete them here so _process_end has nothing to unlink.
    env['ir.model.data'].sudo().search([
        ('module', '=', 'orchida_uae_e_invoicing'),
        ('name', 'like', 'selection__res_partner__cfg_buyer_agency_id__%'),
    ]).unlink()
