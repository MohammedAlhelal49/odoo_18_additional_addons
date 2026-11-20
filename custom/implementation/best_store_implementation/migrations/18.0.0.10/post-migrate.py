from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Cash difference notifications moved to dekad_pos_sale_enhancement, which has its
    # own template; this noupdate copy is not removed by the upgrade on its own.
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = env.ref('best_store_implementation.mail_template_cash_difference', raise_if_not_found=False)
    if template:
        template.unlink()
