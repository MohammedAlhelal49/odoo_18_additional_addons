from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _load_pos_data_fields(self, config_id):
        """
        إضافة حقل qty_available إلى البيانات
        المرسلة إلى POS session عند التحميل
        """
        fields = super()._load_pos_data_fields(config_id)
        if "qty_available" not in fields:
            fields.append("qty_available")
        return fields

    @api.model
    def get_pos_stock_qty(self, product_ids, config_id):
        """
        الكمية المتوفرة حالياً لكل منتج بموقع مخزون نقطة البيع
        (موقع المصدر لعملية التسليم تبع نقطة البيع)، بالوحدة الأساسية للمنتج.
        """
        config = self.env["pos.config"].browse(config_id)
        location = config.picking_type_id.default_location_src_id
        products = self.sudo().browse(product_ids)
        if location:
            products = products.with_context(location=location.id)
        return {product.id: product.qty_available for product in products}
