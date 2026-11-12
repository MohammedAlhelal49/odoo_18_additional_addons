from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.constrains("start_date", "end_date")
    def _check_line_dates(self):
        for line in self:
            if not line.start_date or not line.end_date:
                continue

            # Rule 1: start_date must be before end_date
            if line.start_date >= line.end_date:
                raise ValidationError(
                    "On line '%s', the Start Date must be earlier than the End Date."
                    % (line.name or line.product_id.display_name or "")
                )

            order = line.order_id
            order_start = order.rental_start_date
            order_end = order.end_date

            # Rule 2: line dates must fall within the order's rental range
            if order_start and line.start_date < order_start:
                raise ValidationError(
                    "On line '%s', the Start Date (%s) cannot be before the "
                    "contract's Rental Start Date (%s)."
                    % (
                        line.name or line.product_id.display_name or "",
                        line.start_date,
                        order_start,
                    )
                )

            if order_end and line.end_date > order_end:
                raise ValidationError(
                    "On line '%s', the End Date (%s) cannot be after the "
                    "contract's End Date (%s)."
                    % (
                        line.name or line.product_id.display_name or "",
                        line.end_date,
                        order_end,
                    )
                )
