# -*- coding: utf-8 -*-
import logging
import re
import time

import requests

from odoo import http
from odoo.http import request
from datetime import date

_logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Name of the honeypot field rendered (hidden via CSS) in every public
# form. Real visitors never see or fill it; simple bots that
# auto-fill every input on a page do - if it comes back non-empty we
# silently drop the submission without telling the caller anything
# was wrong (so scripted bots don't learn to avoid this field).
HONEYPOT_FIELD = 'company_url'


class DekadWebsiteController(http.Controller):

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _base_values(self, active_page, title, description):
        return {
            'active_page': active_page,
            'page_title': title,
            'page_description': description,
            'current_year': date.today().year,
            'recaptcha_site_key': self._get_recaptcha_site_key(),
        }

    def _get_recaptcha_site_key(self):
        return request.env['ir.config_parameter'].sudo().get_param(
            'dekad_website.recaptcha_site_key'
        )

    def _is_spam_honeypot(self, kwargs):
        return bool((kwargs.get(HONEYPOT_FIELD) or '').strip())

    def _is_valid_email(self, email):
        return bool(_EMAIL_RE.match(email or ''))

    def _check_rate_limit(self, form_key, seconds=20):
        """Very light per-session throttle: refuse if this same browser
        session already submitted this form in the last `seconds`
        seconds. Not a substitute for reCAPTCHA against determined
        bots, but it stops naive rapid-fire spam scripts for free."""
        session_key = '_ve_last_submit_%s' % form_key
        last = request.session.get(session_key)
        now = time.time()
        if last and (now - last) < seconds:
            return False
        request.session[session_key] = now
        return True

    def _verify_recaptcha(self, token):
        """Verify a Google reCAPTCHA v3 token server-side. Returns True
        if reCAPTCHA isn't configured yet (fail-open, so leads aren't
        lost before you've set up your keys), or if Google's API is
        unreachable (fail-open, so a Google outage never blocks your
        forms). Only returns False for a token Google actively scored
        as low-confidence / invalid."""
        secret = request.env['ir.config_parameter'].sudo().get_param(
            'dekad_website.recaptcha_secret_key'
        )
        if not secret:
            return True
        if not token:
            return False
        try:
            resp = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': secret,
                    'response': token,
                    'remoteip': request.httprequest.remote_addr,
                },
                timeout=5,
            )
            result = resp.json()
        except Exception:
            _logger.warning("reCAPTCHA verification request failed", exc_info=True)
            return True
        if not result.get('success'):
            return False
        score = result.get('score')
        if score is not None and score < 0.5:
            return False
        return True

    def _passes_spam_checks(self, kwargs, form_key):
        """Runs honeypot + rate-limit + reCAPTCHA together. Returns
        (ok, is_honeypot) - is_honeypot lets the caller silently
        pretend success instead of showing a visible error, since a
        honeypot hit means it's almost certainly a bot, not a
        confused real visitor."""
        if self._is_spam_honeypot(kwargs):
            return False, True
        if not self._check_rate_limit(form_key):
            return False, False
        if not self._verify_recaptcha(kwargs.get('g-recaptcha-response')):
            return False, False
        return True, False

    # ---------------------------------------------------------
    # Pages
    # ---------------------------------------------------------
    @http.route(['/', '/home'], type='http', auth='public', website=True, sitemap=True)
    def dekad_home(self, **kwargs):
        values = self._base_values(
            'home',
            'Dekad Software Solutions - Odoo ERP Development & Consulting',
            'Dekad Software Solutions - Custom Odoo ERP implementation, integration, and support services.',
        )
        # Latest 3 published blog posts, for the "Latest Insights" section.
        # Kept to well-known fields only (name/subtitle/website_url/post_date/
        # author) - cover images can be wired up once we confirm the exact
        # field/route your website_blog version exposes for them.
        values['latest_posts'] = request.env['blog.post'].sudo().search(
            [('website_published', '=', True)],
            order='post_date desc',
            limit=3,
        )
        # Featured clients for the homepage "Our Clients" section - 8 cards
        # (2 rows of 4, matching the Industries grid), with a "See more"
        # link to the full /clients page for the rest.
        values['home_clients'] = request.env['dekad.client'].sudo().search(
            [('is_published', '=', True)],
            order='sequence, name',
            limit=8,
        )
        values['has_more_clients'] = request.env['dekad.client'].sudo().search_count(
            [('is_published', '=', True)]
        ) > len(values['home_clients'])
        if kwargs.get('subscribed'):
            values['form_sent'] = True
        return request.render('dekad_website.page_home', values)

    # TEMPORARILY DISABLED - Home v2 (alternate split-panel hero homepage,
    # kept in the codebase for reference; route disabled on request).
    # @http.route('/home-v2', type='http', auth='public', website=True, sitemap=True)
    # def dekad_home_v2(self, **kwargs):
    #     """Alternate homepage with the original split-panel hero, kept
    #     alongside the main '/' homepage (full-bleed hero) for comparison."""
    #     values = self._base_values(
    #         'home',
    #         'Dekad Software Solutions - Odoo ERP Development & Consulting',
    #         'Dekad Software Solutions - Custom Odoo ERP implementation, integration, and support services.',
    #     )
    #     values['latest_posts'] = request.env['blog.post'].sudo().search(
    #         [('website_published', '=', True)],
    #         order='post_date desc',
    #         limit=3,
    #     )
    #     values['home_clients'] = request.env['dekad.client'].sudo().search(
    #         [('is_published', '=', True)],
    #         order='sequence, name',
    #         limit=8,
    #     )
    #     values['has_more_clients'] = request.env['dekad.client'].sudo().search_count(
    #         [('is_published', '=', True)]
    #     ) > len(values['home_clients'])
    #     if kwargs.get('subscribed'):
    #         values['form_sent'] = True
    #     return request.render('dekad_website.page_home_v2', values)

    @http.route('/clients', type='http', auth='public', website=True, sitemap=True)
    def dekad_clients_index(self, **kwargs):
        values = self._base_values(
            'clients',
            'Our Clients — Dekad Software Solutions',
            'Businesses that trust Dekad Software Solutions for their Odoo ERP needs.',
        )
        values['clients'] = request.env['dekad.client'].sudo().search(
            [('is_published', '=', True)],
            order='sequence, name',
        )
        return request.render('dekad_website.clients_index_template', values)

    @http.route('/clients/<string:slug>', type='http', auth='public', website=True, sitemap=True)
    def dekad_client_detail(self, slug=None, **kwargs):
        client = request.env['dekad.client'].sudo().search(
            [('slug', '=', slug), ('is_published', '=', True)], limit=1
        )
        if not client:
            return request.not_found()
        values = self._base_values(
            'clients',
            f"{client.name} — Dekad Software Solutions Client",
            client.short_description or '',
        )
        values['client'] = client
        return request.render('dekad_website.client_detail_template', values)

    @http.route('/newsletter-subscribe', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def dekad_newsletter_subscribe(self, **kwargs):
        ok, _is_hp = self._passes_spam_checks(kwargs, 'newsletter')
        email = (kwargs.get('email') or '').strip()
        if ok and email and self._is_valid_email(email):
            request.env['dekad.contact.submission'].sudo().create({
                'submission_type': 'newsletter',
                'name': email,
                'email': email,
            })
            return request.redirect('/?subscribed=1#newsletter-section')
        return request.redirect('/')

    # TEMPORARILY DISABLED - About Us page (real content not ready yet).
    # Uncomment to re-enable; the page/template itself is untouched.
    # @http.route('/about', type='http', auth='public', website=True, sitemap=True)
    # def dekad_about(self, **kwargs):
    #     values = self._base_values(
    #         'about',
    #         'About Us — Dekad Software Solutions',
    #         'Learn about Dekad Software Solutions — our story, team, mission, and values.',
    #     )
    #     return request.render('dekad_website.page_about', values)

    @http.route('/privacy-policy', type='http', auth='public', website=True, sitemap=True)
    def dekad_privacy(self, **kwargs):
        values = self._base_values(
            'privacy',
            'Privacy Policy — Dekad Software Solutions',
            'Read how Dekad Software Solutions collects, uses, and protects your personal information.',
        )
        return request.render('dekad_website.page_privacy', values)

    # NOTE: /elements (UI component showcase page from the original
    # template) was removed - unreachable from any nav/footer link and
    # served no real purpose for the live site.

    # NOTE: The static /insights and /insights/<slug> demo pages were
    # removed in favor of Odoo's own website_blog app (real posts,
    # editable from the frontend, tags, etc.) - see /blog instead.

    @http.route('/contact', type='http', auth='public', website=True, sitemap=True, methods=['GET', 'POST'], csrf=True)
    def dekad_contact(self, **kwargs):
        values = self._base_values(
            'contact',
            'Contact Us — Dekad Software Solutions',
            'Get in touch with Dekad Software Solutions — book a free consultation today.',
        )

        if request.httprequest.method == 'POST':
            ok, is_honeypot = self._passes_spam_checks(kwargs, 'contact')
            name = (kwargs.get('name') or '').strip()
            email = (kwargs.get('email') or '').strip()
            phone = (kwargs.get('phone') or '').strip()
            service = (kwargs.get('service') or '').strip() or False
            message = (kwargs.get('message') or '').strip()

            if is_honeypot:
                # Pretend success without creating anything - don't
                # tip off the bot that it was caught.
                return request.redirect('/contact?sent=1')

            if ok and name and email and self._is_valid_email(email):
                request.env['dekad.contact.submission'].sudo().create({
                    'submission_type': 'contact',
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'service': service,
                    'message': message,
                })
                # Post/Redirect/Get: redirect to a plain GET instead of
                # rendering the POST result directly, so refreshing the
                # confirmation page never re-triggers the browser's "resend
                # form data?" prompt (and never creates a duplicate record).
                return request.redirect('/contact?sent=1')
            else:
                values['form_error'] = True

        if kwargs.get('sent'):
            values['form_sent'] = True

        return request.render('dekad_website.page_contact', values)

    # ---------------------------------------------------------
    # Request Demo / Free Consultation -> dekad.contact.submission
    # ---------------------------------------------------------
    _SERVICE_LABELS = {
        'odoo-consultancy': 'Odoo Consultancy',
        'odoo-implementation': 'Odoo Implementation',
        'odoo-integration': 'Odoo Integration',
        'odoo-support': 'Odoo Support',
        'odoo-migration': 'Odoo Migration',
        'odoo-web-design': 'Odoo Web Design',
    }

    def _create_submission(self, kwargs, submission_type):
        """Create a dekad.contact.submission from a Request Demo / Free
        Consultation form and return it, or False if required fields are
        missing or invalid."""
        name = (kwargs.get('name') or '').strip()
        email = (kwargs.get('email') or '').strip()
        if not (name and email and self._is_valid_email(email)):
            return False

        return request.env['dekad.contact.submission'].sudo().create({
            'submission_type': submission_type,
            'name': name,
            'email': email,
            'phone': (kwargs.get('phone') or '').strip(),
            'company': (kwargs.get('company') or '').strip(),
            'message': (kwargs.get('message') or '').strip(),
        })

    @http.route('/request-demo', type='http', auth='public', website=True, sitemap=True, methods=['GET', 'POST'], csrf=True)
    def dekad_request_demo(self, **kwargs):
        values = self._base_values(
            'request-demo',
            'Request a Demo — Dekad Software Solutions',
            'Request a live demo of our Odoo ERP services.',
        )
        if request.httprequest.method == 'POST':
            ok, is_honeypot = self._passes_spam_checks(kwargs, 'request-demo')
            if is_honeypot:
                return request.redirect('/request-demo?sent=1')
            if ok and self._create_submission(kwargs, 'demo'):
                return request.redirect('/request-demo?sent=1')
            else:
                values['form_error'] = True
        if kwargs.get('sent'):
            values['form_sent'] = True
        return request.render('dekad_website.page_request_demo', values)

    @http.route('/free-consultation', type='http', auth='public', website=True, sitemap=True, methods=['GET', 'POST'], csrf=True)
    def dekad_free_consultation(self, **kwargs):
        values = self._base_values(
            'free-consultation',
            'Book a Free Consultation — Dekad Software Solutions',
            'Book a free consultation with our Odoo ERP experts.',
        )
        if request.httprequest.method == 'POST':
            ok, is_honeypot = self._passes_spam_checks(kwargs, 'free-consultation')
            if is_honeypot:
                return request.redirect('/free-consultation?sent=1')
            if ok and self._create_submission(kwargs, 'consultation'):
                return request.redirect('/free-consultation?sent=1')
            else:
                values['form_error'] = True
        if kwargs.get('sent'):
            values['form_sent'] = True
        return request.render('dekad_website.page_free_consultation', values)