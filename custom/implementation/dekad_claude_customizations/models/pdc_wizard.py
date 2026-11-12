import base64
import logging
import os
import subprocess
import tempfile

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import mimetypes

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None


class PdcWizard(models.Model):
    _inherit = 'pdc.wizard'

    dekad_received_by_id = fields.Many2one(
        'res.users', string='Received By', copy=False,
        domain=[('share', '=', False)],
        default=lambda self: self.env.user,
        help='User shown (name and signature) as the receiver on the voucher.',
    )

    # The original field is an Image field (images only). Redefined as a plain binary
    # so a PDF can be uploaded too; data already stored stays valid (same attachment storage).
    pdc_image = fields.Binary(string='PDC Image', attachment=True,
                              help='Photo or PDF of the cheque (JPG, PNG or PDF, max 2 MB).')
    pdc_image_filename = fields.Char(string='PDC Image File Name')

    @api.constrains('pdc_image')
    def _check_dekad_pdc_image(self):
        limit = 2 * 1024 * 1024
        for rec in self.filtered('pdc_image'):
            raw = base64.b64decode(rec.pdc_image)
            if len(raw) > limit:
                raise ValidationError(_(
                    "The cheque file is too large (max 2 MB). / حجم ملف الشيك كبير (الحد الأقصى 2 ميغابايت)."))
            if not (mimetypes.guess_mimetype(raw).startswith('image/')
                    or raw[:5] == b'%PDF-'):
                raise ValidationError(_(
                    "Only images or PDF files are allowed. / يسمح بالصور أو ملفات PDF فقط."))

    @staticmethod
    def _dekad_pdf_first_page(raw):
        """First page of a PDF as a PNG (base64) using Ghostscript, or False."""
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 'in.pdf')
            out = os.path.join(tmp, 'out.png')
            with open(src, 'wb') as f:
                f.write(raw)
            try:
                subprocess.run(
                    ['gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m', '-r110',
                     '-dFirstPage=1', '-dLastPage=1', '-sOutputFile=' + out, src],
                    check=True, timeout=30, capture_output=True)
                with open(out, 'rb') as f:
                    return base64.b64encode(f.read())
            except (OSError, subprocess.SubprocessError):
                _logger.warning("Could not convert the PDC PDF to an image", exc_info=True)
                return False

    def dekad_cheque_copy(self):
        """Image shown on the voucher: the PDC Image (a picture, or the first page of a PDF),
        else the first image in Cheque Attachments."""
        self.ensure_one()
        if self.pdc_image:
            raw = base64.b64decode(self.pdc_image)
            if mimetypes.guess_mimetype(raw).startswith('image/'):
                return self.pdc_image
            if raw[:5] == b'%PDF-':
                page = self._dekad_pdf_first_page(raw)
                if page:
                    return page
        att = self.attachment_ids.sudo().filtered(
            lambda a: (a.mimetype or '').startswith('image/'))[:1]
        return att.datas if att else False

    def dekad_amount_words(self, lang='en'):
        """Amount in words for the voucher, English or Arabic."""
        self.ensure_one()
        amount = self.payment_amount or 0.0
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

    def dekad_invoice_lines(self):
        """Linked invoices/bills with their payments by date, this cheque, and the balance.

        The cheque only reconciles against the invoice when it is 'done'; before that
        it is shown as a pending row and subtracted from the balance."""
        self.ensure_one()
        invoices = (self.invoice_id | self.invoice_ids).sorted(
            lambda m: (m.invoice_date or m.date, m.id))
        remaining = self.payment_amount or 0.0
        result = []
        for inv in invoices:
            rows = []
            partials = inv._get_reconciled_invoices_partials()[0]
            for _partial, amount, line in sorted(
                    partials, key=lambda p: (p[2].move_id.date, p[2].id)):
                rows.append({
                    'date': line.move_id.date,
                    'name': line.move_id.name,
                    'ref': (line.payment_id.memo if line.payment_id else line.move_id.ref) or '',
                    'amount': amount,
                    'cheque': False,
                })
            balance = inv.amount_residual
            if self.state != 'done' and balance > 0 and remaining > 0:
                allocated = min(remaining, balance)
                remaining -= allocated
                balance -= allocated
                rows.append({
                    'date': self.payment_date,
                    'name': self.name,
                    'ref': self.reference or '',
                    'amount': allocated,
                    'cheque': True,
                })
            result.append({'invoice': inv, 'rows': rows, 'balance': balance})
        return result
