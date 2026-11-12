from odoo import api, fields, models

# Standard delivery phases loaded by the "Add standard phases" button: (English, Arabic).
STANDARD_PHASES = [
    ('Analysis', 'التحليل'),
    ('Configuration', 'التهيئة'),
    ('Data import', 'استيراد البيانات'),
    ('Training', 'التدريب'),
    ('Go-live', 'التشغيل'),
]


class DekadCpModule(models.Model):
    _name = 'dekad.cp.module'
    _description = 'Proposal Functional Module'
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Module (Product)')
    name_en = fields.Char(string='Module (EN)', required=True)
    name_ar = fields.Char(string='Module (AR) / الوحدة')
    scope_en = fields.Text(string='Included Scope (EN)')
    scope_ar = fields.Text(string='Included Scope (AR) / النطاق المشمول')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            en = product.with_context(lang='en_US')
            ar = product.with_context(lang='ar_001')
            self.name_en = en.name
            self.name_ar = ar.name
            self.scope_en = en.cp_scope
            self.scope_ar = ar.cp_scope


class DekadCpPhase(models.Model):
    _name = 'dekad.cp.phase'
    _description = 'Proposal Delivery Phase'
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name_en = fields.Char(string='Phase (EN)', required=True)
    name_ar = fields.Char(string='Phase (AR) / المرحلة')
    duration = fields.Char(string='Duration / المدة', help='Free text, e.g. "2 weeks" or "أسبوعان".')


class DekadCtPayment(models.Model):
    _name = 'dekad.ct.payment'
    _description = 'Implementation Contract Payment'
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name_en = fields.Char(string='Payment due on (EN)', required=True,
                          help='e.g. "On signing the contract" or "On delivery of the trial version".')
    name_ar = fields.Char(string='Payment due on (AR) / تُسدد عند')
    percent = fields.Float(string='%', required=True)
    method = fields.Selection(
        [('transfer', 'Bank transfer'), ('cheque', 'Cheque'), ('cash', 'Cash')],
        string='Method', help='Printed in brackets after the due event. Leave empty to print nothing.')
