from odoo import _, models, fields
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_laundry_report_emails = fields.Char(related="pos_config_id.laundry_report_emails", readonly=False)
    pos_laundry_auto_close = fields.Boolean(related="pos_config_id.laundry_auto_close", readonly=False)
    pos_laundry_auto_close_time = fields.Float(related="pos_config_id.laundry_auto_close_time", readonly=False)
    pos_laundry_auto_close_grace = fields.Integer(related="pos_config_id.laundry_auto_close_grace", readonly=False)
    pos_laundry_tz = fields.Char(related="pos_config_id.laundry_tz")
    pos_laundry_free_delivery_from = fields.Float(related="pos_config_id.laundry_free_delivery_from", readonly=False)
    pos_laundry_delivery_product_id = fields.Many2one(
        related="pos_config_id.laundry_delivery_product_id", readonly=False)
    laundry_statement_whatsapp_message = fields.Char(
        string="Statement WhatsApp Message",
        config_parameter="london_laundry_implementation.statement_whatsapp_message",
        help="Text of the WhatsApp message sent with the customer statement. Placeholders: "
             "{{partner_name}}, {{company}}, {{date_from}}, {{date_to}}, {{previous_balance}}, {{invoiced}}, "
             "{{invoice_count}}, {{open_count}}, {{paid}}, {{remaining}}, {{total_due}}, {{statement_link}}. "
             "Empty = the default message.")

    laundry_ready_whatsapp_message = fields.Char(
        string="Order Ready WhatsApp Message",
        config_parameter="london_laundry_implementation.ready_whatsapp_message",
        help="Text of the WhatsApp 'order ready' message. Placeholders: {{partner_name}}, {{order}}, "
             "{{amount}}, {{balance}}, {{invoice_link}}, {{company}}. Empty = the default Arabic/English message.")

    def action_send_laundry_daily_report_now(self):
        """Send yesterday's summary of the selected point of sale right away (test / on demand)."""
        self.ensure_one()
        config = self.pos_config_id
        # the button does not save the settings first: write the e-mails typed on screen
        if config.laundry_report_emails != self.pos_laundry_report_emails:
            config.laundry_report_emails = self.pos_laundry_report_emails
        if not config._laundry_report_email_list():
            raise UserError(_("Please enter at least one e-mail address for the daily report."))
        report = self.env["london.laundry.daily.report"]
        mail = report._send_config_report(config, report._report_day(config))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if mail.state != "exception" else "warning",
                "message": _("Daily report sent to %s", mail.email_to) if mail.state != "exception"
                           else _("The daily report could not be sent: %s", mail.failure_reason or ""),
            },
        }
