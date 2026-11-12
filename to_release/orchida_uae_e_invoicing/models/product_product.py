from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    orchida_standard_id = fields.Char(
        string='RCM Standard ID Fallback',
        help='Fallback GTIN used for RCM when the product barcode is empty.',
    )
    orchida_rcm_data_status = fields.Char(
        string='RCM Data Status',
        compute='_compute_orchida_rcm_data_status',
        readonly=True,
    )

    def _orchida_get_hs_code(self):
        self.ensure_one()
        return self.product_tmpl_id.orchida_hs_code

    def _orchida_get_sac_code(self):
        self.ensure_one()
        return self.product_tmpl_id.orchida_sac_code

    def _orchida_get_rcm_item_type(self):
        self.ensure_one()
        return self.product_tmpl_id.orchida_rcm_item_type

    @api.depends(
        'barcode',
        'orchida_standard_id',
        'product_tmpl_id.orchida_rcm_item_type',
        'product_tmpl_id.orchida_hs_code',
        'product_tmpl_id.orchida_sac_code',
    )
    def _compute_orchida_rcm_data_status(self):
        for product in self:
            item_type = product._orchida_get_rcm_item_type()
            missing = []
            if not (product.barcode or product.orchida_standard_id):
                missing.append('GTIN')
            if item_type in ('G', 'B') and not product._orchida_get_hs_code():
                missing.append('HS')
            if item_type in ('S', 'B') and not product._orchida_get_sac_code():
                missing.append('SAC')
            product.orchida_rcm_data_status = 'Ready' if not missing else 'Missing: ' + ', '.join(missing)
