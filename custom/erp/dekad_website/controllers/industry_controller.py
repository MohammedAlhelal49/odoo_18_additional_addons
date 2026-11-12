# -*- coding: utf-8 -*-
from datetime import date

from odoo import http
from odoo.http import request
from ..data.industry_data import INDUSTRIES_CATALOG
from ..data.translate_utils import localize


class DekadIndustryController(http.Controller):

    @http.route(['/industries', '/industries/<string:industry_slug>'], type='http', auth="public", website=True, sitemap=True)
    def render_industry_page(self, industry_slug=None, **kwargs):
        if not industry_slug:
            return request.render('dekad_website.industries_index_template', {
                'industries': localize(INDUSTRIES_CATALOG),
                'active_page': 'industries',
                'current_year': date.today().year,
            })

        industry = INDUSTRIES_CATALOG.get(industry_slug)
        if not industry:
            return request.not_found()

        return request.render('dekad_website.master_industry_template', {
            'page': localize(industry),
            'active_page': 'industries',
            'current_year': date.today().year,
        })