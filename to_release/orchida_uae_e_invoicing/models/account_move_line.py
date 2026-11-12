from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from ..constants import UNCL5189_ALLOWANCE_CODES, UNCL7161_CHARGE_CODES


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    mapped_unit_code = fields.Char(
        string='API UnitCode',
        compute='_compute_mapped_unit_code',
        help='Resolved API UnitCode for this line based on company + UoM mapping.',
    )

    # Document Allowance / Charge fields
    orchida_is_document_ac = fields.Boolean(
        string='Doc Allowance/Charge',
        default=False,
        help='When True, this line is treated as a document-level Allowance or Charge instead of a regular product line.',
    )
    orchida_ac_indicator = fields.Selection(
        [('allowance', 'Allowance'), ('charge', 'Charge')],
        string='A/C',
        help='Document-level Allowance (discount) or Charge (surcharge).',
    )
    orchida_allowance_reason_code = fields.Selection(
        UNCL5189_ALLOWANCE_CODES,
        string='Allowance Reason Code',
        help='Peppol UNCL 5189 reason code for document-level allowance.',
    )
    orchida_charge_reason_code = fields.Selection(
        UNCL7161_CHARGE_CODES,
        string='Charge Reason Code',
        help='Peppol UNCL 7161 reason code for document-level charge.',
    )
    # Kept as Selection to avoid Odoo 17 upgrade crash when converting to Char.
    # Computed from the type-specific fields below.
    orchida_ac_reason_code = fields.Selection(
        UNCL5189_ALLOWANCE_CODES + UNCL7161_CHARGE_CODES,
        string='AC Reason Code',
        compute='_compute_orchida_ac_reason_code',
        store=True,
        help='Effective reason code (UNCL 5189 for allowance, UNCL 7161 for charge).',
    )
    orchida_ac_reason = fields.Char(
        string='AC Reason',
        help='Free-text reason for the allowance or charge.',
    )
    orchida_ac_amount = fields.Float(
        string='AC Amount',
        digits=(16, 2),
        help='Positive amount for the document-level allowance or charge.',
    )

    # Line-level optional PINT fields
    orchida_line_note = fields.Char(
        string='E-Invoice Line Note',
        help='Optional note sent as IBT-127 on the invoice line.',
    )
    orchida_buyer_item_code = fields.Char(
        string='Buyer Item Code',
        help='Buyers item identifier sent as IBT-156.',
    )

    @api.depends('product_uom_id', 'move_id.company_id')
    def _compute_mapped_unit_code(self):
        company_ids = self.mapped('move_id.company_id').ids
        uom_ids = self.mapped('product_uom_id').ids

        mapping_by_key = {}
        if company_ids and uom_ids:
            mappings = self.env['orchida.uom.api.map'].search([
                ('company_id', 'in', company_ids),
                ('uom_id', 'in', uom_ids),
                ('active', '=', True),
            ])
            mapping_by_key = {
                (mapping.company_id.id, mapping.uom_id.id): mapping.unit_code_id.code
                for mapping in mappings
                if mapping.unit_code_id
            }

        for line in self:
            company_id = line.move_id.company_id.id if line.move_id.company_id else False
            uom_id = line.product_uom_id.id if line.product_uom_id else False
            line.mapped_unit_code = mapping_by_key.get((company_id, uom_id), '')

    @api.depends('orchida_ac_indicator', 'orchida_allowance_reason_code', 'orchida_charge_reason_code')
    def _compute_orchida_ac_reason_code(self):
        for line in self:
            if line.orchida_ac_indicator == 'allowance':
                line.orchida_ac_reason_code = line.orchida_allowance_reason_code or ''
            elif line.orchida_ac_indicator == 'charge':
                line.orchida_ac_reason_code = line.orchida_charge_reason_code or ''
            else:
                line.orchida_ac_reason_code = ''

    @api.onchange('orchida_ac_amount', 'orchida_ac_indicator')
    def _onchange_orchida_ac_amount(self):
        for line in self:
            if line.orchida_is_document_ac and line.orchida_ac_amount and line.orchida_ac_indicator:
                sign = -1 if line.orchida_ac_indicator == 'allowance' else 1
                line.price_unit = sign * line.orchida_ac_amount
                if not line.quantity:
                    line.quantity = 1.0

    @api.constrains('orchida_is_document_ac', 'orchida_ac_indicator', 'orchida_ac_amount',
                    'orchida_allowance_reason_code', 'orchida_charge_reason_code',
                    'orchida_ac_reason', 'tax_ids')
    def _check_orchida_document_ac(self):
        for line in self:
            if not line.orchida_is_document_ac:
                continue
            if not line.orchida_ac_indicator:
                raise ValidationError(_(
                    "Line '%(line)s': Document Allowance/Charge requires a type (Allowance or Charge).",
                    line=line.name or 'N/A',
                ))
            if line.orchida_ac_amount <= 0:
                raise ValidationError(_(
                    "Line '%(line)s': Document Allowance/Charge amount must be greater than zero.",
                    line=line.name or 'N/A',
                ))
            has_reason_code = (
                line.orchida_allowance_reason_code
                if line.orchida_ac_indicator == 'allowance'
                else line.orchida_charge_reason_code
            )
            if not has_reason_code and not line.orchida_ac_reason:
                raise ValidationError(_(
                    "Line '%(line)s': Document Allowance/Charge requires a Reason Code or a Reason.",
                    line=line.name or 'N/A',
                ))
            if not line.tax_ids:
                raise ValidationError(_(
                    "Line '%(line)s': Document Allowance/Charge requires at least one tax.",
                    line=line.name or 'N/A',
                ))

