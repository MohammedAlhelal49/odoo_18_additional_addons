# -*- coding: utf-8 -*-
import re
from datetime import date

from odoo import http
from odoo.http import request

from . import content

PHONE_RE = re.compile(r'^\+?[0-9\s\-()]{7,20}$')


class AlomranEngineeringWebsite(http.Controller):

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _is_en(self):
        return not (request.env.lang or 'en_US').startswith('ar')

    def _other_lang_code(self, is_en):
        """Code of the language the switcher points to (first active ar/en lang of the website)."""
        prefix = 'en' if not is_en else 'ar'
        lang = request.website.language_ids.filtered(lambda l: l.code.startswith(prefix))[:1]
        return lang.code if lang else False

    def _values(self, active_page, page, **extra):
        is_en = self._is_en()
        values = {
            'is_en': is_en,
            'dir': 'ltr' if is_en else 'rtl',
            'c': content.common(is_en),
            'company': content.COMPANY,
            'services': content.services(is_en),
            'form': content.form(is_en),
            'cta': content.cta(is_en),
            'page': page,
            'active_page': active_page,
            'other_lang': self._other_lang_code(is_en),
            'current_year': date.today().year,
            # consumed by website.layout for <title> and <meta name="description">
            'title': page.get('title'),
            'website_meta_description': page.get('description'),
            'pc': content.projects_page(is_en),
        }
        values.update(extra)
        return values

    def _localized(self, url):
        return request.env['ir.http']._url_for(url)

    def _projects(self, limit=None, featured=False):
        domain = [('is_published', '=', True)]
        if featured:
            domain.append(('is_featured', '=', True))
        return request.env['alomran.eng.project'].search(domain, limit=limit)

    # ---------------------------------------------------------
    # Pages
    # ---------------------------------------------------------
    @http.route(['/', '/home'], type='http', auth='public', website=True, sitemap=True)
    def aoe_home(self, **kwargs):
        is_en = self._is_en()
        projects = self._projects(limit=6, featured=True) or self._projects(limit=6)
        return request.render('alomran_engineering_website.page_home', self._values(
            'home', content.home(is_en),
            process=content.process(is_en),
            projects=projects,
        ))

    @http.route('/about', type='http', auth='public', website=True, sitemap=True)
    def aoe_about(self, **kwargs):
        return request.render('alomran_engineering_website.page_about', self._values(
            'about', content.about(self._is_en()),
        ))

    @http.route('/services', type='http', auth='public', website=True, sitemap=True)
    def aoe_services(self, **kwargs):
        is_en = self._is_en()
        return request.render('alomran_engineering_website.page_services', self._values(
            'services', content.services_page(is_en),
            process=content.process(is_en),
        ))

    @http.route('/projects', type='http', auth='public', website=True, sitemap=True)
    def aoe_projects(self, **kwargs):
        projects = self._projects()
        return request.render('alomran_engineering_website.page_projects', self._values(
            'projects', content.projects_page(self._is_en()),
            projects=projects,
            used_categories=list(dict.fromkeys(projects.mapped('category'))),
        ))

    @http.route('/projects/<int:project_id>', type='http', auth='public', website=True, sitemap=False)
    def aoe_project_detail(self, project_id, **kwargs):
        project = request.env['alomran.eng.project'].search(
            [('id', '=', project_id), ('is_published', '=', True)], limit=1)
        if not project:
            raise request.not_found()
        page = dict(content.projects_page(self._is_en()))
        page['title'] = '%s | %s' % (project.name, content.common(self._is_en())['company_full'])
        page['description'] = project.summary or page['description']
        others = self._projects(limit=4).filtered(lambda p: p != project)[:3]
        return request.render('alomran_engineering_website.page_project_detail', self._values(
            'projects', page, project=project, others=others,
        ))

    @http.route('/contact', type='http', auth='public', website=True, sitemap=True)
    def aoe_contact(self, **kwargs):
        return request.render('alomran_engineering_website.page_contact', self._values(
            'contact', content.contact_page(self._is_en()),
            form_sent=kwargs.get('sent') == '1',
            form_error=kwargs.get('error') == '1',
        ))

    @http.route('/contact/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True, sitemap=False)
    def aoe_contact_submit(self, **post):
        # Honeypot: bots fill the hidden "website" field, humans never see it.
        if post.get('website'):
            return request.redirect(self._localized('/contact?sent=1#aoe-form'))

        name = (post.get('name') or '').strip()[:120]
        phone = (post.get('phone') or '').strip()[:30]
        if not name or not PHONE_RE.match(phone):
            return request.redirect(self._localized('/contact?error=1#aoe-form'))

        service_key = (post.get('service') or '').strip()
        service_titles = {s['key']: s['title'] for s in content.services(True)}
        emirate = post.get('emirate') if post.get('emirate') in dict(content.form(True)['emirates']) else False

        request.env['alomran.eng.inquiry'].create_from_website({
            'name': name,
            'phone': phone,
            'email': (post.get('email') or '').strip()[:120] or False,
            'service': service_titles.get(service_key, 'Other'),
            'emirate': emirate,
            'message': (post.get('message') or '').strip()[:4000] or False,
            'lang': request.env.lang,
            'source_page': (post.get('source_page') or '')[:200] or False,
        })
        return request.redirect(self._localized('/contact?sent=1#aoe-form'))
