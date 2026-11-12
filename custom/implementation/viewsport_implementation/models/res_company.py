import base64
import re

from markupsafe import Markup

from odoo import fields, models
from odoo.tools.misc import file_open

DEFAULT_FOOTER = (
    "Head office: Business Avenue Building - Port Saeed - Office # 606, Dubai, UAE\n"
    "هاتـف:042222015، فاكس: 042770170، صندوق بريد رقـم: 430406، دبـي - الإمـارات العربية المتحدة\n"
    "Tel: 04 222 2015, Fax: 04 277 0170, P.O. Box 430406 -Dubai - United Arab Emirates\n"
    "Email:info@fplandscape.com – web site:www.viewsportpitches.com"
)

# Terms 3 to 9 of the purchase order; {emirate} and {supplier} are replaced when printing.
DEFAULT_PO_TERMS = (
    "<p><strong>3-</strong> All information contained is this document is strictly confidential and must not be disclosed "
    "to any individual (s) or organisation other than those directly employed by the applicant / customer named overleaf. "
    "Sharing this information will lead to an immediate termination of the sale and / or partnership with "
    "<strong>Viewsport Pitches.</strong></p>"
    "<p><strong>4-</strong> All prices quoted included <strong>VAT</strong> which is charged at the Government rate at the date of invoice.</p>"
    "<p><strong>5-</strong> All prices are <strong>Ex - {emirate} - UAE</strong> 'Delivered to Site' cost is inclusive of shipping costs, "
    "RTA, pass, customs and taxes collection arrangements should be arranged and pay by the Vendor.</p>"
    "<p><strong>6- Viewsport Pitches</strong> does not accept any costs, or claims for consequential losses incurred by partners / Vendor, "
    "or their customers for late or delayed deliveries.</p>"
    "<p><strong>7- Viewsport Pitches</strong> under no circumstances accept consequential loss claims in any form.</p>"
    "<p>8- Shelf life for all products in this PO not less than one year from Delivery Date.</p>"
    "<p><strong>9-</strong> {supplier} (the supplier) responsibility to secure a copy of the maintenance instructions and training "
    "<strong>Viewsport Pitches team</strong> for all machinery.</p>"
)

DEFAULT_RFQ_TERMS = (
    "<p><strong>3-</strong> All prices quoted include VAT which is charged at the Government rate at the date of invoice.</p>"
)

# Terms 3 onwards of the sales quotation.
DEFAULT_QUOTATION_TERMS = (
    "<p><strong>3- Validity of Proposal:</strong><br/>Our proposal valid for a period of one month (30 calendar days from the "
    "above date) after date we reserve the right to re-quote if the works do not commence on site within 60 days of signing "
    "the contract.</p>"
    "<p><strong>4- All works mentioned the below is exclusions from VSP scope of work:</strong></p>"
    "<p>4.1- Any other items not mentioned in the BOQ.</p>"
    "<p>4.2- Removing the existing grass included waste materials.</p>"
    "<p>4.3- Substructure and civil works.</p>"
)

_ARABIC = re.compile('[؀-ۿ]')


def _default_report_logo():
    with file_open('viewsport_implementation/static/src/img/viewsport_logo.png', 'rb') as f:
        return base64.b64encode(f.read())


class ResCompany(models.Model):
    _inherit = 'res.company'

    procurement_manager_id = fields.Many2one('res.users', string='Procurement Manager')
    accountant_id = fields.Many2one('res.users', string='Accountant')

    vs_legal_name = fields.Char(string='Legal Name', default='VIEWSPORT PITCHES CONTRACTING L.L.C',
                                help='Printed on the tax invoice and in its bank details.')
    vs_short_legal_name = fields.Char(string='Short Legal Name', default='Viewsport Pitches Cont. L.L.C',
                                      help='Printed as "Deliver To" on the purchase order.')
    vs_report_logo = fields.Image(string='Report Logo', default=_default_report_logo, max_width=1024, max_height=512)
    vs_bill_from_dept = fields.Char(string='Bill From Department', default='Finance dept.')
    vs_bill_from_address = fields.Char(string='Bill From Address', default='P.O Box 430406 - Dubai - UAE')
    vs_bill_from_phone = fields.Char(string='Bill From Phone', default='0097142222015')
    vs_bill_from_email = fields.Char(string='Bill From Email', default='admin@fplandscape.com')
    vs_report_footer = fields.Text(string='Report Footer', default=DEFAULT_FOOTER,
                                   help='One line per row; lines written in Arabic are printed right-to-left.')
    vs_po_terms = fields.Html(string='Purchase Order Terms (3 onwards)', default=DEFAULT_PO_TERMS, sanitize=True,
                              help='Use {emirate} and {supplier}: they are replaced by the PO values when printing.')

    vs_quotation_terms = fields.Html(string='Quotation Terms (3 onwards)', default=DEFAULT_QUOTATION_TERMS, sanitize=True)
    vs_rfq_terms = fields.Html(string='RFQ Terms (3 onwards)', default=DEFAULT_RFQ_TERMS, sanitize=True)

    def _vs_footer_lines(self):
        """[(text, is_arabic)] for the report footer."""
        self.ensure_one()
        return [(line.strip(), bool(_ARABIC.search(line)))
                for line in (self.vs_report_footer or '').splitlines() if line.strip()]

    def _vs_po_terms(self, emirate, supplier):
        self.ensure_one()
        terms = self.vs_po_terms or Markup()
        return Markup(terms).replace('{emirate}', emirate or '').replace('{supplier}', supplier or '')
