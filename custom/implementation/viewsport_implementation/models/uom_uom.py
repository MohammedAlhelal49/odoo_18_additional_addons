from odoo import api, fields, models

DEFAULT_REPORT_NAMES = {
    'uom.product_uom_unit': 'EA',
    'uom.product_uom_meter': 'RM',
    'uom.uom_square_meter': 'M²',
    'uom.product_uom_cubic_meter': 'M³',
    'uom.product_uom_kgm': 'KG',
    'uom.product_uom_litre': 'Ltrs',
}


class UomUom(models.Model):
    _inherit = 'uom.uom'

    vs_report_name = fields.Char(string='Report Name', help='Name printed on the Viewsport reports, e.g. "EA" for Units.')

    def _vs_label(self):
        return (self[:1].vs_report_name or self[:1].name or '')

    @api.model
    def _vs_set_default_report_names(self):
        """Give the standard units the names used on the Viewsport templates (only when not set yet)."""
        for xmlid, label in DEFAULT_REPORT_NAMES.items():
            uom = self.env.ref(xmlid, raise_if_not_found=False)
            if uom and not uom.vs_report_name:
                uom.vs_report_name = label
