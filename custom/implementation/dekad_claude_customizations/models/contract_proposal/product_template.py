from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cp_scope = fields.Text(
        string='Proposal Scope', translate=True,
        help='Included scope printed in the Technical Proposal when this product (category "Modules") '
             'is added as a module. Write it in English, then translate it to Arabic like the product name.')

    @api.model
    def _cp_seed_arabic(self):
        """Arabic name/scope of the seeded module products (only while still equal to the English text)."""
        arabic = {
        'cp_product_accounting': (
            'المحاسبة',
            'دليل الحسابات، الأرصدة الافتتاحية، فواتير العملاء والموردين والمدفوعات، التسوية البنكية، ضريبة القيمة المضافة والتقارير المالية.'),
        'cp_product_sales': (
            'المبيعات',
            'العملاء والمنتجات، عروض الأسعار وأوامر البيع، قوائم الأسعار، الفوترة من أوامر البيع.'),
        'cp_product_purchase': (
            'المشتريات',
            'الموردون، طلبات عروض الأسعار، أوامر الشراء، الاستلام وفواتير الموردين.'),
        'cp_product_inventory': (
            'المخزون',
            'المستودعات والمواقع، الاستلام والتسليم، حركات المخزون، تقييم المخزون وتقاريره.'),
        'cp_product_pos': (
            'نقاط البيع',
            'جلسات نقاط البيع، عمليات الكاشير، طرق الدفع، الإغلاق اليومي، الربط مع المخزون والمحاسبة.'),
        'cp_product_hr': (
            'الموارد البشرية',
            'بيانات الموظفين، الحضور والانصراف، الإجازات والغياب، العقود والوثائق.'),
        }
        for key, (name_ar, scope_ar) in arabic.items():
            product = self.env.ref('dekad_claude_customizations.' + key, raise_if_not_found=False)
            if not product:
                continue
            ar = product.with_context(lang='ar_001')
            if ar.name == product.with_context(lang='en_US').name:
                ar.write({'name': name_ar, 'cp_scope': scope_ar})
