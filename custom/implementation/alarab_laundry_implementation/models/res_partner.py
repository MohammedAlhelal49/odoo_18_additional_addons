import logging

from odoo import SUPERUSER_ID, api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _format_uae_number(self, phone):
        """Format a number as '+971 50 123 4567' (international format).

        Uses the partner's country (fallback AE) instead of assuming every number starting
        with 0 is Emirati. Returns False when the number is not valid, so it is never overwritten
        with something broken.
        """
        if not phone:
            return False
        try:
            import phonenumbers
        except ImportError:
            return False
        region = (self.country_id.code if len(self) == 1 else False) or "AE"
        try:
            number = phonenumbers.parse(phone, region)
        except phonenumbers.NumberParseException:
            return False
        if not phonenumbers.is_valid_number(number):
            return False
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    @api.model
    def _run_mobile_fix(self):
        """Normalize phone/mobile of all contacts. Idempotent: only writes what really changes."""
        try:
            import phonenumbers  # noqa: F401
        except ImportError:
            _logger.warning("Phone normalization skipped: python 'phonenumbers' is not installed.")
            return
        partners = self.with_context(active_test=False).search([
            "|", ("phone", "!=", False), ("mobile", "!=", False),
        ])
        changed = 0
        for partner in partners:
            vals = {}
            mobile = partner._format_uae_number(partner.mobile) if partner.mobile else False
            phone = partner._format_uae_number(partner.phone) if partner.phone else False
            if mobile and mobile != partner.mobile:
                vals["mobile"] = mobile
            if phone and phone != partner.phone:
                vals["phone"] = phone
            # keep the original behaviour: fill an empty mobile from a valid phone
            if not partner.mobile and phone:
                vals["mobile"] = phone
            if vals:
                partner.write(vals)
                changed += 1
        _logger.info("Phone normalization: %s contacts updated.", changed)

    @api.model
    def init(self):
        env = api.Environment(self._cr, SUPERUSER_ID, {})
        env["res.partner"]._run_mobile_fix()
