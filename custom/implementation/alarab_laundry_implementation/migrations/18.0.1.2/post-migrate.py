"""Remove the XML indentation that ended up inside the two WhatsApp templates' text."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in ("alarab_laundry_implementation.whatsapp_pos_ready_template",
                  "alarab_laundry_implementation.whatsapp_invoice_template_v2"):
        template = env.ref(xmlid, raise_if_not_found=False)
        if template and template.message:
            cleaned = "\n".join(line.strip() for line in template.message.strip().splitlines())
            if cleaned != template.message:
                template.message = cleaned
