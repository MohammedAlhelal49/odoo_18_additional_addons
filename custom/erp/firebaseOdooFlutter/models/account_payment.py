import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        """Override to send FCM notification when a payment is posted."""
        skip_fcm = self.env.context.get('skip_fcm_notification')
        res = super(AccountPayment, self.with_context(skip_fcm_notification=True)).action_post()
        if not skip_fcm:
            for payment in self:
                payment.with_context(skip_fcm_notification=False)._send_payment_notification(payment, event='posted')
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Send FCM notification when a new payment is created."""
        skip_fcm = self.env.context.get('skip_fcm_notification')
        payments = super(AccountPayment, self.with_context(skip_fcm_notification=True)).create(vals_list)
        if not skip_fcm:
            for payment in payments:
                if payment.state != 'posted':
                    payment.with_context(skip_fcm_notification=False)._send_payment_notification(payment, event='created')
        return payments

    def _send_payment_notification(self, payment, event='posted'):
        """Send FCM notification to relevant users for a payment event."""
        if self.env.context.get('skip_fcm_notification'):
            return

        recipients = self.env['res.partner']

        # Notify creator / responsible user
        if payment.create_uid and payment.create_uid.partner_id:
            recipients |= payment.create_uid.partner_id

        # Notify partner (customer/vendor) user accounts
        if payment.partner_id and payment.partner_id.user_ids:
            for user in payment.partner_id.user_ids:
                recipients |= user.partner_id

        # Exclude current performing user
        current_partner = self.env.user.partner_id
        if current_partner:
            recipients -= current_partner

        if not recipients:
            return

        ref_str = f" ({payment.ref})" if payment.ref else ""
        partner_name = payment.partner_id.name or 'N/A'

        if event == 'posted':
            title = f"Payment Posted: {payment.name}"
            body = f"Payment {payment.name}{ref_str} for {partner_name} has been posted. Amount: {payment.amount:.2f} {payment.currency_id.name or ''}"
        else:
            title = f"New Payment: {payment.name or 'Draft'}"
            body = f"A new payment{ref_str} has been created for {partner_name}. Amount: {payment.amount:.2f} {payment.currency_id.name or ''}"

        fcm_data = {
            "type": "account_payment",
            "event": event,
            "model": "account.payment",
            "res_id": str(payment.id),
            "record_name": str(payment.name or ''),
            "body": body,
        }

        try:
            self.env['mail.thread'].sudo()._send_fcm_common(recipients, title, body, fcm_data)
        except Exception as e:
            _logger.error(f"Failed to send FCM for payment {payment.name}: {e}")
