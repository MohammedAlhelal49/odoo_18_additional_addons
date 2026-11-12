from odoo import _, fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    # Collected now so turnaround / not-picked-up reports have history later.
    laundry_ready_date = fields.Datetime(string="Ready On", copy=False, readonly=True, index=True)
    laundry_picked_up_date = fields.Datetime(string="Picked Up On", copy=False, readonly=True, index=True)

    def action_laundry_mark_ready(self):
        self.filtered(lambda o: not o.laundry_ready_date).write({"laundry_ready_date": fields.Datetime.now()})
        return True

    def action_laundry_mark_picked_up(self):
        now = fields.Datetime.now()
        for order in self:
            if order.laundry_picked_up_date:
                raise UserError(_("Order %s is already marked as picked up.", order.name))
            vals = {"laundry_picked_up_date": now}
            if not order.laundry_ready_date:
                vals["laundry_ready_date"] = now
            order.write(vals)
        return True

    def action_send_whatsapp(self):
        """The 'Order Ready' WhatsApp button also stamps the ready date (first time only)."""
        res = super().action_send_whatsapp()
        self.filtered(lambda o: not o.laundry_ready_date).write({"laundry_ready_date": fields.Datetime.now()})
        return res
