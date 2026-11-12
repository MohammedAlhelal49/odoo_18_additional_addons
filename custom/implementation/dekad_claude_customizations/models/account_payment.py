from odoo import fields, models

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    dekad_received_by_id = fields.Many2one(
        'res.users', string='Received By', copy=False,
        domain=[('share', '=', False)],
        default=lambda self: self.env.user,
        help='User shown (name and signature) as the receiver on the voucher.',
    )

    def dekad_amount_words(self, lang='en'):
        """Amount in words for the payment receipt, English or Arabic."""
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
