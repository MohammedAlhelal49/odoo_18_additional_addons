from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Technical Proposal Dynamic Fields
    x_implementation_period = fields.Char(string="Implementation Period")
    x_training_period = fields.Char(string="Training Period")
    x_testing_period = fields.Char(string="Testing Period")
    x_hosting_payment = fields.Monetary(string="Hosting Payment")

    # Contract Dynamic Fields
    x_contract_date = fields.Date(
        string="Contract Date",
        default=fields.Date.context_today
    )
    x_documentary_cycle = fields.Char(
        string="Documentary Cycle",
        default="المبيعات، المشتريات، والمخازن"
    )
    x_minimum_documentary_cycle = fields.Char(
        string="Minimum Documentary Cycle",
    )
    x_maximum_documentary_cycle = fields.Char(
        string="Maximum Documentary Cycle",
    )
    x_target_company_name = fields.Char(
        string="System Company Name",
        help="Target company name for database setup"
    )
    x_number_of_trainees = fields.Integer(
        string="Number of trainees",
    )
    x_hosting_location = fields.Char(
        string="Hosting Location",
    )

    # Software Edition & Version Fields
    x_odoo_edition = fields.Selection(
        selection=[
            ('community', 'Odoo Community'),
            ('enterprise', 'Odoo Enterprise'),
        ],
        string="Odoo Edition",
        default='community',
        required=True
    )

    x_odoo_version = fields.Selection(
        selection=[
            ('20', 'Version 20'),
            ('19', 'Version 19'),
            ('18', 'Version 18'),
        ],
        string="Odoo Version",
        default='18',
        required=True
    )

    # Payment Schedule Customization
    x_down_payment_details = fields.Char(
        string="Down Payment Details",
        default="50% من إجمالي القيمة"
    )
    x_second_payment_details = fields.Char(
        string="Second Payment Details",
        default="50% بشيك مؤجل بعد شهر"
    )
    x_payment_method_text = fields.Char(
        string="Payment Method",
        default="تحويل بنكي / شيك / نقداً"
    )
    x_payment_period = fields.Char(
        string="Payment Period",
    )
    x_first_payment_period_limit = fields.Char(
        string="First Payment Period Limit",
    )

    # Signatures, Stamp & Brand PNG Placeholders
    x_daem_logo = fields.Image(string="First Party Logo (PNG)")
    x_daem_signature = fields.Image(string="First Party Signature (PNG)")
    x_daem_stamp = fields.Image(string="Company Stamp (PNG)")
