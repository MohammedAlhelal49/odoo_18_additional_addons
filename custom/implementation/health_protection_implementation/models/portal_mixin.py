import base64

from odoo import models


class Base(models.AbstractModel):
    _inherit = 'base'

    def hp_footer_qr_url(self):
        """Link of the QR code printed in the footer of every document; False = the company website."""
        return False

    def hp_footer_qr_data_uri(self):
        """QR code printed in the footer (under the phone number) of every external document, as an inline PNG:
        the document's own link when it has one (hp_footer_qr_url), else the website (web.base.url)."""
        url = (len(self) == 1 and self.hp_footer_qr_url()) or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        png = self.env['ir.actions.report'].barcode('QR', url, width=300, height=300)
        return 'data:image/png;base64,' + base64.b64encode(png).decode()


class PortalMixin(models.AbstractModel):
    _inherit = 'portal.mixin'

    def hp_portal_url(self):
        """Full portal link (with access token) of this document, used by the printed QR code."""
        self.ensure_one()
        return self.get_base_url() + self.get_portal_url()

    def hp_portal_qr_data_uri(self):
        """QR code of hp_portal_url() as an inline PNG, so the PDF does not need to fetch it."""
        self.ensure_one()
        png = self.env['ir.actions.report'].barcode('QR', self.hp_portal_url(), width=300, height=300)
        return 'data:image/png;base64,' + base64.b64encode(png).decode()

    def hp_show_portal_qr(self):
        """Whether the printed document shows the portal QR code (next to the stamp)."""
        return False

    def hp_footer_qr_url(self):
        self.ensure_one()
        return self.hp_show_portal_qr() and self.hp_portal_url()
