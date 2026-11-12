import html
import re

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    dekad_tax_start_date = fields.Date(
        string='Tax Invoice Start Date',
        help='Invoices dated on or after this date are printed as "Tax Invoice". '
             'Earlier invoices, or all invoices when empty, are printed as "Sales Invoice".')

    dekad_trade_license = fields.Char(
        related='partner_id.dekad_trade_license', readonly=False, string='Trade Licence No.')
    dekad_legal_name = fields.Char(
        string='Legal Name (Contracts)',
        help='Full legal name printed as the first party of the implementation contract. Falls back to the company name.')
    dekad_brand_en = fields.Char(
        string='ERP Brand (English)',
        help='Brand of the ERP edition built on Odoo, printed in proposals and contracts, e.g. "Dekad" gives "Dekad ERP". Falls back to the first word of the company name.')
    dekad_brand_ar = fields.Char(
        string='ERP Brand (Arabic)',
        help='Arabic brand printed in the Arabic text, e.g. "ديكاد". Falls back to the English brand.')
    dekad_stamp = fields.Binary(string='Company Stamp', attachment=True)
    dekad_signatory_id = fields.Many2one(
        'res.users', string='Document Signatory',
        help='The signature of this user (User Signature in his preferences) is printed on the Technical Proposal.')

    def ct_brand(self, lang='en'):
        self.ensure_one()
        en = (self.dekad_brand_en or '').strip() or ((self.name or '').split() or [''])[0]
        return ((self.dekad_brand_ar or '').strip() or en) if lang == 'ar' else en

    def _ct_text_lines(self, value):
        text = re.sub(r'</(p|h\d|div|li)>|<br\s*/?>', '\n', str(value or ''))
        text = html.unescape(re.sub(r'<[^>]+>', '', text)).replace('\xa0', ' ')
        return [line.strip() for line in text.split('\n') if line.strip()]

    def ct_info(self):
        """Contract details of this company, read from what its documents already print:
        legal name and TRN from the header text, address from the company address fields (footer text only when they are empty)."""
        self.ensure_one()
        header = self._ct_text_lines(self.company_details)
        trn = ''
        name_parts = []
        for line in header:
            match = re.match(r'(?i)\s*(?:TRN|Tax Registration Number)\s*:?\s*(\S+)', line)
            if match:
                trn = match.group(1)
            else:
                name_parts.append(line)
        address = self.partner_id.ct_address()
        if not self.partner_id.street and not self.partner_id.city:
            address = next((line for line in self._ct_text_lines(self.report_footer)
                            if 'emirates' in line.lower() or 'uae' in line.lower()), address)
        return {
            'name': self.dekad_legal_name or ' '.join(name_parts) or self.name,
            'trn': self.vat or trn,
            'address': address,
        }

    def dekad_bar_color(self):
        """Color for voucher title bars: the company primary color, or the
        secondary one when the primary is too light for white text."""
        self.ensure_one()
        primary = self.primary_color or '#555555'
        try:
            h = primary.lstrip('#')
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        except ValueError:
            return primary
        if luminance > 0.55 and self.secondary_color:
            return self.secondary_color
        return primary
