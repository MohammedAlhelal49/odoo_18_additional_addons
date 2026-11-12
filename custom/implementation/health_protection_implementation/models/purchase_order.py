from odoo import api, fields, models

from .account_move import hp_address_line


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    customer_id = fields.Many2one(
        'res.partner', string='Customer', tracking=True,
        help="Customer this purchase is made for. Its pricelist gives the purchase prices.")
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Price List', tracking=True,
        compute='_compute_pricelist_id', store=True, readonly=False, precompute=True,
        help="Purchase prices of the order lines are taken from this pricelist.")

    def hp_partner_address_line(self):
        self.ensure_one()
        return hp_address_line(self.partner_id)

    def hp_show_portal_qr(self):
        self.ensure_one()
        return self.state != 'cancel'

    @api.depends('customer_id')
    def _compute_pricelist_id(self):
        for order in self:
            order.pricelist_id = order.customer_id.property_product_pricelist if order.customer_id else False

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_purchase_price(self):
        self.order_line._apply_pricelist_purchase_price(reset_missing=True)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('order_id.pricelist_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        super()._compute_price_unit_and_date_planned_and_name()
        self._apply_pricelist_purchase_price()

    def _apply_pricelist_purchase_price(self, reset_missing=False):
        """Use the purchase price of the order's pricelist rule, when the rule has one.

        :param reset_missing: when the customer changes, lines without a purchase price in the
            new pricelist go back to the product cost instead of keeping the previous customer's price
        """
        for line in self:
            pricelist = line.order_id.pricelist_id
            if not line.product_id or line.invoice_lines:
                continue
            uom = line.product_uom or line.product_id.uom_po_id
            if reset_missing:
                line.price_unit = line.product_id.uom_id._compute_price(line.product_id.standard_price, uom)
            if not pricelist:
                continue
            date = line.order_id.date_order or fields.Date.context_today(line)
            rule = self.env['product.pricelist.item'].browse(
                pricelist._get_product_rule(line.product_id, line.product_qty or 1.0, date=date))
            if not rule.purchase_price:
                continue
            price = line.product_id.uom_id._compute_price(rule.purchase_price, uom)
            line.price_unit = pricelist.currency_id._convert(price, line.currency_id, line.company_id, date, False)
            line.discount = 0.0
