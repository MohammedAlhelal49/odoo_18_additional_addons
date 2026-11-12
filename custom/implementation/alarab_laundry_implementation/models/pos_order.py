import logging

from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.addons.web.controllers.utils import clean_action

_logger = logging.getLogger(__name__)



class PosReceipt(models.Model):
    """
        This is an Odoo model for Point of Sale (POS).
        It creates a new model of pos.receipt for providing different types of
        receipt design.
    """
    _name = 'pos.receipt'
    _description = 'POS Receipts'

    name = fields.Char(string='Name', help='Name of the pos receipt')
    design_receipt = fields.Text(string='Receipt XML',
                                 help='Add your customised receipts for pos')

class PosOrder(models.Model):
    _inherit = "pos.order"

    wa_phone_valid = fields.Boolean(
        string="Valid WhatsApp number", compute="_compute_wa_phone_valid")

    @api.depends("partner_id.mobile", "partner_id.phone", "partner_id.country_id")
    def _compute_wa_phone_valid(self):
        link = self.env["alarab.whatsapp.link"]
        for order in self:
            order.wa_phone_valid = bool(order.partner_id and link.normalize_phone(order.partner_id))

    # ------------------------------------------------------------------
    # WhatsApp Web (wa.me): the employee opens a pre-filled chat and presses send.
    # ------------------------------------------------------------------
    def _wa_render(self, template_xmlid, with_invoice=False):
        self.ensure_one()
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            raise UserError(_("The WhatsApp template %s was deleted.", template_xmlid))
        extra = {
            "pos_order_name": self.pos_reference or self.name or "",
            "pos_order_amount": ("%.2f %s" % (self.amount_total, self.currency_id.name or "")).strip(),
        }
        if with_invoice and self.account_move:
            # The user can read this order, so exposing its own invoice link is fine
            # even for cashiers without accounting rights.
            invoice = self.account_move.sudo()
            extra.update({
                "invoice_name": invoice.name or "",
                "invoice_amount": ("%.2f %s" % (invoice.amount_total, invoice.currency_id.name or "")).strip(),
                "invoice_link": invoice.get_base_url() + invoice._get_share_url(),
            })
        return self.env["whatsapp.template"].render_template(
            template.message, self.partner_id, extra_context=extra)

    def _wa_get_url(self, kind):
        """kind: 'invoice' or 'ready'. Returns the wa.me URL, or False if it cannot be built."""
        self.ensure_one()
        if not self.partner_id:
            return False
        if kind == "invoice" and not self.account_move:
            return False
        link = self.env["alarab.whatsapp.link"]
        phone = link.normalize_phone(self.partner_id)
        if not phone:
            return False
        if kind == "invoice":
            text = self._wa_render("alarab_laundry_implementation.whatsapp_invoice_template_v2", True)
        else:
            text = self._wa_render("alarab_laundry_implementation.whatsapp_pos_ready_template")
        return link.build_url(phone, text)

    def _wa_open_action(self, kind, log_message):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("This order has no customer."))
        if not self.env["alarab.whatsapp.link"].normalize_phone(self.partner_id):
            raise UserError(_("The customer's phone number is missing or invalid."))
        url = self._wa_get_url(kind)
        if not url:
            raise UserError(_("This order has no invoice yet."))
        self.message_post(body=log_message)
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}

    def action_send_whatsapp(self):
        """Manual 'order ready' message."""
        return self._wa_open_action(
            "ready", _("WhatsApp Web opened with the 'order ready' message."))

    def action_send_whatsapp_invoice(self):
        """Manual (re)open of the invoice message."""
        return self._wa_open_action(
            "invoice", _("WhatsApp Web opened with the invoice message."))

    def get_whatsapp_invoice_url(self):
        """Called by the POS after invoicing from the ticket screen."""
        self.ensure_one()
        return self._wa_get_url("invoice")

    def action_pos_order_invoice(self):
        res = super().action_pos_order_invoice()
        # Only for the backend "Invoice" button (it passes this context key);
        # POS RPC calls and the customer self-invoicing portal are not affected.
        if self.env.context.get("alarab_wa_open") and len(self) == 1 and res:
            url = self._wa_get_url("invoice")
            if url:
                self.message_post(body=_("WhatsApp Web opened with the invoice message."))
                # The web client only normalizes the top-level action (fills `views`),
                # so normalize the nested one ourselves.
                return {
                    "type": "ir.actions.client",
                    "tag": "alarab_open_whatsapp",
                    "params": {"url": url, "next": clean_action(dict(res), self.env)},
                }
        return res

    def _export_for_ui_with_invoice(self):
        """ export order with invoice number"""
        data = super(PosOrder, self)._export_for_ui() if hasattr(super(), "_export_for_ui") else {}
        # fallback if no super
        data.update({
            'id': self.id,
            'pos_reference': self.pos_reference,
            'amount_total': self.amount_total,
            'invoice_number': self.account_move.sudo().name if self.account_move else False,
        })
        return data

    @api.model
    def sync_from_ui(self, orders):
        """Override sync_from_ui to inject invoice_number in response"""
        res = super().sync_from_ui(orders)
        if "pos.order" in res:
            for order in res["pos.order"]:
                pos = self.browse(order["id"])
                order["invoice_number"] = pos.account_move.sudo().name if pos.account_move else False
                # WhatsApp link for the payment screen (read-only; must never break the sync)
                order["alarab_wa_invoice_url"] = False
                if pos.account_move:
                    try:
                        with self.env.cr.savepoint():
                            order["alarab_wa_invoice_url"] = pos._wa_get_url("invoice")
                    except Exception:  # noqa: BLE001
                        _logger.exception("WhatsApp: could not build invoice link for %s", pos.name)
        return res
