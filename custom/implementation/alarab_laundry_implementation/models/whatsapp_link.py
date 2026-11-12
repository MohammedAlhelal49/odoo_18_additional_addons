import logging
import urllib.parse

from odoo import api, models

_logger = logging.getLogger(__name__)


class AlarabWhatsappLink(models.AbstractModel):
    _name = "alarab.whatsapp.link"
    _description = "WhatsApp Web link helper"

    @api.model
    def normalize_phone(self, partner):
        """Partner number as international digits without '+', or False if missing/invalid."""
        raw = partner.mobile or partner.phone
        if not raw:
            return False
        try:
            import phonenumbers
        except ImportError:
            _logger.warning("WhatsApp: python 'phonenumbers' is not installed, cannot validate numbers.")
            return False
        region = partner.country_id.code or self.env.company.country_id.code or "AE"
        try:
            number = phonenumbers.parse(raw, region)
        except phonenumbers.NumberParseException:
            return False
        if not phonenumbers.is_valid_number(number):
            return False
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164).lstrip("+")

    @api.model
    def build_url(self, phone, text):
        # safe="" so &, =, ?, # inside the message are encoded and never cut the text
        return "https://wa.me/%s?text=%s" % (phone, urllib.parse.quote(text or "", safe=""))
