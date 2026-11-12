from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        self.env['orchida.uom.api.map'].sudo().seed_default_mappings()
        return companies

    trn_tin = fields.Char(
        string="TRN/TIN",
        help="Seller VAT/tax identifier used for payload CompanyTaxID.",
    )

    orchida_connector_enabled = fields.Boolean(
        string="Enable Orchida E-Invoicing",
        default=True,
        help="Master switch for this company. When disabled, the connector does nothing: no validation, no submission, no cron jobs, and the normal Odoo accounting flow is unchanged. Submission history remains visible read-only.",
    )



    # Document Allowance / Charge default products
    orchida_doc_allowance_product_id = fields.Many2one(
        'product.product',
        string='Default Allowance Product',
        domain=[('type', '=', 'service')],
        help='Default product used when adding a document-level allowance line to an invoice.',
    )
    orchida_doc_charge_product_id = fields.Many2one(
        'product.product',
        string='Default Charge Product',
        domain=[('type', '=', 'service')],
        help='Default product used when adding a document-level charge line to an invoice.',
    )
