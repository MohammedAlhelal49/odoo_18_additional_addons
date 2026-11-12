# -*- coding: utf-8 -*-
from odoo import models

from ..controllers.site_facts import DEFAULT_SITE_URL


class Website(models.Model):
    _inherit = 'website'

    def _alomran_site_url(self):
        """Public URL of the website for SEO data (schema.org JSON-LD):
        Website > Settings > Domain, else DEFAULT_SITE_URL. No trailing slash."""
        domain = ((self[:1].domain if self else '') or '').strip()
        if not domain:
            return DEFAULT_SITE_URL
        if '://' not in domain:
            domain = 'https://' + domain
        return domain.rstrip('/')
