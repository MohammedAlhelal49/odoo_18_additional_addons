import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


# Official UAE localization taxes (stable ir.model.data name suffix), mapped to
# their default Orchida PINT AE tax category. Resolved by XML name suffix because
# the numeric company prefix and owning module differ across Odoo versions
# (l10n_ae on 16, account on 17+). Only mapped when the category is unset.
DEFAULT_AE_TAX_CATEGORY_MAPPINGS = {
    # Standard rate 5% (each emirate)
    'uae_sale_tax_5_dubai': 'S',
    'uae_sale_tax_5_abu_dhabi': 'S',
    'uae_sale_tax_5_sharjah': 'S',
    'uae_sale_tax_5_ajman': 'S',
    'uae_sale_tax_5_umm_al_quwain': 'S',
    'uae_sale_tax_5_ras_al_khaima': 'S',
    'uae_sale_tax_5_fujairah': 'S',
    # Zero-rated supplies and exports
    'uae_sale_tax_0': 'Z',
    'uae_export_tax': 'Z',
    # Exempt supplies
    'uae_sale_tax_exempted': 'E',
    # Tourist refund scheme (5% standard)
    'uae_sale_tax_tourist_refund': 'S',
    # Reverse charge (each emirate on 16/17/18)
    'uae_sale_tax_reverse_charge_dubai': 'AE',
    'uae_sale_tax_reverse_charge_abu_dhabi': 'AE',
    'uae_sale_tax_reverse_charge_sharjah': 'AE',
    'uae_sale_tax_reverse_charge_ajman': 'AE',
    'uae_sale_tax_reverse_charge_umm_al_quwain': 'AE',
    'uae_sale_tax_reverse_charge_ras_al_khaima': 'AE',
    'uae_sale_tax_reverse_charge_fujairah': 'AE',
    # Purchases
    'uae_purchase_tax_5': 'S',
    'uae_purchase_tax_0': 'Z',
    'uae_purchase_tax_exempted': 'E',
    'uae_purchase_tax_reverse_charge': 'AE',
    'uae_import_tax': 'S',
    # v19 additions
    'uae_purchase_postponed_tax': 'S',
    'uae_out_of_scope': 'O',
}


AE_EXEMPTION_CODES = [
    ('DL8.46.1', 'DL8.46.1 - Certain financial services'),
    ('DL8.46.2', 'DL8.46.2 - Supply of residential units (lease or sale)'),
    ('DL8.46.3', 'DL8.46.3 - Bare land'),
    ('DL8.46.4', 'DL8.46.4 - Local passenger transport'),
]

AE_GOODS_TYPE_CODES = [
    ('DL8.48.8.1', 'DL8.48.8.1 - Gold and Diamonds'),
    ('DL8.48.8.2', 'DL8.48.8.2 - Electronic Devices'),
    ('DL8.48.3.1', 'DL8.48.3.1 - Crude or refined oil'),
    ('DL8.48.3.2', 'DL8.48.3.2 - Unprocessed or processed natural gas'),
    ('DL8.48.3.3', 'DL8.48.3.3 - Pure hydrocarbons'),
]

AETaxCat_CODES = [
    ('S', 'S - Standard rate'),
    ('E', 'E - Exempt from tax'),
    ('O', 'O - Services outside scope of tax'),
    ('AE', 'AE - VAT Reverse Charge'),
    ('Z', 'Z - Zero rated'),
    ('N', 'N - Standard rate additional VAT'),
]


class AccountTax(models.Model):
    _inherit = 'account.tax'

    orchida_tax_category = fields.Selection(
        AETaxCat_CODES,
        string='Orchida PINT AE Tax Category',
        help='UAE PINT AE VAT category code used for e-invoice line tax breakdown.',
    )
    orchida_exemption_code = fields.Selection(
        AE_EXEMPTION_CODES,
        string='Orchida Exemption Code',
        help='Required when tax category is "Exempt from tax" (E).',
    )
    orchida_rcm_goods_type = fields.Selection(
        AE_GOODS_TYPE_CODES,
        string='RCM NatureCode',
        help='Required when tax category is "VAT Reverse Charge" (AE).',
    )

    def seed_default_tax_categories(self):
        """Assign Orchida categories to official UAE localization taxes.

        Resolves the taxes through their stable ir.model.data name suffix so the
        mapping works regardless of the owning module (l10n_ae on Odoo 16,
        account on 17+) or the per-company numeric prefix. Only fills empty
        categories; existing mappings (customer or administrator) are preserved.
        Custom taxes are never touched.
        """
        model_data = self.env['ir.model.data'].sudo().search([
            ('model', '=', 'account.tax'),
        ])
        known_suffixes = set(DEFAULT_AE_TAX_CATEGORY_MAPPINGS)
        by_suffix = {}
        for record in model_data:
            name = record.name or ''
            # XML names carry a per-company numeric prefix, e.g. "2_uae_export_tax".
            if '_' in name:
                candidate = name.split('_', 1)[1]
            else:
                candidate = name
            if candidate in known_suffixes:
                by_suffix.setdefault(candidate, record)
        taxes_by_id = {}
        for suffix, category in DEFAULT_AE_TAX_CATEGORY_MAPPINGS.items():
            record = by_suffix.get(suffix)
            if record:
                taxes_by_id[record.res_id] = category
        if not taxes_by_id:
            _logger.info('No official UAE localization taxes found to map')
            return

        taxes = self.env['account.tax'].sudo().browse(taxes_by_id.keys()).exists()
        mapped = 0
        for tax in taxes:
            if tax.orchida_tax_category:
                continue
            tax.orchida_tax_category = taxes_by_id[tax.id]
            mapped += 1
        _logger.info(
            'Mapped %s/%s official UAE taxes to Orchida categories',
            mapped,
            len(taxes),
        )
