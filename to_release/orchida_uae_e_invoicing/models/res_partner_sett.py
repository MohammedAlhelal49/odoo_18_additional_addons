from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    trn_tin = fields.Char(
        string="TRN/TIN",
        help="Buyer's VAT/tax identifier used for payload buyerTaxID (UAE TRN for VAT-registered buyers).",
    )
    buyer_endpoint_id = fields.Char(
        string="Endpoint ID",
        help="Buyer's electronic address (EndpointID) to which the invoice is delivered.",
    )

    cfg_buyer_scheme_id = fields.Char(
        string="Scheme ID",
        default="0235",
        help="Identification scheme for Endpoint ID (buyerSchemeID). Example: 0235 for UAE TRN.",
    )
    cfg_buyer_agency_id = fields.Selection(
        [
            ('TL', 'TL - Trade License'),
            ('EID', 'EID - Emirates ID'),
            ('PAS', 'PAS - Passport'),
            ('CD', 'CD - Cabinet Decision'),
        ],
        string="Agency ID",
        default="TL",
        help="Buyer legal registration identifier type (BTAE-16 / @schemeAgencyID). "
             "Per IBR-183-AE must be TL, EID, PAS, or CD.",
    )
    cfg_buyer_agency_name = fields.Char(
        string="Agency Name",
        default="Trade License issuing Authority",
        help="Authority or entity that issued the commercial registration identifier.",
    )
    cfg_buyer_tax_scheme = fields.Selection(
        [('VAT', 'VAT'), ('TIN', 'TIN'), ('OTHER', 'Other')],
        string="Buyer Tax Scheme",
        default='VAT',
        help="Tax scheme sent in the payload buyerType field. VAT for TRN-registered buyers, TIN for non-VAT buyers.",
    )

    orchida_payment_instruction = fields.Selection(
        [
            ('', 'Use normal company transfer'),
            ('cash', 'Cash'),
            ('credit_transfer', 'Bank transfer'),
        ],
        string="E-Invoice Payment Instruction Override",
        default='',
        help="Override the normal company bank-transfer instruction only when the customer pays in cash or requires a bank transfer.",
    )
