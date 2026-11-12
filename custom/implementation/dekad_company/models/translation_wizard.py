import base64
from odoo import models, fields, api


class ModuleTranslationWizard(models.TransientModel):
    _name = 'module.translation.wizard'
    _description = 'Interactive Module Translator'

    module_id = fields.Many2one(
        'ir.module.module',
        string='Module',
        required=True,
        domain=[('state', '=', 'installed')]
    )
    lang_id = fields.Many2one(
        'res.lang',
        string='Language',
        required=True,
        # Defaulting to Arabic
        default=lambda self: self.env['res.lang'].search([('code', 'like', 'ar%')], limit=1)
    )
    untranslated_only = fields.Boolean(string='Show Untranslated Only', default=True)
    line_ids = fields.One2many('module.translation.wizard.line', 'wizard_id', string='Terms')

    def action_load_terms(self):
        self.ensure_one()

        export_wiz = self.env['base.language.export'].create({
            'lang': self.lang_id.code,
            'format': 'po',
            'modules': [(6, 0, [self.module_id.id])],
        })
        export_wiz.act_getfile()

        if not export_wiz.data:
            return

        po_content = base64.b64decode(export_wiz.data).decode('utf-8')

        lines = []
        entries = po_content.split('\n\n')

        for entry in entries:
            msgid, msgstr = "", ""
            for line in entry.splitlines():
                if line.startswith('msgid '):
                    msgid = line[7:].strip('"')
                elif line.startswith('msgstr '):
                    msgstr = line[8:].strip('"')

            # Skip empty source strings (often PO headers)
            if not msgid:
                continue

            # Filter logic
            if self.untranslated_only and msgstr:
                continue

            lines.append((0, 0, {
                'source_string': msgid,
                'translation': msgstr,
            }))

        # Clear existing lines and write new ones
        self.write({'line_ids': [(5, 0, 0)] + lines})

        # Re-open the wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'module.translation.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_translations(self):
        self.ensure_one()

        po_lines = [
            'msgid ""',
            'msgstr ""',
            f'"Language: {self.lang_id.code}\\n"',
            '"MIME-Version: 1.0\\n"',
            '"Content-Type: text/plain; charset=UTF-8\\n"',
            ""
        ]

        for line in self.line_ids:
            if line.translation:
                po_lines.append(f'msgid "{line.source_string}"')
                po_lines.append(f'msgstr "{line.translation}"')
                po_lines.append("")

        po_data = base64.b64encode('\n'.join(po_lines).encode('utf-8'))

        import_wiz = self.env['base.language.import'].create({
            'name': f'ar_update_{self.module_id.name}.po',
            'data': po_data,
            'lang': self.lang_id.code,
            'overwrite': True,
        })
        import_wiz.import_lang()

        return {'type': 'ir.actions.client', 'tag': 'reload'}


class ModuleTranslationWizardLine(models.TransientModel):
    _name = 'module.translation.wizard.line'
    _description = 'Translation Term Line'

    wizard_id = fields.Many2one('module.translation.wizard', ondelete='cascade')
    source_string = fields.Text(string='Source Text (English)', readonly=True)
    translation = fields.Text(string='Target Translation')
