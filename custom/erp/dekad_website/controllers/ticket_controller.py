# -*- coding: utf-8 -*-
import base64
import logging
import os
from datetime import date
from urllib.parse import quote

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Only common, non-executable document/image/archive formats are accepted
# as ticket attachments - this blocks scripts and executables (.exe, .php,
# .sh, .js, .html, .svg...) that could otherwise be uploaded and later
# opened by a staff member, or (if ever served directly) run in a browser.
ALLOWED_ATTACHMENT_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.zip',
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

# Known file signatures ("magic bytes") for every extension above, keyed
# by the *category* of container format - checking these against the
# actual uploaded bytes (not just trusting the filename) stops an
# attacker from bypassing the extension whitelist by simply renaming a
# malicious file (e.g. shell.php -> shell.jpg would fail this check
# even though it passed the extension check).
_MAGIC_SIGNATURES = {
    'jpeg': [b'\xff\xd8\xff'],
    'png':  [b'\x89PNG\r\n\x1a\n'],
    'gif':  [b'GIF87a', b'GIF89a'],
    'webp': [b'RIFF'],  # 'WEBP' also appears at byte offset 8, checked separately below
    'pdf':  [b'%PDF-'],
    'zip_container': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],  # .zip, .docx, .xlsx, .pptx (all zip-based)
    'ole_container': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],          # legacy .doc, .xls, .ppt
}
_EXT_TO_CATEGORIES = {
    '.jpg': ['jpeg'], '.jpeg': ['jpeg'],
    '.png': ['png'],
    '.gif': ['gif'],
    '.webp': ['webp'],
    '.pdf': ['pdf'],
    '.zip': ['zip_container'],
    '.docx': ['zip_container'], '.xlsx': ['zip_container'], '.pptx': ['zip_container'],
    '.doc': ['ole_container'], '.xls': ['ole_container'], '.ppt': ['ole_container'],
    # .txt / .csv have no reliable magic bytes - validated by the
    # dangerous-signature blocklist below instead.
    '.txt': [], '.csv': [],
}
# Regardless of claimed extension, never accept content that starts with
# one of these - catches a malicious file renamed to *any* allowed
# extension, including .txt/.csv which have no magic bytes of their own.
_DANGEROUS_SIGNATURES = [
    b'MZ',           # Windows executable/DLL
    b'\x7fELF',      # Linux executable
    b'#!/',          # shebang script (sh, bash, python, php-cli...)
    b'<?php',
    b'<%',           # ASP/JSP
    b'<script',
    b'<html', b'<!DOCTYPE html',
]


def _validate_attachment_content(filename, content):
    """Returns an error message string if the upload should be rejected,
    or None if it's fine. Checks the real file bytes, not just the
    filename extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return ("That file type isn't allowed. Accepted formats: images, "
                "PDF, Word/Excel/PowerPoint, text, CSV, or zip.")

    header = content[:16]
    lowered = content[:200].lstrip().lower()
    for bad_sig in _DANGEROUS_SIGNATURES:
        if lowered.startswith(bad_sig) or header.startswith(bad_sig):
            return "This file's content doesn't match its file type and was rejected."

    categories = _EXT_TO_CATEGORIES.get(ext, [])
    if categories:
        matched = False
        for cat in categories:
            for sig in _MAGIC_SIGNATURES[cat]:
                if header.startswith(sig):
                    matched = True
                    break
            if matched:
                break
        if categories == ['webp'] and matched:
            # WEBP is a RIFF container - confirm the 'WEBP' tag at byte
            # offset 8 too, not just the generic RIFF header.
            matched = content[8:12] == b'WEBP'
        if not matched:
            return "This file's content doesn't match its file extension and was rejected."

    return None


class DekadTicketController(http.Controller):

    @http.route('/submit-ticket', type='http', auth='user', website=True, sitemap=True, methods=['GET', 'POST'], csrf=True)
    def submit_ticket(self, **kwargs):
        """auth='user' means only logged-in users (portal or internal) can
        reach this page - an unauthenticated visitor is automatically
        redirected to /web/login?redirect=/submit-ticket by Odoo itself."""
        partner = request.env.user.partner_id
        tags = request.env['helpdesk.tag'].sudo().search([])

        values = {
            'active_page': 'submit-ticket',
            'page_title': 'Submit a Ticket — Dekad Software Solutions',
            'page_description': 'Submit a support ticket to the Dekad Software Solutions helpdesk.',
            'partner': partner,
            'tags': tags,
            'current_year': date.today().year,
        }

        if request.httprequest.method == 'POST':
            # Honeypot: silently pretend success if the hidden field got
            # filled in (almost certainly a bot, not a real visitor).
            if (kwargs.get('company_url') or '').strip():
                return request.redirect('/submit-ticket?sent=1')

            subject = (kwargs.get('name') or '').strip()
            description = (kwargs.get('description') or '').strip()
            partner_name = (kwargs.get('partner_name') or '').strip()
            partner_email = (kwargs.get('partner_email') or '').strip()
            company_name = (kwargs.get('partner_company_name') or '').strip()

            attachment = request.httprequest.files.get('attachment')
            attachment_bytes = None
            if attachment and attachment.filename:
                attachment_bytes = attachment.read()

                if len(attachment_bytes) > MAX_ATTACHMENT_SIZE:
                    values['form_error'] = True
                    values['form_error_message'] = "The attached file is too large (10 MB max)."
                    return request.render('dekad_website.ticket_submit_template', values)

                content_error = _validate_attachment_content(attachment.filename, attachment_bytes)
                if content_error:
                    values['form_error'] = True
                    values['form_error_message'] = content_error
                    return request.render('dekad_website.ticket_submit_template', values)

            tag_ids = request.httprequest.form.getlist('tag_ids')

            if subject and description and partner_name and partner_email and tag_ids:
                # Same partner-matching mechanism Odoo's own website_helpdesk
                # module uses: look up (or create) the res.partner by the
                # submitted email, rather than always trusting the logged-in
                # session's own partner_id - the visitor may have edited the
                # email field to someone else's before submitting.
                if request.env.user.email == partner_email:
                    matched_partner = partner
                else:
                    matched_partner = request.env['res.partner'].sudo().search(
                        [('email', '=', partner_email)], limit=1
                    )
                    if not matched_partner:
                        matched_partner = request.env['res.partner'].sudo().create({
                            'email': partner_email,
                            'name': partner_name,
                            'phone': (kwargs.get('partner_phone') or '').strip(),
                            'company_name': company_name,
                        })

                # Same mechanism Odoo's own website_helpdesk module uses:
                # no custom setting of ours - just whichever team(s) have
                # the native "Use for Website Form" flag enabled, managed
                # entirely from the Helpdesk app's own team configuration.
                # Multi-company / multi-website: filtered by website_id,
                # exactly like Odoo's own website_helpdesk module does -
                # team.website_id is itself computed from team.company_id
                # (team.company_id.website_id), and Odoo enforces via a
                # model constraint that a team's company always matches
                # its website's company, so filtering by website_id alone
                # is enough to guarantee the team belongs to this site's
                # own company - it can never pull in a team from another
                # company/website by mistake.
                team = request.env['helpdesk.team'].sudo().search(
                    [('use_website_helpdesk_form', '=', True), ('website_id', '=', request.website.id)],
                    limit=1
                )
                if not team:
                    team = request.env['helpdesk.team'].sudo().search(
                        [('website_id', '=', request.website.id)], limit=1
                    )
                if not team:
                    team = request.env['helpdesk.team'].sudo().search([], limit=1)

                full_description = description
                if company_name:
                    full_description = f"Company: {company_name}\n\n{description}"

                ticket_vals = {
                    'name': subject,
                    'description': full_description,
                    'partner_id': matched_partner.id,
                    'partner_name': partner_name,
                    'partner_email': partner_email,
                    'partner_phone': (kwargs.get('partner_phone') or '').strip(),
                    'tag_ids': [(6, 0, [int(t) for t in tag_ids])] if tag_ids else False,
                }
                if team:
                    ticket_vals['team_id'] = team.id

                ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)

                if attachment_bytes is not None:
                    ticket_attachment = request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        # ir.attachment.datas expects base64 - encoding the
                        # raw upload here (a plain file.read() would silently
                        # corrupt the stored file).
                        'datas': base64.b64encode(attachment_bytes),
                        'res_model': 'helpdesk.ticket',
                        'res_id': ticket.id,
                    })
                    # Same as Odoo's own website_helpdesk module: give the
                    # attachment an access token so the ticket's own
                    # portal user can view/download it later from their
                    # portal account, even though it wasn't uploaded
                    # through the backend chatter.
                    ticket_attachment.generate_access_token()

                redirect_url = '/submit-ticket?sent=1'
                if ticket.ticket_ref:
                    redirect_url += '&ref=%s' % quote(ticket.ticket_ref)
                return request.redirect(redirect_url)
            else:
                values['form_error'] = True

        if kwargs.get('sent'):
            values['form_sent'] = True
            values['ticket_ref'] = kwargs.get('ref')

        return request.render('dekad_website.ticket_submit_template', values)