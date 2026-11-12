import re

from odoo import api, fields, models

ARABIC = re.compile(r'[؀-ۿ]')


def _split_name(name):
    """ "English / عربي" -> ("English", "عربي"); a name like "1/2 kg" stays as it is. """
    name = (name or '').strip()
    parts = [part.strip() for part in name.split('/') if part.strip()]
    ar = [part for part in parts if ARABIC.search(part)]
    en = [part for part in parts if not ARABIC.search(part)]
    if ar and en:
        return ' / '.join(en), ' / '.join(ar)
    return ('', name) if ARABIC.search(name) else (name, '')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _label_names(self):
        """ English and Arabic name for the 38 x 25 label.
        Takes them from "English / عربي" in the name, otherwise from the Arabic translation. """
        self.ensure_one()
        en_name = self.with_context(lang='en_US').name
        en, ar = _split_name(en_name)
        if not ar:
            ar_langs = [code for code, _name in self.env['res.lang'].get_installed() if code.startswith('ar')]
            for lang in ar_langs:
                translated = self.with_context(lang=lang).name
                if translated and translated != en_name and ARABIC.search(translated):
                    ar = _split_name(translated)[1]
                    break
        return {'en': en, 'ar': ar}


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # English + Arabic name for the POS receipt, whatever the cashier's language
    osh_name_en = fields.Char(compute='_compute_osh_names')
    osh_name_ar = fields.Char(compute='_compute_osh_names')

    def _compute_osh_names(self):
        for product in self:
            names = product._label_names()
            product.osh_name_en = names['en']
            product.osh_name_ar = names['ar']

    def _label_names(self):
        self.ensure_one()
        return self.product_tmpl_id._label_names()

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + ['osh_name_en', 'osh_name_ar']
