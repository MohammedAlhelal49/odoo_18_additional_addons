"""Rename 'مغسلة' to 'مصبغة'.

- WhatsApp templates: loaded as noupdate, so the new XML text is not applied on update.
- Menu / action names: Odoo keeps existing translations on update, so the new
  ar_001.po values are not applied either.
"""
from odoo import SUPERUSER_ID, api

OLD, NEW = "مغسلة", "مصبغة"

TRANSLATED_NAMES = {
    "ir.ui.menu": "ir_ui_menu",
    "ir.actions.client": "ir_act_client",
    "ir.actions.act_window": "ir_act_window",
    "ir.actions.report": "ir_act_report_xml",
}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in ("alarab_laundry_dashboard.whatsapp_winback_template",
                  "alarab_laundry_dashboard.whatsapp_payment_reminder_template"):
        template = env.ref(xmlid, raise_if_not_found=False)
        if template and template.message and OLD in template.message:
            template.message = template.message.replace(OLD, NEW)

    for model, table in TRANSLATED_NAMES.items():
        cr.execute(f"""
            UPDATE {table} t
               SET name = replace(t.name::text, %s, %s)::jsonb
              FROM ir_model_data d
             WHERE d.module = 'alarab_laundry_dashboard'
               AND d.model = %s
               AND d.res_id = t.id
               AND t.name::text LIKE %s
        """, [OLD, NEW, model, f"%{OLD}%"])
