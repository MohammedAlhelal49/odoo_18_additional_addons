from odoo import api, fields, models

from .purchase_order import amount_to_dirhams_text, vat_label


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_enclose = fields.Char(string='SO Enclose')
    so_no_of_pages = fields.Char(string='Quote of Pages')
    ship_to_info = fields.Text(string='Ship To')
    contact_person_id = fields.Many2one('res.partner', string='Contact Person')
    contact_number = fields.Char(string='Contact Number')
    qtn_seq = fields.Char(string='QTN No.', copy=False, readonly=True,
                          help='Quotation number as on the Viewsport template, e.g. VSPQT20260001.')
    qtn_revision = fields.Integer(string='QTN Revision', default=0, copy=False)
    implementation_period = fields.Char(
        string='Implementation Period',
        default='Not exceed forty five (45) Days after receipt of PO and down payment.')

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._vs_assign_qtn_seq()
        return orders

    def _vs_assign_qtn_seq(self):
        for order in self.filtered(lambda o: not o.qtn_seq):
            order.sudo().qtn_seq = self.env['ir.sequence'].sudo().next_by_code(
                'viewsport.quotation', sequence_date=order.date_order)

    def _get_qtn_number(self):
        """VSPQT20260001 -00: yearly counter followed by the revision."""
        self.ensure_one()
        self._vs_assign_qtn_seq()
        return '%s -%02d' % (self.qtn_seq, self.qtn_revision)

    def _get_project(self):
        """Project analytic account of the order lines (account from a 'Project' plan first)."""
        self.ensure_one()
        account_ids = set()
        for line in self.order_line:
            for key in (line.analytic_distribution or {}):
                account_ids.update(int(account_id) for account_id in key.split(','))
        accounts = self.env['account.analytic.account'].browse(sorted(account_ids)).exists()
        return (accounts.filtered(lambda a: 'project' in (a.plan_id.name or '').lower()) or accounts)[:1]

    def _get_attention(self):
        self.ensure_one()
        if self.contact_person_id:
            return self.contact_person_id.name
        return self.partner_id.name if self.partner_id.parent_id else ''

    def _get_quotation_rows(self):
        """[(number, line, kind)] as on the template: notes are 'Subject Line' rows, sections are numbered
        1.00, 2.00 ('Sub Subject Line') and the products below a section are numbered 1.1, 1.2..."""
        self.ensure_one()
        rows, section, item = [], 0, 0
        for line in self.order_line:
            if line.display_type == 'line_note':
                rows.append(('', line, 'subject'))
            elif line.display_type == 'line_section':
                section, item = section + 1, 0
                rows.append(('%.2f' % section, line, 'section'))
            elif section:
                item += 1
                rows.append(('%d.%d' % (section, item), line, 'product'))
            else:
                item += 1
                rows.append(('%.2f' % item, line, 'product'))
        return rows

    def _vs_vat_label(self):
        lines = self.order_line.filtered(lambda l: not l.display_type)
        return vat_label([l.tax_id for l in lines]) if lines else '5%'

    def _get_amount_in_words(self):
        self.ensure_one()
        if self.currency_id.name == 'AED':
            return amount_to_dirhams_text(self.amount_total)
        return self.currency_id.amount_to_text(self.amount_total)
