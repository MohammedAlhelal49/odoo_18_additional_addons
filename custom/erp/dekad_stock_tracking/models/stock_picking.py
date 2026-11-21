from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_order_confirm_date = fields.Datetime(
        string='Order Confirm Date',
        tracking=True,
        copy=False,
    )
    x_preparing_order_date = fields.Datetime(
        string='Preparing Order Date',
        tracking=True,
        copy=False,
    )
    x_shipping_order_date = fields.Datetime(
        string='Shipping Order Date',
        tracking=True,
        copy=False,
    )
    x_shipment_delivery_date = fields.Datetime(
        string='Shipment Delivery Date',
        tracking=True,
        copy=False,
    )
    x_shipment_company = fields.Char(
        string='Shipment Company',
        tracking=True,
        copy=False,
    )
    x_shipment_method = fields.Char(
        string='Shipment Method',
        tracking=True,
        copy=False,
    )
    x_is_intercompany_dest = fields.Boolean(
        string='Is Intercompany Destination',
        default=False,
        copy=False,
    )

    # الحقول اللي بتتزامن مع الـ moves (كلها ماعدا confirm date)
    PROPAGATE_FIELDS = [
        'x_preparing_order_date',
        'x_shipping_order_date',
        'x_shipment_delivery_date',
        'x_shipment_company',
        'x_shipment_method',
    ]

    # كل الحقول للـ intercompany sync
    TRACKING_FIELDS = [
        'x_order_confirm_date',
        'x_preparing_order_date',
        'x_shipping_order_date',
        'x_shipment_delivery_date',
        'x_shipment_company',
        'x_shipment_method',
    ]

    # ------------------------------------------------------------------ #
    #  Propagate Header values → stock.move lines                        #
    # ------------------------------------------------------------------ #

    def _propagate_to_moves(self, vals):
        """
        لما يتغير أي حقل على الـ Header (ماعدا confirm date)،
        نحدّث كل الـ moves تلقائياً بنفس القيمة.
        المستخدم يقدر يعدل كل سطر بشكل منفصل بعدين.
        """
        propagate_vals = {
            k: v for k, v in vals.items()
            if k in self.PROPAGATE_FIELDS
        }
        if not propagate_vals:
            return

        for picking in self:
            if picking.move_ids:
                picking.move_ids.with_context(
                    skip_move_propagation=True
                ).write(propagate_vals)
                _logger.info(
                    "Propagated %s to %d moves of picking %s",
                    list(propagate_vals.keys()),
                    len(picking.move_ids),
                    picking.name,
                )

    # ------------------------------------------------------------------ #
    #  On create: mark Receipt as intercompany destination                #
    # ------------------------------------------------------------------ #

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._mark_intercompany_dest()
        return records

    def _mark_intercompany_dest(self):
        for picking in self:
            if picking.picking_type_code not in ('incoming', 'dropship'):
                continue
            if not picking.partner_id:
                continue
            # نستخدم partner_id مباشرة — موجود وقت الـ create
            sale_company = self.env['res.company'].sudo().search([
                ('partner_id', '=', picking.partner_id.id)
            ], limit=1)
            if sale_company and sale_company != picking.company_id:
                picking.sudo().write({'x_is_intercompany_dest': True})
                picking.move_ids.sudo().write({'x_is_intercompany_dest': True})
                _logger.info(
                    "Marked picking %s and its moves as intercompany destination",
                    picking.name,
                )

    # ------------------------------------------------------------------ #
    #  Find linked Receipt at buying company                              #
    # ------------------------------------------------------------------ #

    def _get_intercompany_dest_picking(self):
        self.ensure_one()
        if not self.sale_id or self.picking_type_code not in ('outgoing', 'dropship'):
            return self.env['stock.picking']

        purchase_order = self.env['purchase.order'].sudo().search([
            ('name', '=', self.sale_id.client_order_ref),
        ], limit=1)

        if not purchase_order:
            return self.env['stock.picking']

        return purchase_order.picking_ids.filtered(
            lambda p: p.picking_type_code in ('incoming', 'dropship')
        )

    # ------------------------------------------------------------------ #
    #  Sync tracking fields to Receipt (intercompany)                    #
    # ------------------------------------------------------------------ #

    def _sync_tracking_to_dest(self, vals):
        sync_vals = {k: v for k, v in vals.items() if k in self.TRACKING_FIELDS}
        if not sync_vals:
            return
        for picking in self:
            if picking.x_is_intercompany_dest:
                continue
            dest_pickings = picking._get_intercompany_dest_picking()
            if dest_pickings:
                dest_pickings.sudo().with_context(
                    skip_intercompany_sync=True
                ).write(sync_vals)
                _logger.info(
                    "Synced %s → %s",
                    picking.name,
                    dest_pickings.mapped('name'),
                )

    # ------------------------------------------------------------------ #
    #  Auto-fill Shipping Order Date on Validate                         #
    # ------------------------------------------------------------------ #

    def button_validate(self):
        res = super().button_validate()
        now = fields.Datetime.now()
        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue
            if picking.x_is_intercompany_dest:
                continue
            if not picking.x_shipping_order_date:
                picking.write({'x_shipping_order_date': now})
        return res

    # ------------------------------------------------------------------ #
    #  Write                                                              #
    # ------------------------------------------------------------------ #

    def write(self, vals):
        res = super().write(vals)

        # 1 — نشر القيم من الـ Header للـ moves
        if not self.env.context.get('skip_intercompany_sync'):
            self._propagate_to_moves(vals)

        # 2 — مزامنة مع الـ Receipt عند UAE
        if not self.env.context.get('skip_intercompany_sync'):
            self._sync_tracking_to_dest(vals)

        return res