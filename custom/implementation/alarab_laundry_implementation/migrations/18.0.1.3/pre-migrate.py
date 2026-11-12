"""Meta Cloud API sending was removed.

Delete its views before the new data is loaded: they show fields that no longer exist,
and Odoo would fail validating any other view of the same models (e.g. the invoice list).
"""
OBSOLETE_VIEWS = (
    "view_move_form_inherit_whatsapp",
    "view_out_invoice_tree_inherit_whatsapp",
    "res_config_settings_view_form_whatsapp",
)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'alarab_laundry_implementation'
           AND model = 'ir.ui.view' AND name IN %s
    """, [OBSOLETE_VIEWS])
    view_ids = tuple(r[0] for r in cr.fetchall())
    if view_ids:
        cr.execute("DELETE FROM ir_ui_view WHERE id IN %s", [view_ids])
        cr.execute("""
            DELETE FROM ir_model_data
             WHERE module = 'alarab_laundry_implementation'
               AND model = 'ir.ui.view' AND name IN %s
        """, [OBSOLETE_VIEWS])
