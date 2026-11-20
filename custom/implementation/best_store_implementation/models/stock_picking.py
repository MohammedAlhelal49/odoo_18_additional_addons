from odoo import Command, _, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def handle_reversed_purchase(self, confirm=False):
        """ Create the missing inter-company purchase order of old deliveries.

            For each done delivery of a sale order sold to another company of
            this database, create in that company the purchase order that the
            inter-company rules create when a sale order is confirmed, with the
            DELIVERED quantities. Sale orders that already have their purchase
            order are skipped.

            The purchase order is left in draft unless ``confirm`` is True; its
            receipt is created when it is confirmed. It is flagged
            auto_generated, so confirming it never creates a sale order back in
            the selling company.

            :return: the created purchase orders
        """
        PurchaseOrder = self.env['purchase.order'].sudo()
        created = PurchaseOrder
        deliveries = self.filtered(lambda p: p.state == 'done' and p.picking_type_code == 'outgoing' and p.sale_id)
        for order in deliveries.sale_id:
            company = self.env['res.company'].sudo()._find_company_from_partner(order.partner_id.id)
            if not company or company == order.company_id:
                continue
            if PurchaseOrder.search_count([
                ('company_id', '=', company.id),
                '|', ('auto_sale_order_id', '=', order.id), ('partner_ref', '=', order.name),
            ]):
                continue
            intercompany_user = company.intercompany_user_id
            if not intercompany_user:
                raise UserError(_("Provide one user for intercompany relation for %s", company.name))

            # same environment as sale_purchase_inter_company_rules uses on SO confirmation
            so = order.with_user(intercompany_user).with_context(default_company_id=company.id).with_company(company).sudo()
            company_partner = so.company_id.partner_id.with_user(intercompany_user)
            po_vals = so._prepare_purchase_order_data(company, company_partner)
            date_done = max(order.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_code == 'outgoing').mapped('date_done'))
            for line in so.order_line:
                if not line.display_type and float_is_zero(line.qty_delivered, precision_rounding=line.product_uom.rounding):
                    continue
                line_vals = so._prepare_purchase_order_line_data(line, so.date_order, company)
                if not line.display_type:
                    line_vals['product_qty'] = line.product_uom._compute_quantity(line.qty_delivered, line.product_id.uom_po_id)
                    line_vals['date_planned'] = date_done
                po_vals['order_line'].append(Command.create(line_vals))

            purchase_order = self.env['purchase.order'].with_user(intercompany_user).with_context(
                default_company_id=company.id).with_company(company).create(po_vals)
            purchase_order.message_post(body=_(
                "Generated afterwards from %(origin)s of company %(company)s (delivered quantities).",
                origin=order.name, company=order.company_id.name))
            if not order.client_order_ref:
                order.sudo().client_order_ref = purchase_order.name
            if confirm:
                purchase_order.button_confirm()
            created |= purchase_order
        return created.sudo()

    def action_handle_reversed_purchase(self):
        purchase_orders = self.handle_reversed_purchase()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success' if purchase_orders else 'warning',
                'message': _("Purchase orders created: %s", ', '.join(purchase_orders.mapped('name')))
                if purchase_orders else _("Nothing to create: no inter-company delivery without its purchase order."),
                'sticky': bool(purchase_orders),
            },
        }
