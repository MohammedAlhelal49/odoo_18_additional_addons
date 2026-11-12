# -*- coding: utf-8 -*-
import base64
import logging
import os

from lxml import html as lxml_html

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DekadClientImportWizard(models.TransientModel):
    _name = 'dekad.client.import.wizard'
    _description = 'Import Clients from HTML + Logo Folder'

    html_file = fields.Binary(string='HTML File', required=True,
                               help="The HTML file containing one <div class=\"company-card\" "
                                    "data-title=\"...\" data-image=\"...\" data-text=\"...\"> per client.")
    html_filename = fields.Char(string='HTML Filename')
    logo_folder_path = fields.Char(string='Logos Folder Path (on the server)', required=True,
                                    help="Absolute path on the Odoo server's own filesystem where the logo "
                                         "image files are located, e.g. /home/odoo/client_logos. "
                                         "Each client's data-image filename is looked up in this folder.")
    result_summary = fields.Text(string='Result', readonly=True)

    def _find_logo_file(self, folder, image_ref):
        """Return the absolute path of the logo file matching image_ref's
        filename inside folder, or False if not found. Tries an exact
        filename match first, then a case-insensitive fallback."""
        basename = os.path.basename((image_ref or '').replace('\\', '/'))
        if not basename:
            return False

        exact_path = os.path.join(folder, basename)
        if os.path.isfile(exact_path):
            return exact_path

        # Case-insensitive fallback - copy/paste from HTML often has a
        # different case than the actual file on disk.
        try:
            for fname in os.listdir(folder):
                if fname.lower() == basename.lower():
                    return os.path.join(folder, fname)
        except OSError:
            return False
        return False

    def action_import(self):
        self.ensure_one()

        folder = (self.logo_folder_path or '').strip()
        if not folder or not os.path.isdir(folder):
            raise UserError(
                "The logos folder path doesn't exist or isn't a folder on the server:\n%s" % folder
            )

        try:
            html_bytes = base64.b64decode(self.html_file)
            doc = lxml_html.fromstring(html_bytes)
        except Exception as e:
            raise UserError("Could not parse the HTML file: %s" % e)

        cards = doc.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " company-card ")]')
        if not cards:
            raise UserError(
                'No elements with class "company-card" were found in this HTML file. '
                'Double check you uploaded the right file.'
            )

        Client = self.env['dekad.client'].sudo()
        created_names = []
        skipped = []
        sequence = 10

        for card in cards:
            title = (card.get('data-title') or '').strip()
            image_ref = (card.get('data-image') or '').strip()
            text = (card.get('data-text') or '').strip()

            if not title:
                skipped.append("(no data-title found) - skipped")
                continue

            logo_path = self._find_logo_file(folder, image_ref) if image_ref else False
            if not logo_path:
                skipped.append(f"{title}: logo file '{image_ref}' not found in the folder - skipped")
                continue

            try:
                with open(logo_path, 'rb') as f:
                    logo_data = base64.b64encode(f.read())
            except OSError as e:
                skipped.append(f"{title}: could not read logo file ({e}) - skipped")
                continue

            Client.create({
                'name': title,
                'short_description': text or False,
                'logo': logo_data,
                'is_published': False,
                'sequence': sequence,
            })
            created_names.append(title)
            sequence += 10

        summary_lines = [f"Created {len(created_names)} client(s):"]
        summary_lines += [f"  - {n}" for n in created_names]
        if skipped:
            summary_lines.append("")
            summary_lines.append(f"Skipped {len(skipped)}:")
            summary_lines += [f"  - {s}" for s in skipped]

        self.result_summary = '\n'.join(summary_lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dekad.client.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': dict(self.env.context, dekad_import_done=True),
        }