from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='res_company' AND column_name='orchida_connector_enabled'")
    if cr.fetchone():
        cr.execute("UPDATE res_company SET orchida_connector_enabled = TRUE WHERE orchida_connector_enabled IS NULL")
