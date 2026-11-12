from odoo import api, fields, models, _
from odoo.exceptions import UserError


UNCL5189_ALLOWANCE_CODES = [
    ('41', '41 - Bonus for works ahead of schedule'),
    ('42', '42 - Other bonus'),
    ('60', "60 - Manufacturer's consumer discount"),
    ('62', '62 - Due to military status'),
    ('63', '63 - Due to work accident'),
    ('64', '64 - Special agreement'),
    ('65', '65 - Production error discount'),
    ('66', '66 - New outlet discount'),
    ('67', '67 - Sample discount'),
    ('68', '68 - End-of-range discount'),
    ('70', '70 - Incoterm discount'),
    ('71', '71 - Point of sales threshold allowance'),
    ('88', '88 - Material surcharge/deduction'),
    ('95', '95 - Discount'),
    ('100', '100 - Special rebate'),
    ('102', '102 - Fixed long term'),
    ('103', '103 - Temporary'),
    ('104', '104 - Standard'),
    ('105', '105 - Yearly turnover'),
]

UNCL7161_CHARGE_CODES = [
    # Shipping & Logistics
    ('AAT', 'AAT - Rush delivery'),
    ('FC', 'FC - Freight service'),
    ('HD', 'HD - Handling'),
    ('LA', 'LA - Labelling'),
    ('LAA', 'LAA - Labour'),
    ('PC', 'PC - Packing'),
    ('PL', 'PL - Palletizing'),
    ('RAB', 'RAB - Repacking'),
    ('RV', 'RV - Loading'),
    ('SAA', 'SAA - Shipping and handling'),
    ('SAD', 'SAD - Special packaging'),
    ('SG', 'SG - Shrink-wrap'),
    ('SH', 'SH - Special handling'),
    ('SU', 'SU - Set-up'),
    ('TT', 'TT - Transportation - third party billing'),
    ('TV', 'TV - Transportation by vendor'),
    ('WH', 'WH - Warehousing'),
    # Services & Fees
    ('AAH', 'AAH - Additional processing'),
    ('ABF', 'ABF - Tooling'),
    ('ABK', 'ABK - Miscellaneous'),
    ('ABL', 'ABL - Additional packaging'),
    ('ABN', 'ABN - Dunnage'),
    ('ABR', 'ABR - Containerisation'),
    ('ABS', 'ABS - Carton packing'),
    ('ACF', 'ACF - Miscellaneous treatment'),
    ('ACG', 'ACG - Enamelling treatment'),
    ('ACH', 'ACH - Heat treatment'),
    ('ACI', 'ACI - Plating treatment'),
    ('ACJ', 'ACJ - Painting'),
    ('ACK', 'ACK - Polishing'),
    ('ACL', 'ACL - Priming'),
    ('ACM', 'ACM - Preservation treatment'),
    ('ACS', 'ACS - Fitting'),
    ('ADC', 'ADC - Consolidation'),
    ('ADE', 'ADE - Bill of lading'),
    ('ADT', 'ADT - Pick-up'),
    ('AEF', 'AEF - Rents and leases'),
    ('AEK', 'AEK - Cash on delivery'),
    ('AEM', 'AEM - Clerical or administrative services'),
    ('AEN', 'AEN - Guarantee'),
    ('AEO', 'AEO - Collection and recycling'),
    ('AJ', 'AJ - Adjustments'),
    ('AU', 'AU - Authentication'),
    ('CA', 'CA - Cataloguing'),
    ('CAB', 'CAB - Cartage'),
    ('CAD', 'CAD - Certification'),
    ('CAE', 'CAE - Certificate of conformance'),
    ('CAF', 'CAF - Certificate of origin'),
    ('CAI', 'CAI - Cutting'),
    ('CAJ', 'CAJ - Consular service'),
    ('CAK', 'CAK - Customer collection'),
    ('CG', 'CG - Cleaning'),
    ('CS', 'CS - Cigarette stamping'),
    ('CT', 'CT - Count and recount'),
    ('DL', 'DL - Delivery'),
    ('EG', 'EG - Engraving'),
    ('EP', 'EP - Expediting'),
    ('ER', 'ER - Exchange rate guarantee'),
    ('FAA', 'FAA - Fabrication'),
    ('FAB', 'FAB - Freight equalization'),
    ('FAC', 'FAC - Freight extraordinary handling'),
    ('FH', 'FH - Filling/handling'),
    ('FI', 'FI - Financing'),
    ('GAA', 'GAA - Grinding'),
    ('HH', 'HH - Hoisting and hauling'),
    ('IAA', 'IAA - Installation'),
    ('IAB', 'IAB - Installation and warranty'),
    ('ID', 'ID - Inside delivery'),
    ('IF', 'IF - Inspection'),
    ('IR', 'IR - Installation and training'),
    ('IS', 'IS - Invoicing'),
    ('LAB', 'LAB - Repair and return'),
    ('LF', 'LF - Legalisation'),
    ('MAE', 'MAE - Mounting'),
    ('MI', 'MI - Mail invoice'),
    ('ML', 'ML - Mail invoice to each location'),
    ('NAA', 'NAA - Non-returnable containers'),
    ('PA', 'PA - Invoice with shipment'),
    ('PAA', 'PAA - Phosphatizing (steel treatment)'),
    ('PRV', 'PRV - Price variation'),
    ('RAC', 'RAC - Repair'),
    ('RAD', 'RAD - Returnable container'),
    ('RAF', 'RAF - Restocking'),
    ('RE', 'RE - Re-delivery'),
    ('RF', 'RF - Refurbishing'),
    ('RH', 'RH - Rail wagon hire'),
    ('SA', 'SA - Salvaging'),
    ('SAE', 'SAE - Stamping'),
    ('SAI', 'SAI - Consignee unload'),
    ('SM', 'SM - Special finish'),
    ('TAB', 'TAB - Tank renting'),
    ('TAC', 'TAC - Testing'),
    ('V1', 'V1 - Drop yard'),
    ('V2', 'V2 - Drop dock'),
    ('XAA', 'XAA - Combine all same day shipment'),
    ('YY', 'YY - Split pick-up'),
    ('ZZZ', 'ZZZ - Mutually defined'),
]


class OrchidaDocumentAcWizard(models.TransientModel):
    _name = 'orchida.document.ac.wizard'
    _description = 'Document Allowance/Charge Wizard'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        ondelete='cascade',
    )
    indicator = fields.Selection(
        [('allowance', 'Allowance'), ('charge', 'Charge')],
        string='Type',
        required=True,
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        digits=(16, 2),
        help='Positive amount for the document-level allowance or charge.',
    )
    allowance_reason_code = fields.Selection(
        UNCL5189_ALLOWANCE_CODES,
        string='Allowance Reason Code',
    )
    charge_reason_code = fields.Selection(
        UNCL7161_CHARGE_CODES,
        string='Charge Reason Code',
    )
    reason = fields.Char(
        string='Reason',
        required=True,
    )
    tax_id = fields.Many2one(
        'account.tax',
        string='Tax',
        required=True,
        domain="[('type_tax_use', '=', 'sale')]",
        help='Tax applied to this allowance or charge line.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_id = self.env.context.get('default_move_id')
        if move_id and 'tax_id' in fields_list:
            move = self.env['account.move'].browse(move_id)
            company = move.company_id
            if company.account_sale_tax_id:
                res['tax_id'] = company.account_sale_tax_id.id
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.tax_id:
            raise UserError(_(
                "A tax is required for document allowances and charges."
            ))

        move = self.move_id
        if move.state not in ('draft', 'posted'):
            raise UserError(_(
                "You can only add allowance/charge lines to draft or posted invoices."
            ))

        product = move._get_or_create_orchida_doc_ac_product(self.indicator)
        if not product:
            raise UserError(_(
                "Could not find or create a default product for this document-level entry."
            ))

        allowance_reason = self.allowance_reason_code if self.indicator == 'allowance' else False
        charge_reason = self.charge_reason_code if self.indicator == 'charge' else False
        if not allowance_reason and not charge_reason:
            raise UserError(_(
                "A reason code is required for document %(type)s.",
                type=self.indicator,
            ))

        sign = -1 if self.indicator == 'allowance' else 1
        line_vals = {
            'move_id': move.id,
            'product_id': product.id,
            'quantity': 1.0,
            'price_unit': sign * self.amount,
            'name': self.reason or f"Document {self.indicator.title()}",
            'orchida_is_document_ac': True,
            'orchida_ac_indicator': self.indicator,
            'orchida_ac_amount': self.amount,
            'orchida_allowance_reason_code': allowance_reason,
            'orchida_charge_reason_code': charge_reason,
            'orchida_ac_reason': self.reason,
            'tax_ids': [(6, 0, self.tax_id.ids)] if self.tax_id else [(6, 0, [])],
        }
        self.env['account.move.line'].create(line_vals)
        return {'type': 'ir.actions.act_window_close'}
