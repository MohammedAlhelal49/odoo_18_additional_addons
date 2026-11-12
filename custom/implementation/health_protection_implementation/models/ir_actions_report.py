from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def hp_set_paperformat(self, report_names, paperformat_xmlid):
        """Set a paperformat on reports looked up by report_name (no error when a report's module is not installed)."""
        paperformat = self.env.ref(paperformat_xmlid)
        self.search([('report_name', 'in', report_names)]).write({'paperformat_id': paperformat.id})
        return True
