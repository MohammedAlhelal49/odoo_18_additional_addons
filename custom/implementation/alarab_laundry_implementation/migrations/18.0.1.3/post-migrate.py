"""Meta Cloud API sending was removed.

- delete its settings, including the stored access token;
- delete its cron: it was loaded as noupdate, so Odoo would keep it and it would fail
  every run calling a method that no longer exists.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    cr.execute(r"""
        DELETE FROM ir_config_parameter
         WHERE key LIKE 'alarab\_laundry\_implementation.wa\_%%'
    """)
    env = api.Environment(cr, SUPERUSER_ID, {})
    cron = env.ref("alarab_laundry_implementation.cron_send_whatsapp_invoices", raise_if_not_found=False)
    if cron:
        cron.unlink()
