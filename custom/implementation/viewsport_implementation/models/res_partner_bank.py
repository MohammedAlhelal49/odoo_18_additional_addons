from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    vs_account_no = fields.Char(string='Account No.', help='Local account number printed beside the IBAN.')
    vs_account_class = fields.Char(string='Account Class', help='e.g. "AED - Business one C/A"')

    def _vs_iban_display(self):
        """UAE IBAN as written on the Viewsport templates: AE - 34 - 050 - 0000000017105312."""
        self.ensure_one()
        number = self.sanitized_acc_number or ''
        if number.startswith('AE') and len(number) == 23:
            return '%s - %s - %s - %s' % (number[:2], number[2:4], number[4:7], number[7:])
        return self.acc_number
