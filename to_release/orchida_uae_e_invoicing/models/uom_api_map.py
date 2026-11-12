from odoo import api, fields, models


DEFAULT_UOM_MAPPINGS = (
    ('uom.product_uom_millimeter', 'orchida_uae_e_invoicing.orchida_unit_code_mmt'),
    ('uom.product_uom_gram', 'orchida_uae_e_invoicing.orchida_unit_code_grm'),
    ('uom.product_uom_cm', 'orchida_uae_e_invoicing.orchida_unit_code_cmt'),
    ('uom.product_uom_cubic_inch', 'orchida_uae_e_invoicing.orchida_unit_code_inq'),
    ('uom.product_uom_inch', 'orchida_uae_e_invoicing.orchida_unit_code_inh'),
    ('uom.product_uom_oz', 'orchida_uae_e_invoicing.orchida_unit_code_onz'),
    ('uom.product_uom_floz', 'orchida_uae_e_invoicing.orchida_unit_code_oza'),
    ('uom.uom_square_foot', 'orchida_uae_e_invoicing.orchida_unit_code_ftk'),
    ('uom.product_uom_hour', 'orchida_uae_e_invoicing.orchida_unit_code_hur'),
    ('uom.product_uom_foot', 'orchida_uae_e_invoicing.orchida_unit_code_fot'),
    ('uom.product_uom_lb', 'orchida_uae_e_invoicing.orchida_unit_code_lbr'),
    ('uom.product_uom_yard', 'orchida_uae_e_invoicing.orchida_unit_code_yrd'),
    ('uom.product_uom_qt', 'orchida_uae_e_invoicing.orchida_unit_code_qtl'),
    ('uom.product_uom_unit', 'orchida_uae_e_invoicing.orchida_unit_code_c62'),
    ('uom.product_uom_day', 'orchida_uae_e_invoicing.orchida_unit_code_day'),
    ('uom.product_uom_meter', 'orchida_uae_e_invoicing.orchida_unit_code_mtr'),
    ('uom.uom_square_meter', 'orchida_uae_e_invoicing.orchida_unit_code_mtk'),
    ('uom.product_uom_litre', 'orchida_uae_e_invoicing.orchida_unit_code_ltr'),
    ('uom.product_uom_kgm', 'orchida_uae_e_invoicing.orchida_unit_code_kgm'),
    ('uom.product_uom_gal', 'orchida_uae_e_invoicing.orchida_unit_code_gll'),
    ('uom.product_uom_cubic_foot', 'orchida_uae_e_invoicing.orchida_unit_code_ftq'),
    ('uom.product_uom_km', 'orchida_uae_e_invoicing.orchida_unit_code_kmt'),
    ('uom.product_uom_cubic_meter', 'orchida_uae_e_invoicing.orchida_unit_code_mtq'),
    ('uom.product_uom_ton', 'orchida_uae_e_invoicing.orchida_unit_code_tne'),
    ('uom.product_uom_mile', 'orchida_uae_e_invoicing.orchida_unit_code_smi'),
)


class OrchidaUomApiMap(models.Model):
    _name = 'orchida.uom.api.map'
    _description = 'Orchida UoM to API UnitCode Mapping'
    _order = 'company_id, uom_id'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        required=True,
        index=True,
        help='Odoo Unit of Measure to map into invoice line UnitCode.',
    )
    unit_code_id = fields.Many2one(
        'orchida.unit.code',
        string='API UnitCode',
        required=True,
        index=True,
        help='Select UN/ECE Rec 20 + Rec 21 unit code used for line UnitCode (for example: EA).',
    )
    active = fields.Boolean(default=True)

    @api.model
    def seed_default_mappings(self):
        mapping_model = self.sudo().with_context(active_test=False)
        defaults = [
            (self.env.ref(uom_ref).id, self.env.ref(unit_code_ref).id)
            for uom_ref, unit_code_ref in DEFAULT_UOM_MAPPINGS
        ]
        uom_ids = [uom_id for uom_id, _unit_code_id in defaults]
        for company in self.env['res.company'].sudo().search([]):
            existing_uom_ids = set(mapping_model.search([
                ('company_id', '=', company.id),
                ('uom_id', 'in', uom_ids),
            ]).mapped('uom_id').ids)
            mapping_model.create([
                {
                    'company_id': company.id,
                    'uom_id': uom_id,
                    'unit_code_id': unit_code_id,
                }
                for uom_id, unit_code_id in defaults
                if uom_id not in existing_uom_ids
            ])

    _sql_constraints = [
        ('uniq_company_uom_map', 'unique(company_id, uom_id)', 'A UnitCode mapping for this UoM already exists for this company.'),
    ]
