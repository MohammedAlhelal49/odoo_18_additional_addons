from decimal import ROUND_HALF_UP, Decimal

from num2words import num2words

from odoo import api, fields, models

UAE_EMIRATES = [
    ('Abu Dhabi', 'Abu Dhabi'),
    ('Dubai', 'Dubai'),
    ('Sharjah', 'Sharjah'),
    ('Ajman', 'Ajman'),
    ('Umm Al Quwain', 'Umm Al Quwain'),
    ('Ras Al Khaimah', 'Ras Al Khaimah'),
    ('Fujairah', 'Fujairah'),
]

_UNITS = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
          'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
_TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
_SCALES = ['', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion']


def _hundreds_to_words(number):
    hundreds, rest = divmod(number, 100)
    words = []
    if hundreds:
        words.append('%s Hundred' % _UNITS[hundreds])
    if rest < 20:
        words.append(_UNITS[rest])
    else:
        words.append(_TENS[rest // 10])
        words.append(_UNITS[rest % 10])
    return ' '.join(w for w in words if w)


def _whole_number_to_words(number):
    """Same wording as the ConvertWholeNumber VBA macro of the Viewsport Excel template."""
    if not number:
        return 'Zero'
    parts = []
    scale = 0
    while number:
        number, chunk = divmod(number, 1000)
        if chunk:
            scale_name = _SCALES[scale] if scale < len(_SCALES) else ''
            parts.insert(0, ' '.join(w for w in [_hundreds_to_words(chunk), scale_name] if w))
        scale += 1
    return ' '.join(parts)


def amount_to_dirhams_text(amount):
    """Port of the ConvertToDirhams VBA macro, e.g. 46.2 -> 'Forty Six Dirhams and Twenty Fils'."""
    cents = int((Decimal(str(abs(amount or 0.0))) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    dirhams, fils = divmod(cents, 100)
    text = '%s %s' % (_whole_number_to_words(dirhams), 'Dirham' if dirhams == 1 else 'Dirhams')
    if fils:
        text += ' and %s %s' % (_whole_number_to_words(fils), 'Fil' if fils == 1 else 'Fils')
    return ('Minus ' + text) if (amount or 0) < 0 and cents else text


def vat_label(tax_sets):
    """'5%' when every taxed line uses the same single percentage, '' otherwise (mixed / exempt lines)."""
    rates = {tuple(sorted(t.amount for t in taxes)) for taxes in tax_sets}
    if len(rates) == 1:
        rate = next(iter(rates))
        if len(rate) == 1:
            return '%g%%' % rate[0]
    return ''


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    po_enclose = fields.Char(string='PO Enclose')
    po_no_of_pages = fields.Char(string='PO No. of Pages')
    ship_to_info = fields.Text(string='Delivery Location')
    contact_person_id = fields.Many2one('res.partner', string='Contact Person')
    contact_number = fields.Char(string='Contact Number')
    delivery_plan_type = fields.Selection(
        [('immediate', 'Immediately'), ('period', 'Within Period')],
        string='Delivery Plan', default='immediate', required=True)
    delivery_days = fields.Integer(string='Delivery Period', default=15)
    delivery_period_unit = fields.Selection(
        [('days', 'Days'), ('weeks', 'Weeks')], string='Period Unit', default='days', required=True)
    ex_emirate = fields.Selection(UAE_EMIRATES, string='Prices Ex Emirate', default='Dubai')
    po_revision = fields.Integer(string='Revision', default=0, copy=False)
    partner_ref_date = fields.Date(string='Vendor Quote Date', copy=False)
    rfq_seq = fields.Char(string='RFQ Sequence', copy=False, readonly=True,
                          help='Yearly RFQ counter, printed after the project code: 2000-260001.')
    rfq_delivery_location = fields.Selection(
        [('site', 'At Project Site'), ('warehouse', 'Viewsport Warehouse'), ('supplier', 'Collect at Supplier Store')],
        string='RFQ Delivery Location', default='warehouse')

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._vs_assign_rfq_seq()
        return orders

    def _vs_assign_rfq_seq(self):
        for order in self.filtered(lambda o: not o.rfq_seq):
            order.sudo().rfq_seq = self.env['ir.sequence'].sudo().next_by_code(
                'viewsport.rfq', sequence_date=order.date_order)

    def _get_rfq_number(self):
        """RFQ number as on the Viewsport template: <project code>-<yy><counter>, e.g. 2000-260001."""
        self.ensure_one()
        self._vs_assign_rfq_seq()
        project = self._get_rfq_project_ref()
        return '%s-%s' % (project, self.rfq_seq) if project != '-' else self.rfq_seq

    def _get_rfq_report_filename(self):
        """RFQ_<project>_<number>_<first item>_<supplier>, as the Excel file names."""
        self.ensure_one()
        item = self.order_line.filtered(lambda l: not l.display_type)[:1]
        parts = ['RFQ', self._get_rfq_project_ref().replace('-', ''), self.rfq_seq or self.name,
                 (item.product_id.name or item.name or '').split('\n')[0][:40],
                 self.partner_id.commercial_partner_id.name or '']
        return '_'.join(p.strip() for p in parts if p and p.strip()).replace('/', '-')

    @api.onchange('partner_id')
    def _onchange_partner_id_payment_terms(self):
        if self.partner_id and self.partner_id.property_supplier_payment_term_id:
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id

    @api.onchange('contact_person_id')
    def _onchange_contact_person_id(self):
        if self.contact_person_id:
            self.contact_number = self.contact_person_id.phone or self.contact_person_id.mobile or self.contact_number

    def _vs_vat_label(self):
        lines = self.order_line.filtered(lambda l: not l.display_type)
        return vat_label([l.taxes_id for l in lines]) if lines else '5%'

    def _get_revision_label(self):
        self.ensure_one()
        return '[%02d]' % self.po_revision

    def _get_delivery_period_label(self):
        self.ensure_one()
        unit = 'Weeks' if self.delivery_period_unit == 'weeks' else 'Days'
        return '%s %s' % (self.delivery_days or 0, unit)

    def _get_delivery_plan_label(self):
        self.ensure_one()
        return 'Implementation period' if self.delivery_plan_type == 'period' else 'Delivery Plan'

    def _get_delivery_term_short(self):
        self.ensure_one()
        if self.delivery_plan_type == 'period':
            return self._get_delivery_period_label()
        return 'Immediately'

    def _get_rfq_delivery_period_text(self):
        """Term 2 of the RFQ, e.g. 'Immediately' or 'not exceed 1 Weeks after receipt of #PO.'"""
        self.ensure_one()
        if self.delivery_plan_type == 'period':
            return 'not exceed %s after receipt of #PO.' % self._get_delivery_period_label()
        return 'Immediately.'

    def _get_rfq_project_ref(self):
        self.ensure_one()
        project = self._get_project_analytic_account()
        return project.custom_project_code or project.code or '-'

    def _get_delivery_plan_text(self):
        self.ensure_one()
        if self.delivery_plan_type == 'period':
            count = self.delivery_days or 0
            unit = 'Weeks' if self.delivery_period_unit == 'weeks' else 'Days'
            return 'Not exceed %s (%s) %s after receipt of PO.' % (num2words(count), count, unit)
        return 'Immediately.'

    def _get_amount_in_words(self):
        self.ensure_one()
        if self.currency_id.name == 'AED':
            return amount_to_dirhams_text(self.amount_total)
        return self.currency_id.amount_to_text(self.amount_total)

    def _get_project_analytic_account(self):
        """Project of the PO: an account with a project code, else one from a 'Project' plan, else the first one."""
        self.ensure_one()
        account_ids = set()
        for line in self.order_line:
            for key in (line.analytic_distribution or {}):
                account_ids.update(int(account_id) for account_id in key.split(','))
        accounts = self.env['account.analytic.account'].browse(sorted(account_ids)).exists()
        project_accounts = accounts.filtered(lambda a: 'project' in (a.plan_id.name or '').lower())
        return (accounts.filtered('custom_project_code') or project_accounts or accounts)[:1]
