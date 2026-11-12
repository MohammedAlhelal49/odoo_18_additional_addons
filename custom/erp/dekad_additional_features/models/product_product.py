from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    MAIN_COMPANY_ID = 1

    x_name_ar = fields.Char(
        string="Arabic Name",
        compute="_compute_x_name_ar",
        store=False,
    )

    x_name_en = fields.Char(
        string="English Name",
        compute="_compute_x_name_en",
        store=False,
    )

    x_product_search = fields.Char(
        string="Product Search",
        search="_search_x_product_search",
        store=False,
    )

    @api.depends("name")
    def _compute_x_name_ar(self):
        for rec in self:
            rec.x_name_ar = (
                rec.with_context(lang="ar_001").display_name or ""
            )

    @api.depends("name")
    def _compute_x_name_en(self):
        for rec in self:
            rec.x_name_en = (
                rec.with_context(lang="en_US").display_name or ""
            )

    @api.model
    def _search_x_product_search(self, operator, value):
        if not value:
            return []

        search_value = str(value)

        self.env.cr.execute(
            """
            SELECT pp.id
              FROM product_product AS pp
              JOIN product_template AS pt
                ON pt.id = pp.product_tmpl_id
             WHERE COALESCE(pt.name->>'en_US', '') ILIKE %s
                OR COALESCE(pt.name->>'ar_001', '') ILIKE %s
            """,
            (
                f"%{search_value}%",
                f"%{search_value}%",
            ),
        )

        language_product_ids = [
            row[0] for row in self.env.cr.fetchall()
        ]

        return expression.OR([
            [("id", "in", language_product_ids)],
            [("default_code", "ilike", search_value)],
            [("barcode", "ilike", search_value)],
        ])



    def write(self, vals):
        """
        Block ONLY Odoo's internal archive call (active=False) triggered
        automatically after attribute changes.
        Manual archiving by the user is allowed.

        We detect internal calls by checking the context flag
        'from_attribute_change' that we set in product_template.py.
        """
        if vals.get('active') is False and self.env.context.get('from_attribute_change'):
            all_ids = self.ids

            # Check stock moves — all companies
            stock_groups = self.env['stock.move.line'].sudo().read_group(
                domain=[
                    ('product_id', 'in', all_ids),
                    ('move_id.state', '=', 'done'),
                ],
                fields=['product_id'],
                groupby=['product_id'],
                lazy=False,
            )
            stock_ids = [g['product_id'][0] for g in stock_groups]

            # Check accounting moves — all companies
            accounting_groups = self.env['account.move.line'].sudo().read_group(
                domain=[
                    ('product_id', 'in', all_ids),
                    ('move_id.state', '=', 'posted'),
                ],
                fields=['product_id'],
                groupby=['product_id'],
                lazy=False,
            )
            accounting_ids = [g['product_id'][0] for g in accounting_groups]

            locked_ids = set(stock_ids) | set(accounting_ids)
            affected = self.filtered(lambda p: p.id in locked_ids)

            if affected:
                has_stock = bool(set(affected.ids) & set(stock_ids))
                has_accounting = bool(set(affected.ids) & set(accounting_ids))

                if has_stock and has_accounting:
                    reason = _("completed stock moves and posted accounting moves")
                elif has_stock:
                    reason = _("completed stock moves")
                else:
                    reason = _("posted accounting moves")

                raise UserError(_(
                    "⛔ Cannot archive the following Variants.\n\n"
                    "They have %s:\n"
                    "• %s\n\n"
                    "Archiving these Variants would break inventory "
                    "and accounting traceability."
                ) % (
                    reason,
                    '\n• '.join(affected.mapped('display_name')),
                ))

        return super().write(vals)



    related_pricelist_price = fields.Float()

    vendor_code = fields.Char(
        string="Vendor Code",
        help="Vendor-specific code for this product variant"
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'is_storable' in fields_list:
            res['is_storable'] = True
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        if not name:
            return super().name_search(
                name=name,
                args=args,
                operator=operator,
                limit=limit,
            )

        words = name.split()
        domain = []

        for word in words:
            # x_product_search already searches:
            # - English product name
            # - Arabic product name
            # - default_code
            # - barcode
            word_domain = expression.OR([
                [('x_product_search', operator, word)],

                # Extra variant fields
                [('vendor_code', operator, word)],

                # Attribute value: Red, XL, أحمر...
                [('product_template_attribute_value_ids.name', operator, word)],

                # Attribute name: Color, Size, اللون...
                [('product_template_attribute_value_ids.attribute_id.name', operator, word)],
            ])

            # Every entered word must match something
            domain = expression.AND([domain, word_domain])

        args = expression.AND([args, domain])

        return super().name_search(
            name='',
            args=args,
            operator=operator,
            limit=limit,
        )


    def generate_variations_pricelist_rules(self):

        Pricelist = self.env['product.pricelist']
        PricelistItem = self.env['product.pricelist.item']

        # Fetch the default pricelist (you can adjust this condition)
        default_pricelist = self.env['product.pricelist'].search([('name', '=', 'Default')], limit=1)

        if not default_pricelist:
            default_pricelist = Pricelist.create({
                'name': 'Default',
                'currency_id': self.env.user.company_id.currency_id.id,
                'company_id': self.env.user.company_id.id,
            })

        for template in self:
            product_variation_ids = template.product_variant_ids.ids

            # Delete pricelist items for variants that no longer exist in the template
            PricelistItem.search([
                ('pricelist_id', '=', default_pricelist.id),
                ('product_id.product_tmpl_id', '=', template.id),
                ('product_id', 'not in', product_variation_ids)
            ]).unlink()

            # Create rules for missing variants
            existing_items = PricelistItem.search([
                ('pricelist_id', '=', default_pricelist.id),
                ('product_id.product_tmpl_id', '=', template.id),
            ])

            for variant in template.product_variant_ids:
                if not existing_items.filtered(
                        lambda item: item.product_id.id == variant.id):
                    PricelistItem.create({
                        'pricelist_id': default_pricelist.id,
                        'product_id': variant.id,
                        'applied_on': '0_product_variant',
                        'compute_price': 'fixed',
                        'fixed_price': variant.lst_price,
                    })

            for variant in template.product_variant_ids:
                UpdatePricelistItem = PricelistItem.search([
                    ('pricelist_id', '=', default_pricelist.id),
                    ('product_id', '=', variant.id),
                    ('applied_on', '=', '0_product_variant'),
                    ('compute_price', '=', 'fixed'),

                ])
                for record in UpdatePricelistItem:
                    if record.fixed_price == 0:
                        record.fixed_price = variant.related_pricelist_price


    # -------------------------------------------------------------------------
    # Copy cost from the main company to all other companies
    # -------------------------------------------------------------------------
    # IMPORTANT (TEMPORARY): this method is specific to Warood Al Rabea
    # (ورود الربيع). It is currently run manually from the Odoo shell for
    # that company only; no button or view calls it. Warood has no
    # implementation module yet, so it lives here for now. It will be
    # REMOVED from this generic module later (moved to Warood's own
    # implementation module once that exists). Do not use it for other clients.
    # Same applies to MAIN_COMPANY_ID above, which is only used here.
    # -------------------------------------------------------------------------
    def action_copy_cost_from_main_company(self):
        """
        For every shared product variant:
        - Reference cost = main company cost if > 0,
          otherwise the highest cost found in the other companies.
        - The reference cost is written ONLY in companies whose cost is 0
          (main company included). Companies that already have a cost > 0
          are never touched.
        """
        main_company = self.env['res.company'].sudo().browse(self.MAIN_COMPANY_ID)
        other_companies = self.env['res.company'].sudo().search([
            ('id', '!=', main_company.id),
        ])
        all_companies = main_company | other_companies

        # Shared products only (or products owned by the main company)
        products = self.sudo().with_context(active_test=False).search([
            ('company_id', 'in', [False, main_company.id]),
        ])

        for product in products:
            costs = {
                company: product.with_company(company).standard_price
                for company in all_companies
            }

            # 1) Determine the reference cost
            main_cost = costs[main_company]
            if main_company.currency_id.compare_amounts(main_cost, 0.0) > 0:
                reference_cost = main_cost
            else:
                reference_cost = max(
                    (costs[c] for c in other_companies),
                    default=0.0,
                )

            # No cost anywhere -> nothing to do
            if main_company.currency_id.compare_amounts(reference_cost, 0.0) <= 0:
                continue

            # 2) Fill only companies whose cost is 0
            for company, cost in costs.items():
                if company.currency_id.compare_amounts(cost, 0.0) <= 0:
                    product.with_company(company).with_context(
                        skip_global_cost_sync=True,
                    ).standard_price = reference_cost
