import base64
import os

from markupsafe import Markup

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None

from odoo import api, fields, models
from odoo.tools.misc import format_date

from .cp_lines import STANDARD_PHASES

EDITION_LABELS = {'community': ('Dekad ERP (based on Odoo)', 'ديكاد ERP (مبني على أودو)'), 'enterprise': ('Odoo Enterprise', 'أودو إنتربرايز (Odoo Enterprise)')}

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'fonts')
FONT_FILES = {'regular': 'Cairo-Regular.ttf', 'bold': 'Cairo-Bold.ttf'}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cp_revision = fields.Integer(string='Proposal Revision', default=1, copy=False)
    cp_project_en = fields.Char(string='Project Name (EN)', default='Core Business ERP Implementation')
    cp_project_ar = fields.Char(string='Project Name (AR) / اسم المشروع', default='تنفيذ نظام إدارة الأعمال الأساسي')
    cp_edition = fields.Selection([('community', 'Company ERP (based on Odoo)'), ('enterprise', 'Odoo Enterprise')],
                                  string='Odoo Edition', default='enterprise')
    cp_version = fields.Char(string='Odoo Version', default='18')

    cp_module_ids = fields.One2many('dekad.cp.module', 'order_id', string='Functional Modules', copy=True)
    cp_note_modules = fields.Text(string='Additional Notes (Modules)')

    cp_phase_ids = fields.One2many('dekad.cp.phase', 'order_id', string='Delivery Phases', copy=True)
    cp_duration_en = fields.Char(string='Overall Duration (EN)', help='e.g. 2 to 3 months from the start of work')
    cp_duration_ar = fields.Char(string='Overall Duration (AR) / المدة الإجمالية',
                                 help='مثال: من شهرين إلى ثلاثة أشهر من تاريخ بدء العمل')
    cp_note_delivery = fields.Text(string='Additional Notes (Delivery)')

    cp_training_from = fields.Integer(string='Sessions From')
    cp_training_to = fields.Integer(string='Sessions To')
    cp_training_hours = fields.Float(string='Hours per Session', default=1.5)
    cp_note_training = fields.Text(string='Additional Notes (Training)')

    cp_note_data = fields.Text(string='Additional Notes (Data & Acceptance)')

    cp_support_months = fields.Integer(string='Free Support (months)', default=3)
    cp_support_from = fields.Char(string='Support Hours From', default='10:00')
    cp_support_to = fields.Char(string='Support Hours To', default='18:00')
    cp_note_support = fields.Text(string='Additional Notes (Support)')
    cp_note_annual = fields.Text(string='Additional Notes (Annual Support)')

    cp_cust_signer_name = fields.Char(string='Customer Signatory Name')
    cp_cust_signer_title = fields.Char(string='Customer Signatory Position')

    # ---- implementation contract ---------------------------------------------
    ct_date = fields.Date(string='Contract Date', copy=False,
                          help='Actual signing date of the implementation contract (not the quotation date).')
    ct_payment_method = fields.Selection(
        [('transfer', 'Bank transfer'), ('cheque', 'Cheque'), ('cash', 'Cash'),
         ('any', 'Bank transfer / cheque / cash')], string='Payment Method', default='any')
    ct_has_tax_flag = fields.Boolean(compute='_compute_ct_has_tax')
    ct_tax_mode = fields.Selection(
        [('exclusive', 'Exclusive of VAT'), ('inclusive', 'Inclusive of VAT')],
        string='Contract Value', default='exclusive')
    ct_payment_ids = fields.One2many('dekad.ct.payment', 'order_id', string='Contract Payments', copy=True)
    ct_late_days = fields.Integer(
        string='First Payment Delay Limit (working days)', default=7,
        help='If the FIRST payment is later than this after signing, the first party may terminate the contract.')
    ct_notice_days = fields.Integer(
        string='Overdue Payment: Reminder After (days)', default=7,
        help='A written reminder is sent when a payment is unpaid this many days after its due date.')
    ct_suspend_days = fields.Integer(
        string='Overdue Payment: Work Stops After (days)', default=15,
        help='Unpaid this many days after the due date: the first party may suspend work, support and hosting.')
    ct_terminate_days = fields.Integer(
        string='Overdue Payment: Contract Ends After (days)', default=30,
        help='Unpaid this many days after the due date: the first party may terminate the contract; amounts paid are not refunded.')
    ct_withdraw_days = fields.Integer(
        string='Client Withdrawal Window (working days)', default=15,
        help='If the client cancels within this many working days of signing, the first payment is not refunded '
             'and the second payment cheque is returned.')
    ct_note = fields.Text(string='Additional Contract Terms')

    cp_include_hosting = fields.Boolean(string='Include Hosting & Licences')
    cp_hosting_users = fields.Integer(string='Number of Users')
    cp_hosting_price = fields.Monetary(string='Hosting (server) per Year', default=1500.0, currency_field='currency_id')
    cp_note_hosting = fields.Text(string='Additional Notes (Hosting)')

    # ---- buttons -------------------------------------------------------------
    def action_cp_add_phases(self):
        for order in self:
            if order.cp_phase_ids:
                continue
            for index, (name_en, name_ar) in enumerate(STANDARD_PHASES, start=1):
                self.env['dekad.cp.phase'].create({
                    'order_id': order.id, 'sequence': index * 10, 'name_en': name_en, 'name_ar': name_ar})
        return True

    # ---- contract helpers -----------------------------------------------------
    def ct_platform(self, lang='en'):
        """Platform name with the version: 'Dekad ERP 18 (based on Odoo)' / 'Odoo Enterprise 18'."""
        self.ensure_one()
        version = (self.cp_version or '').strip()
        enterprise = self.cp_edition == 'enterprise'
        if lang == 'ar':
            base = 'أودو إنتربرايز' if enterprise else '%s ERP' % self.company_id.ct_brand('ar')
            suffix = '' if enterprise else ' (مبني على أودو)'
        else:
            base = 'Odoo Enterprise' if enterprise else '%s ERP' % self.company_id.ct_brand()
            suffix = '' if enterprise else ' (based on Odoo)'
        return '%s%s%s' % (base, ' ' + version if version else '', suffix)

    def ct_ref(self):
        self.ensure_one()
        return 'CT-%s' % self.name

    def ct_has_tax(self):
        """True when the order lines carry an active tax; archived taxes mean no tax at all."""
        self.ensure_one()
        return any(line.tax_id for line in self.order_line if not line.display_type)

    @api.depends('order_line.tax_id')
    def _compute_ct_has_tax(self):
        for order in self:
            order.ct_has_tax_flag = order.ct_has_tax()

    def ct_total(self):
        self.ensure_one()
        return self.amount_total if self.ct_has_tax() and self.ct_tax_mode == 'inclusive' else self.amount_untaxed

    def ct_installments(self):
        """[(english label, arabic label, amount, percent)] from the contract payments of the order;
        from the order's payment term when none are entered; a single payment otherwise."""
        self.ensure_one()
        total = self.ct_total()
        methods = {'transfer': ('bank transfer', 'تحويل بنكي'), 'cheque': ('cheque', 'شيك'), 'cash': ('cash', 'نقداً')}
        rows = []
        if self.ct_payment_ids:
            for line in self.ct_payment_ids.sorted('sequence'):
                en, ar = line.name_en, line.name_ar or line.name_en
                if line.method:
                    en = '%s (by %s)' % (en, methods[line.method][0])
                    ar = '%s (%s)' % (ar, methods[line.method][1])
                rows.append([en, ar, line.percent])
        else:
            term = self.payment_term_id
            lines = term.line_ids.sorted('id') if term else term.browse()
            for line in lines:
                if line.nb_days:
                    rows.append(['After %s days from the contract date' % line.nb_days,
                                 'بعد %s يوماً من تاريخ العقد' % line.nb_days,
                                 line.value_amount if line.value == 'percent' else 0.0])
                else:
                    rows.append(['On signing the contract', 'عند توقيع العقد',
                                 line.value_amount if line.value == 'percent' else 0.0])
            if not rows:
                rows = [['On signing the contract', 'عند توقيع العقد', 100.0]]
        result, paid = [], 0.0
        for index, (en, ar, percent) in enumerate(rows):
            if index == len(rows) - 1:
                amount = total - paid
                percent = 100.0 - sum(r[3] for r in result) if result else 100.0
            else:
                amount = self.currency_id.round(total * percent / 100.0)
            paid += amount
            result.append((en, ar, amount, percent))
        return result

    def ct_words(self, amount, lang='en'):
        """Amount in words, English or Arabic."""
        self.ensure_one()
        whole = int(amount)
        fils = int(round((amount - whole) * 100))
        if lang == 'ar':
            if not num2words:
                return ''
            name = 'درهم إماراتي' if self.currency_id.name == 'AED' else self.currency_id.name
            text = '%s %s' % (num2words(whole, lang='ar'), name)
            if fils:
                text += ' و%s فلس' % num2words(fils, lang='ar')
            return text + ' فقط لا غير'
        return self.currency_id.with_context(lang='en_US').amount_to_text(amount) + ' Only'

    @api.model
    def ct_v(self, value):
        """Value, or a blank line to fill by hand when empty."""
        return value or Markup('<span class="ct-blank">&nbsp;</span>')

    # ---- helpers used by the QWeb report -----------------------------------------
    def cp_ref(self):
        self.ensure_one()
        return 'TP-%s' % self.name

    def cp_date(self):
        self.ensure_one()
        return (self.date_order or fields.Datetime.now()).date()

    @api.model
    def cp_v(self, value, lang='en'):
        """Value, or a yellow bracketed placeholder (to be filled by hand) when it is empty."""
        if value:
            return value
        return Markup('<span class="cp-todo">[%s]</span>') % ('يُستكمل يدوياً' if lang == 'ar' else 'To be completed')

    def cp_d(self, value, lang='en'):
        """Date as 21 Sep 2026 (Latin digits in both languages)."""
        return format_date(self.env, value, lang_code='en_US', date_format='dd MMM yyyy') if value else ''

    def cp_label(self, kind, value, lang='en'):
        if value == 'community':
            brand = self.company_id.ct_brand(lang)
            return '%s ERP (مبني على أودو)' % brand if lang == 'ar' else '%s ERP (based on Odoo)' % brand
        return EDITION_LABELS.get(value, ('', ''))[1 if lang == 'ar' else 0]

    def cp_company_label(self):
        """Provider name printed under the signature."""
        name = self.company_id.name or ''
        return name if 'solution' in name.lower() else '%s Software Solutions' % name

    def cp_sessions(self, lang='en'):
        """Training sessions wording: a range, a number, or "as needed" when nothing is set."""
        self.ensure_one()
        first, last, hours = self.cp_training_from, self.cp_training_to, self.cp_training_hours
        low, high = (min(first, last), max(first, last)) if first and last else (first or last, 0)
        hrs = ('%g' % hours) if hours else ''
        if lang == 'ar':
            if high and high != low:
                text = 'من %d إلى %d جلسات تدريبية حسب الحاجة' % (low, high)
            elif low == 1:
                text = 'جلسة تدريبية واحدة'
            elif low == 2:
                text = 'جلستان تدريبيتان'
            elif low:
                text = '%d جلسات تدريبية' % low
            else:
                text = 'جلسات تدريبية حسب الحاجة'
            return text + ('، مدة كل جلسة حتى %s ساعة' % hrs if hrs else '')
        if high and high != low:
            text = '%d to %d training sessions as needed' % (low, high)
        elif low:
            text = '%d training session%s' % (low, '' if low == 1 else 's')
        else:
            text = 'training sessions as needed'
        return text + (', each up to %s hours' % hrs if hrs else '')

    def cp_font_css(self):
        """@font-face rules with the bundled Cairo files embedded as data URIs (no network
        access needed by wkhtmltopdf). Empty when the font files are not bundled."""
        css = []
        for weight, filename in (('400', FONT_FILES['regular']), ('700', FONT_FILES['bold'])):
            path = os.path.join(FONT_DIR, filename)
            if os.path.isfile(path):
                with open(path, 'rb') as handle:
                    data = base64.b64encode(handle.read()).decode()
                css.append("@font-face{font-family:'Cairo';font-weight:%s;"
                           "src:url(data:font/ttf;base64,%s) format('truetype');}" % (weight, data))
        return Markup('\n'.join(css))
