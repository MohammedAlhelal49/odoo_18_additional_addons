import logging
import re
from uuid import uuid4

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

INCOME_TYPES = {'income', 'income_other'}

# PoS order references look like "Order 00564-001-0003": session id, login number, sequence
POS_REFERENCE_SESSION_RE = re.compile(r'(\d{5})-\d{3}-\d{4}')

class PosOrder(models.Model):
    _inherit = 'pos.order'


    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        result = super()._get_invoice_lines_values(line_values, pos_order_line)

        if not (pos_order_line.order_id.amount_total < 0.0):
            return result

        refund_account = self.env.company.refund_income_account_id
        if not refund_account:
            return result

        result['account_id'] = refund_account.id

        return result


    def action_cancel_order(self):
        if not self.env.user.has_group('account.group_account_invoice'):
            raise UserError(_("You must have the group (Accounting Invoicing) to perform this action."))
        for order in self:
            # Cancel related invoice
            if order.account_move:
                order.account_move.button_draft()
                order.account_move.button_cancel()
                # order.account_move.unlink()

            # Cancel related journal entries from POS payments
            for payment in order.payment_ids:
                move = payment.account_move_id
                if move:
                    move.button_draft()
                    move.button_cancel()
                    # move.unlink()

            # Cancel related delivery pickings
            for picking in order.picking_ids:
                if picking.state == 'done':
                    picking.action_confirm_cancel()
                # picking.unlink()

            order.write({'state': 'cancel'})


    def action_correct_order(self):
        if not self.env.user.has_group('account.group_account_invoice'):
            raise UserError(_("You must have the group (Accounting Invoicing) to perform this action."))
        for order in self:
            # Cancel related invoice
            if order.account_move and order.account_move.state == 'posted':
                order.account_move.button_draft()
                order.account_move.button_cancel()

            # Cancel related journal entries from POS payments
            for payment in order.payment_ids:
                move = payment.account_move_id
                if move and move.state == 'posted':
                    move.button_draft()
                    move.button_cancel()

            # Cancel related delivery pickings
            for picking in order.picking_ids:
                if picking.state == 'done':
                    picking.action_confirm_cancel()

            order.write({'state': 'cancel'})

            # Duplicate the order
            new_order = order.copy({
                'state': 'draft',
                'name': order.name,
                'pos_reference': order.pos_reference,
                'account_move': False,
                'picking_ids': [],
                # uuid is not copied: without one the PoS cannot match the order and
                # tries to create it again when it syncs it
                'uuid': str(uuid4()),
            })
            for record in (*new_order.lines, *new_order.payment_ids):
                record.uuid = str(uuid4())

            # Log on the new (draft) order
            new_order.message_post(
                body=_("This POS order was created as a correction of a previously cancelled order."))

            # Delete the original order
            order.unlink()

            # Open the new order in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Corrected POS Order',
                'res_model': 'pos.order',
                'res_id': new_order.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def _export_for_ui_with_invoice(self):
        """Export order with invoice number, amount, link, and rendered WhatsApp message"""
        data = super(PosOrder, self)._export_for_ui() if hasattr(super(), "_export_for_ui") else {}

        if self.account_move:
            invoice = self.account_move.sudo()
            partner = self.partner_id
            config = self.session_id.config_id
            template = config.whatsapp_template_id

            invoice_link = invoice.get_portal_url()
            full_invoice_link = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}{invoice_link}"

            # Render WhatsApp message if template exists
            message = ""
            if template and template.message:
                extra = {
                    "invoice_name": invoice.name,  # Add this line
                    "invoice_amount": f"{invoice.amount_total:,.2f} {invoice.currency_id.symbol}",
                    "invoice_link": full_invoice_link,
                }
                message = self.env["whatsapp.template"].render_template(
                    template.message,
                    partner,
                    extra_context=extra,
                )

            data.update({
                'id': self.id,
                'pos_reference': self.pos_reference,
                'amount_total': self.amount_total,
                'invoice_name': invoice.name,
                'invoice_link': invoice.get_portal_url(),
                'invoice_amount': f"{invoice.amount_total:,.2f} {invoice.currency_id.symbol} " if invoice.amount_total else False,
                'whatsapp_message': message,
            })
        return data

    @api.model
    def _get_open_order(self, order):
        existing_order = super()._get_open_order(order)
        # Orders created in the backend without a uuid get a new one in the PoS, so match
        # them by their server id instead of creating a duplicate order.
        if not existing_order and isinstance(order.get('id'), int):
            existing_order = self.search([('id', '=', order['id']), ('uuid', '=', False)], limit=1)
            if existing_order:
                existing_order.uuid = order.get('uuid')
        return existing_order

    @api.model
    def _process_order(self, order, existing_order):
        # The PoS can send an order without its session (e.g. a session that is not loaded
        # anymore): use the order's own session, else the one in its reference, instead of
        # failing on the required session_id.
        if not order.get('session_id'):
            session = existing_order.session_id if existing_order else self._get_session_from_reference(order)
            if session:
                _logger.warning("PoS order %s received without session, using session %s",
                                order.get('name'), session.name)
                order['session_id'] = session.id
        return super()._process_order(order, existing_order)

    @api.model
    def _fill_missing_uuids(self):
        """Give a uuid to orders, lines and payments copied in the backend without one."""
        for model in ('pos.order', 'pos.order.line', 'pos.payment'):
            for record in self.env[model].search([('uuid', 'in', (False, ''))]):
                record.uuid = str(uuid4())

    @api.model
    def _get_session_from_reference(self, order):
        match = POS_REFERENCE_SESSION_RE.search(order.get('name') or '')
        if match:
            return self.env['pos.session'].browse(int(match.group(1))).exists()
        return self.env['pos.session']

    @api.model
    def sync_from_ui(self, orders):
        res = super().sync_from_ui(orders)
        if "pos.order" in res:
            for order in res["pos.order"]:
                pos = self.browse(order["id"])
                invoice = pos.account_move.sudo() if pos.account_move else None
                config = pos.session_id.config_id
                template = config.whatsapp_template_id
                partner = pos.partner_id
                if invoice and template:
                    invoice_link = invoice.get_portal_url()
                    full_invoice_link = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}{invoice_link}"

                    message = self.env["whatsapp.template"].render_template(
                        template.message,
                        partner,
                        extra_context={
                            "invoice_name": invoice.name,
                            "invoice_amount": f"{invoice.amount_total:,.2f} {invoice.currency_id.symbol}",
                            "invoice_link": full_invoice_link,
                        },
                    )

                    order["whatsapp_message"] = message
                else:
                    order["whatsapp_message"] = False
        return res

