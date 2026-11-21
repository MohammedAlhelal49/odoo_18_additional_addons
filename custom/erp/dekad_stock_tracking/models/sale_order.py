from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        now = fields.Datetime.now()
        for order in self:
            for picking in order.picking_ids:
                # على الـ Header
                if not picking.x_order_confirm_date:
                    picking.write({'x_order_confirm_date': now})
                # على كل سطر (stock.move)
                for move in picking.move_ids:
                    if not move.x_order_confirm_date:
                        move.write({'x_order_confirm_date': now})
        return res
