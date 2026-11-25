from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """منتج خصم الزبون انخلق بعد ما انضاف الحقل على نقاط البيع: منربطه هلق."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['pos.config']._laundry_set_customer_discount_product()
