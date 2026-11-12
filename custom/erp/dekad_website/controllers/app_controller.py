# -*- coding: utf-8 -*-
from datetime import date

from odoo import http
from odoo.http import request
from ..data.app_data import APPS_CATALOG
from ..data.translate_utils import localize


class DekadAppController(http.Controller):

    @http.route(['/apps', '/apps/<string:app_slug>'], type='http', auth="public", website=True, sitemap=True)
    def render_app_page(self, app_slug=None, **kwargs):
        if not app_slug:
            return request.render('dekad_website.apps_index_template', {
                'apps': localize(APPS_CATALOG),
                'active_page': 'apps',
                'current_year': date.today().year,
            })

        app_data = APPS_CATALOG.get(app_slug)
        if not app_data:
            return request.not_found()

        return request.render('dekad_website.master_app_template', {
            'page': localize(app_data),
            'active_page': 'apps',
            'current_year': date.today().year,
        })