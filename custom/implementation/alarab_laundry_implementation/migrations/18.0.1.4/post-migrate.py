"""Rename 'مغسلة' to 'مصبغة' in the WhatsApp templates.

They are loaded as noupdate, so the new XML text is not applied on update.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in ("alarab_laundry_implementation.whatsapp_pos_ready_template",
                  "alarab_laundry_implementation.whatsapp_invoice_template_v2"):
        template = env.ref(xmlid, raise_if_not_found=False)
        if template and template.message and "مغسلة" in template.message:
            template.message = template.message.replace("مغسلة", "مصبغة")
