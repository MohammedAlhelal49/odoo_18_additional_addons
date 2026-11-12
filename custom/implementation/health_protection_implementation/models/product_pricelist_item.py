from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    purchase_price = fields.Float(
        string='Purchase Price', digits='Product Price',
        help="Purchase price of this product when bought for the customer of this pricelist.")
