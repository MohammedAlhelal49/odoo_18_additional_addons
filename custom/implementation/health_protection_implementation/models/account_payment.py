from odoo import fields, models

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    hp_is_cheque = fields.Boolean(string='Paid by Cheque')
    hp_cheque_number = fields.Char(string='Cheque No.', copy=False)
    hp_cheque_bank = fields.Char(string='Cheque Bank', copy=False)
    hp_cheque_date = fields.Date(string='Cheque Date', copy=False)
    hp_cheque_due_date = fields.Date(string='Due Date', copy=False)

    def hp_amount_words(self, lang='en'):
        """Amount in words for the vouchers, English or Arabic."""
        self.ensure_one()
        amount = self.amount or 0.0
        currency = self.currency_id
        whole = int(amount)
        fils = int(round((amount - whole) * 100))
        if lang == 'ar':
            if not num2words:
                return ''
            name = 'درهم إماراتي' if currency.name == 'AED' else currency.name
            text = '%s %s' % (num2words(whole, lang='ar'), name)
            if fils:
                text += ' و%s فلس' % num2words(fils, lang='ar')
            return text + ' فقط لا غير'
        return currency.amount_to_text(amount) + ' Only'
