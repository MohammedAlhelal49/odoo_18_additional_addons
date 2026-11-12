from odoo import _, api, fields, models


class LondonDeliveryPerson(models.Model):
    """الشخص اللي وصّل الطلب: الكاشير بيكتب الاسم من نقطة البيع (مع اقتراحات الأسماء اللي
    انكتبت قبل)، والاسم الجديد بينضاف هون لحاله. المدير بيصلّح أو بيأرشف الأسماء من الإعدادات."""
    _name = 'london.delivery.person'
    _inherit = ['pos.load.mixin']
    _description = 'Laundry Delivery Person'
    _order = 'name, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    @api.model
    def _load_pos_data_domain(self, data):
        return [('active', '=', True)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name']

    @api.model
    def _laundry_find_or_create(self, name):
        """نفس الاسم (بغض النظر عن الفراغات وحالة الأحرف) = نفس الشخص، وإلا شخص جديد."""
        name = " ".join((name or "").split())
        if not name:
            return self.browse()
        person = self.with_context(active_test=False).search([('name', '=ilike', name)], limit=1)
        if person and not person.active:
            person.sudo().active = True
        return person or self.sudo().create({'name': name})
