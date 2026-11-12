# -*- coding: utf-8 -*-
from datetime import date

from odoo import http
from odoo.http import request
from ..data.service_data import SERVICES_CATALOG
from ..data.translate_utils import localize


class DekadServiceController(http.Controller):

    @http.route(['/services', '/services/<string:service_slug>'], type='http', auth="public", website=True, sitemap=True)
    def render_service_page(self, service_slug=None, **kwargs):
        if not service_slug:
            return request.render('dekad_website.services_index_template', {
                'services': localize(SERVICES_CATALOG),
                'active_page': 'services',
                'current_year': date.today().year,
            })

        service = SERVICES_CATALOG.get(service_slug)
        if not service:
            return request.not_found()

        return request.render('dekad_website.master_service_template', {
            'page': localize(service),
            'active_page': 'services',
            'current_year': date.today().year,
        })