from odoo import fields, models

from ..constants import UNCL5189_ALLOWANCE_CODES, UNCL7161_CHARGE_CODES


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    orchida_rcm_item_type = fields.Selection(
        [('G', 'Goods'), ('S', 'Services'), ('B', 'Goods and services')],
        string='RCM Commodity Type Override',
        help='Optional explicit RCM CommodityCode. If empty, services map to S and other products map to G.',
    )
    orchida_hs_code = fields.Char(string='RCM HS Code')
    orchida_hs_list_version = fields.Char(string='RCM HS List Version')
    orchida_sac_code = fields.Char(string='RCM SAC Code')
    orchida_sac_scheme_version = fields.Char(string='RCM SAC Scheme Version')
    orchida_doc_ac_reason_code = fields.Selection(
        UNCL5189_ALLOWANCE_CODES + UNCL7161_CHARGE_CODES,
        string='Orchida AC Reason Code',
        help='Document-level reason. UNCL 5189 for the default Allowance product, UNCL 7161 for the default Charge product. The reason text is derived from the code description.',
    )
