# -*- coding: utf-8 -*-
import re
import unicodedata

from odoo import api, fields, models


def _slugify(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r"[^\w\s-]", '', text).strip().lower()
    return re.sub(r"[-\s]+", '-', text) or 'client'


class DekadClient(models.Model):
    _name = 'dekad.client'
    _description = 'Dekad Website Client'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(string='Client Name', required=True)
    slug = fields.Char(string='URL Slug', copy=False, index=True,
                        help="Used in the client's page URL (/clients/<slug>). "
                             "Auto-generated from the name if left empty.")
    logo = fields.Image(string='Logo', required=True, max_width=512, max_height=512)
    industry = fields.Char(string='Industry / Sector')
    short_description = fields.Text(string='Short Description',
                                     help='Optional. Shown on the client card on the clients list page (/clients) and the client detail page - not on the homepage.')
    full_description = fields.Text(string='Full Description',
                                    help='Shown on the client detail page.')
    sequence = fields.Integer(string='Sequence', default=10)
    is_published = fields.Boolean(string='Published', default=True,
                                   help='Only published clients are shown on the website.')

    _sql_constraints = [
        ('slug_unique', 'unique(slug)', 'A client with this URL slug already exists.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('slug'):
                vals['slug'] = self._generate_unique_slug(vals.get('name') or '')
        return super().create(vals_list)

    def _generate_unique_slug(self, name):
        base = _slugify(name)
        slug = base
        counter = 2
        while self.env['dekad.client'].sudo().search_count([('slug', '=', slug)]):
            slug = f"{base}-{counter}"
            counter += 1
        return slug