from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vs_dln_seq = fields.Char(string='Delivery Note No.', copy=False, readonly=True,
                             help='Number printed on the Viewsport delivery note, e.g. 2600001.')
    vs_do_seq = fields.Char(string='Delivery Order No.', copy=False, readonly=True,
                            help='Number printed on the Viewsport delivery order, e.g. 260001.')

    def _vs_number(self, field, code):
        """Number of the delivery note / order, taken from its own yearly sequence the first time it is printed."""
        self.ensure_one()
        if not self[field]:
            self.sudo()[field] = self.env['ir.sequence'].sudo().next_by_code(
                code, sequence_date=self.scheduled_date or fields.Datetime.now())
        return self[field]

    def _vs_dln_number(self):
        return self._vs_number('vs_dln_seq', 'viewsport.delivery.note')

    def _vs_do_number(self):
        return self._vs_number('vs_do_seq', 'viewsport.delivery.order')

    def _vs_sale_order(self):
        self.ensure_one()
        return self.sale_id if 'sale_id' in self._fields else self.env['sale.order']

    def _vs_project(self):
        """Project analytic account of the sales order lines (account from a 'Project' plan first)."""
        self.ensure_one()
        account_ids = set()
        for line in self._vs_sale_order().order_line:
            for key in (line.analytic_distribution or {}):
                account_ids.update(int(account_id) for account_id in key.split(','))
        accounts = self.env['account.analytic.account'].browse(sorted(account_ids)).exists()
        return (accounts.filtered(lambda a: 'project' in (a.plan_id.name or '').lower()) or accounts)[:1]

    def _vs_project_ref(self):
        project = self._vs_project()
        return project.custom_project_code or project.code or ''

    def _vs_customer_po_ref(self):
        """Customer purchase order number (reference written on the sales order)."""
        self.ensure_one()
        return self._vs_sale_order().client_order_ref or ''

    def _vs_invoice_refs(self):
        self.ensure_one()
        invoices = self._vs_sale_order().invoice_ids.filtered(lambda m: m.state == 'posted')
        return ', '.join(invoices.mapped('name'))

    def _vs_lines(self):
        """Moves printed on the delivery documents (cancelled moves left out)."""
        self.ensure_one()
        return self.move_ids.filtered(lambda m: m.state != 'cancel')
