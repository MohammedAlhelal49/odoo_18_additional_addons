from odoo import api, fields, models


class LondonDeliveryMethod(models.Model):
    """طريقة التوصيل: الكاشير بيختارها من نقطة البيع، وبتنتقل للفاتورة."""
    _name = 'london.delivery.method'
    _inherit = ['pos.load.mixin']
    _description = 'Laundry Delivery Method'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    # التوصيل بأجرة: الـ POS بيضيف سطر "توصيل" لحاله وبيطلب سعره
    laundry_with_charge = fields.Boolean(
        string='Delivery Charge',
        help='Choosing this method in the POS adds the delivery charge line and asks the cashier for its price.')

    @api.model
    def _load_pos_data_domain(self, data):
        return [('active', '=', True)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name', 'sequence', 'laundry_with_charge']


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        return super()._load_pos_data_models(config_id) + ['london.delivery.method', 'london.delivery.person']
