import threading
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round

STOCK_ACCOUNT_KEYS = ('stock_input', 'stock_output', 'stock_valuation')


class StockAccountingCorrectionWizard(models.TransientModel):
    """تصحيح فواتير موردين لمنتجات مخزّنة انسجّلت على حساب مصروف بدل Stock Input
    (قبل ما ينضبط الجرد الآلي). الأداة ما بتعدّل الفواتير: بتعمل قيود تسوية بعد المعاينة."""
    _name = 'stock.accounting.correction.wizard'
    _description = 'Stock Accounting Correction'

    mode = fields.Selection(
        [('correct', 'Correct vendor bills and stock accounts'),
         ('redate', 'Redistribute existing sold-part / Stock Output entries by month')],
        string='Mode', default='correct', required=True)
    redate_batch = fields.Selection(selection='_selection_batches', string='Batch to Redistribute')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    date_from = fields.Date(string='Bills From', help='Limits the vendor bills to correct (step 1). Balances are always read in full.')
    date_to = fields.Date(string='Bills To', help='Limits the vendor bills to correct (step 1). Balances are always read in full.')
    journal_id = fields.Many2one(
        'account.journal', string='Correction Journal', required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        default=lambda self: self._default_journal())
    reclass_date_mode = fields.Selection(
        [('bill', 'Bill date'), ('fixed', 'Correction date')], string='Reclassification Date',
        default='bill', required=True,
        help='Bill date: each reclassification entry is dated like its bill, so every month is corrected.')
    correction_date = fields.Date(
        string='Correction Date', required=True, default=fields.Date.context_today,
        help='Date of the revaluation and sold-part entries (and of the reclassifications in "Correction date" mode).')
    state = fields.Selection(
        [('draft', 'Draft'), ('preview', 'Preview'), ('done', 'Done')], default='draft', required=True)
    batch = fields.Char(string='Batch', readonly=True)

    line_ids = fields.One2many('stock.accounting.correction.line', 'wizard_id', string='Lines')
    reclass_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'reclass')])
    revalue_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'revalue')])
    sold_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'sold')])
    output_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'output')])
    layer_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'layer')])
    match_line_ids = fields.One2many(
        'stock.accounting.correction.line', 'wizard_id', domain=[('correction_type', '=', 'match')])
    summary_html = fields.Html(string='Summary', compute='_compute_summary_html', sanitize=False)

    # ------------------------------------------------------------------ helpers
    @api.model
    def _selection_batches(self):
        groups = self.env['account.move']._read_group(
            [('stock_correction_batch', '!=', False), ('stock_correction_type', 'in', ('sold', 'output')),
             ('stock_correction_redated', '=', False), ('stock_correction_monthly', '=', False),
             ('state', '=', 'posted')],
            groupby=['stock_correction_batch'])
        return [(batch, batch) for (batch,) in groups]

    def _month_date(self, day):
        """آخر يوم بشهر هالتاريخ، وما بيتعدّى تاريخ التصحيح."""
        return min(day + relativedelta(day=31), self.correction_date)

    def _allocate(self, amount, weights):
        """توزيع المبلغ على الأشهر حسب الأوزان الموجبة. بيرجع [(تاريخ، مبلغ)]."""
        currency = self.currency_id
        positive = {month: w for month, w in weights.items() if w > 0}
        total = sum(positive.values())
        if total <= 0:
            return [(self.correction_date, amount)]
        result, allocated = defaultdict(float), 0.0
        months = sorted(positive)
        for index, month in enumerate(months):
            part = currency.round(amount - allocated) if index == len(months) - 1 \
                else currency.round(amount * positive[month] / total)
            allocated += part
            result[self._month_date(month)] += part
        return [(date, value) for date, value in sorted(result.items()) if not currency.is_zero(value)]

    def _split_sold(self, product, amount):
        """الجزء المباع: حسب الكمية المسلّمة للزبائن بكل شهر (ناقص المرتجعات)."""
        moves = self.env['stock.move'].search([
            ('company_id', '=', self.company_id.id), ('state', '=', 'done'), ('product_id', '=', product.id),
            '|', '&', ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'customer'),
            '&', ('location_id.usage', '=', 'customer'), ('location_dest_id.usage', '=', 'internal'),
        ])
        weights = defaultdict(float)
        for move in moves:
            sign = 1 if move.location_dest_id.usage == 'customer' else -1
            weights[move.date.date().replace(day=1)] += sign * move.product_qty
        return self._allocate(amount, weights)

    def _split_output(self, product, account, amount):
        """Stock Output: حسب صافي الحساب بكل شهر لهالمنتج (بدون قيود التصحيح)."""
        groups = self.env['account.move.line']._read_group(
            [('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
             ('account_id', '=', account.id), ('product_id', '=', product.id),
             ('move_id.stock_correction_type', '=', False)],
            groupby=['date:month'], aggregates=['balance:sum'])
        weights = {month.date() if hasattr(month, 'date') else month: balance for month, balance in groups}
        return self._allocate(amount, weights)

    @api.model
    def _default_journal(self):
        # دفتر تقييم المخزون (نفس دفتر قيود الجرد الآلي)، وإلا أول دفتر عام
        company = self.env.company
        journal = self.env['product.category'].with_company(company).search([], limit=1).property_stock_journal
        if journal and journal.company_id == company:
            return journal
        return self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)

    def _product_accounts(self, product):
        product = product.with_company(self.company_id)
        return product.product_tmpl_id.with_company(self.company_id)._get_product_accounts()

    def _wrong_bill_lines(self, include_corrected=False):
        """سطور فواتير موردين مرحّلة لمنتجات مخزّنة (جرد آلي) نازلة على حساب غير حسابات المخزون.
        include_corrected: كمان الفواتير اللي انعملها إعادة تصنيف (لإكمال الخطوات 2 و 3 بعد انقطاع)."""
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', '=', 'in_invoice'),
            ('display_type', 'in', ('product', 'cogs')),
            ('product_id.is_storable', '=', True),
        ]
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        lines = self.env['account.move.line'].search(domain, order='date, move_id, id')
        corrected_bills = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('stock_correction_type', '=', 'reclass'),
            ('state', '=', 'posted'),
        ]).stock_correction_source_id

        def is_wrong(line):
            if not include_corrected and line.move_id in corrected_bills:
                return False
            product = line.product_id.with_company(self.company_id)
            if product.categ_id.property_valuation != 'real_time':
                return False
            accounts = self._product_accounts(product)
            if not accounts.get('stock_input'):
                return False
            valuation = accounts.get('stock_valuation')
            if line.display_type == 'cogs':
                # فرق سعر Odoo نازل على حساب المخزون (لما الفاتورة نفسها نزلت على المخزون)
                return bool(valuation) and line.account_id == valuation
            # سطر منتج: لازم ينزل على Stock Input. حساب مصروف أو حساب المخزون نفسه = غلط
            return line.account_id not in (accounts['stock_input'] | accounts.get('stock_output', line.account_id.browse()))

        return lines.filtered(is_wrong)

    def _balance(self, account, product=None):
        domain = [('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
                  ('account_id', '=', account.id)]
        if product:
            domain.append(('product_id', '=', product.id))
        result = self.env['account.move.line']._read_group(domain, aggregates=['balance:sum'])
        return result[0][0] if result else 0.0

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ------------------------------------------------------------------ analyze
    def action_analyze(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("This correction is already done. Start a new one."))
        self.line_ids.unlink()
        if self.mode == 'redate':
            return self._analyze_redate()
        currency = self.currency_id
        rounding = currency.rounding
        wrong = self._wrong_bill_lines()
        Line = self.env['stock.accounting.correction.line']
        vals_list = []

        # 1) إعادة تصنيف: سطر لكل (فاتورة، حساب)
        by_bill = defaultdict(lambda: self.env['account.move.line'])
        for line in wrong:
            by_bill[(line.move_id, line.account_id)] |= line
        for (bill, account), lines in by_bill.items():
            amount = currency.round(sum(lines.mapped('balance')))
            if float_is_zero(amount, precision_rounding=rounding):
                continue
            stock_input = self._product_accounts(lines[0].product_id)['stock_input']
            vals_list.append({
                'wizard_id': self.id,
                'correction_type': 'reclass',
                'move_id': bill.id,
                'partner_id': bill.partner_id.id,
                'date': bill.date if self.reclass_date_mode == 'bill' else self.correction_date,
                'quantity': len(lines),
                'amount': amount,
                'debit_account_id': stock_input.id,
                'credit_account_id': account.id,
                'note': _("%(count)s product line(s) of %(bill)s", count=len(lines), bill=bill.name),
            })

        # 2) و 3) لكل منتج: إعادة تقييم الموجود بالمخزون، والباقي (المباع) للمصروف.
        # منحسب من كل سطور الفواتير المتأثرة (حتى اللي انعملها إعادة تصنيف)، حتى لو العملية انقطعت
        # قبل، بنكمّل الناقص: المنتج اللي انعملّه إعادة تقييم ما بينعاد، والجزء المباع من رصيد Stock Input.
        layer_vals = self._missing_layer_vals()
        si_effect = defaultdict(float)  # أثر الخطوة 5 على Stock Input لكل منتج
        for vals in layer_vals:
            if not vals.get('selected', True):
                continue
            product = self.env['product.product'].browse(vals['product_id'])
            stock_input = self._product_accounts(product)['stock_input']
            if vals['debit_account_id'] == stock_input.id:
                si_effect[product] += vals['amount']
            elif vals['credit_account_id'] == stock_input.id:
                si_effect[product] -= vals['amount']
        vals_list += layer_vals

        affected = self._wrong_bill_lines(include_corrected=True)
        revalued_products = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id), ('stock_correction_type', '=', 'revalue'),
            ('state', '=', 'posted')]).line_ids.product_id
        by_product = defaultdict(lambda: self.env['account.move.line'])
        for line in affected:
            by_product[line.product_id] |= line
        for product, lines in by_product.items():
            pending_reclass = sum((lines & wrong).mapped('balance'))
            product = product.with_company(self.company_id)
            accounts = self._product_accounts(product)
            stock_input = accounts['stock_input']
            plines = lines.filtered(lambda l: l.display_type == 'product')
            non_stock = plines.account_id - accounts['stock_valuation']
            expense_account = max(non_stock, key=lambda a: sum(plines.filtered(
                lambda l: l.account_id == a).mapped('balance'))) if non_stock else accounts['expense']
            billed_amount = sum(plines.mapped('balance'))
            billed_qty = sum(l.product_uom_id._compute_quantity(l.quantity, product.uom_id)
                             if l.product_uom_id else l.quantity for l in plines)
            if float_is_zero(billed_qty, precision_digits=4) or billed_amount <= 0:
                continue
            unit_price = billed_amount / billed_qty
            qty_svl = product.quantity_svl
            value_svl = product.value_svl
            on_hand = min(max(qty_svl, 0.0), billed_qty)
            cost_method = product.categ_id.property_cost_method

            revalue = 0.0
            if on_hand > 0 and product not in revalued_products:
                average = value_svl / qty_svl if qty_svl else 0.0
                revalue = currency.round(on_hand * (unit_price - average))
                if cost_method == 'standard':
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'revalue', 'selected': False,
                        'product_id': product.id, 'quantity': on_hand, 'unit_price': unit_price,
                        'amount': revalue, 'date': self.correction_date,
                        'debit_account_id': accounts['stock_valuation'].id, 'credit_account_id': stock_input.id,
                        'note': _("Skipped: standard cost method (Odoo cannot revalue it)."),
                    })
                    revalue = 0.0
                elif not float_is_zero(revalue, precision_rounding=rounding):
                    note = _("%(qty)s in stock: value %(old)s → %(new)s",
                             qty=float_round(on_hand, 2),
                             old=float_round(on_hand * average, 2), new=float_round(on_hand * unit_price, 2))
                    selected = value_svl + revalue >= 0
                    if not selected:
                        note = _("Skipped: the stock value would become negative.")
                        revalue = 0.0
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'revalue', 'selected': selected,
                        'product_id': product.id, 'quantity': on_hand, 'unit_price': unit_price,
                        'amount': revalue if selected else currency.round(on_hand * (unit_price - average)),
                        'date': self.correction_date,
                        'debit_account_id': accounts['stock_valuation'].id, 'credit_account_id': stock_input.id,
                        'note': note,
                    })

            # Stock Input لهالمنتج بعد إعادة التصنيف وإعادة التقييم: الباقي = الكمية المباعة
            residual = currency.round(self._balance(stock_input, product) + pending_reclass - revalue
                                      + si_effect.get(product, 0.0))
            if residual > rounding / 2:
                for date, part in self._split_sold(product, residual):
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'sold',
                        'product_id': product.id, 'quantity': max(billed_qty - on_hand, 0.0),
                        'unit_price': unit_price, 'amount': part, 'date': date,
                        'debit_account_id': expense_account.id, 'credit_account_id': stock_input.id,
                        'note': _("Stock Input left for this product (sold or consumed part), %s.", date.strftime('%m/%Y')),
                    })
            elif residual < -rounding / 2:
                # فرق سعر Odoo على الفاتورة حط تكلفة البضاعة على المصروف وهي لسا بالمخزون (وانعاد تقييمها):
                # منرجّع هالمصروف بحدود فرق السعر. غير هيك: مراجعة يدوية.
                cogs_lines = self.env['account.move.line'].search([
                    ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
                    ('move_id', 'in', lines.move_id.ids), ('product_id', '=', product.id),
                    ('display_type', '=', 'cogs'), ('account_id', 'not in', [stock_input.id, accounts['stock_valuation'].id]),
                ])
                expensed = currency.round(sum(cogs_lines.mapped('balance')))
                amount = min(-residual, expensed) if expensed > 0 else 0.0
                if amount > rounding / 2:
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'sold',
                        'product_id': product.id, 'amount': amount,
                        'date': self._month_date(max(cogs_lines.mapped('date'))),
                        'debit_account_id': stock_input.id, 'credit_account_id': expense_account.id,
                        'note': _("Price difference on the bill expensed goods that are still in stock: expense reversed."),
                    })
                if -residual - amount > rounding / 2:
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'sold', 'selected': False,
                        'product_id': product.id, 'amount': currency.round(-residual - amount), 'date': self.correction_date,
                        'debit_account_id': stock_input.id, 'credit_account_id': expense_account.id,
                        'note': _("Skipped: Stock Input has a credit left for this product (receipt not billed?). Check manually."),
                    })
        # 4) Stock Output: التسليم انقيّد (مدين Stock Output) بس الفاتورة ما فيها تكلفة البضاعة المباعة
        vals_list += self._stock_output_vals()
        # 6) مطابقة دفعات الزبائن المفتوحة مع فواتيرهم المفتوحة (Add outstanding credit)
        vals_list += self._partner_matching_vals()
        Line.create(vals_list)
        self.state = 'preview'
        return self._reopen()

    def _analyze_redate(self):
        """قيود "الجزء المباع" و"Stock Output" من دفعة سابقة: بتنعكس بنفس تاريخها،
        وبتنعمل من جديد موزّعة على أشهر البيع."""
        if not self.redate_batch:
            raise UserError(_("Choose the batch to redistribute."))
        moves = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id), ('stock_correction_batch', '=', self.redate_batch),
            ('stock_correction_type', 'in', ('sold', 'output')), ('stock_correction_redated', '=', False),
            ('stock_correction_monthly', '=', False), ('state', '=', 'posted'),
        ])
        vals_list = []
        for move in moves:
            debit = move.line_ids.filtered(lambda l: l.debit > 0)[:1]
            credit = move.line_ids.filtered(lambda l: l.credit > 0)[:1]
            product = debit.product_id or credit.product_id
            amount = debit.debit
            if not product or not debit or not credit:
                continue
            if move.stock_correction_type == 'sold':
                splits = self._split_sold(product, amount)
            else:
                splits = self._split_output(product, credit.account_id, amount)
            for date, part in splits:
                vals_list.append({
                    'wizard_id': self.id, 'correction_type': move.stock_correction_type,
                    'move_id': move.id, 'product_id': product.id, 'amount': part, 'date': date,
                    'debit_account_id': debit.account_id.id, 'credit_account_id': credit.account_id.id,
                    'note': _("Redistribution of %(move)s (%(date)s) to %(month)s",
                              move=move.name, date=move.date.strftime('%d/%m/%Y'), month=date.strftime('%m/%Y')),
                })
        self.env['stock.accounting.correction.line'].create(vals_list)
        self.state = 'preview'
        return self._reopen()

    def _create_redate(self, selected, batch):
        """عكس القيد الأصلي بنفس تاريخه (صافي صفر)، وقيود جديدة بتاريخ كل شهر."""
        Move = self.env['account.move'].with_company(self.company_id)
        created = self.env['account.move']
        for original in selected.move_id:
            lines = selected.filtered(lambda l: l.move_id == original)
            reversal = original._reverse_moves(
                default_values_list=[{'date': original.date,
                                      'ref': _("Stock correction - redistribution of %s", original.name)}])
            reversal.write({'stock_correction_batch': batch, 'stock_correction_type': original.stock_correction_type,
                            'stock_correction_monthly': True})
            reversal.action_post()
            created |= reversal
            for line in lines:
                move = Move.create({
                    'move_type': 'entry', 'journal_id': self.journal_id.id, 'company_id': self.company_id.id,
                    'date': line.date, 'ref': line.note,
                    'stock_correction_batch': batch, 'stock_correction_type': line.correction_type,
                    'stock_correction_monthly': True,
                    'line_ids': [
                        (0, 0, {'account_id': line.debit_account_id.id, 'debit': line.amount, 'credit': 0.0,
                                'name': line.note, 'product_id': line.product_id.id}),
                        (0, 0, {'account_id': line.credit_account_id.id, 'debit': 0.0, 'credit': line.amount,
                                'name': line.note, 'product_id': line.product_id.id}),
                    ],
                })
                move.action_post()
                created |= move
            original.stock_correction_redated = True
            if len(created) % 50 < 3:
                self._commit_progress()
        self._commit_progress()
        return created

    def _layer_is_outgoing(self, layer):
        move = layer.stock_move_id
        if move:
            return move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'
        # "Correction of MW/OUT/00062 (modification of past move)" بدون حركة مربوطة
        description = layer.description or ''
        if description.startswith('Correction of '):
            name = description[len('Correction of '):].split(' (')[0]
            picking = self.env['stock.picking'].search(
                [('name', '=', name), ('company_id', '=', self.company_id.id)], limit=1)
            return picking.picking_type_code == 'outgoing'
        return False

    def _missing_layer_vals(self):
        """5) حركات تقييم مخزون بقيمة بس بدون قيد محاسبي (صارت والتقييم يدوي، أو تعديل حركة منتهية):
        قيد لكل (منتج، حساب مقابل، شهر). استلام/تغيير طريقة التقييم: مقابل Stock Input،
        تسليم: مقابل المصروف (تكلفة البضاعة المباعة)."""
        currency = self.currency_id
        layers = self.env['stock.valuation.layer'].search([
            ('company_id', '=', self.company_id.id), ('account_move_id', '=', False)], order='create_date, id')
        groups = defaultdict(lambda: self.env['stock.valuation.layer'])
        for layer in layers:
            if currency.is_zero(layer.value):
                continue
            product = layer.product_id.with_company(self.company_id)
            if product.categ_id.property_valuation != 'real_time':
                continue
            accounts = self._product_accounts(product)
            counterpart = accounts['expense'] if self._layer_is_outgoing(layer) else accounts['stock_input']
            month = layer.create_date.date().replace(day=1)
            groups[(product, accounts['stock_valuation'], counterpart, month)] |= layer
        vals_list = []
        for (product, valuation, counterpart, month), group in groups.items():
            value = currency.round(sum(group.mapped('value')))
            if currency.is_zero(value):
                # حركات بتلغي بعضها (مثلاً تسليم بالغلط وتصحيحه): بس منربطها بقيد صفر؟ لا، منعلّمها بدون قيد
                vals_list.append({
                    'wizard_id': self.id, 'correction_type': 'layer', 'selected': False,
                    'product_id': product.id, 'amount': 0.0, 'date': self._month_date(month),
                    'debit_account_id': valuation.id, 'credit_account_id': counterpart.id,
                    'layer_ids': [(6, 0, group.ids)],
                    'note': _("%(count)s movement(s) cancelling each other (net 0): nothing to post.",
                              count=len(group)),
                })
                continue
            debit, credit = (valuation, counterpart) if value > 0 else (counterpart, valuation)
            kinds = sorted({(l.description or '').split(' (')[0][:40] for l in group})
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'layer',
                'product_id': product.id, 'quantity': sum(group.mapped('quantity')),
                'amount': abs(value), 'date': self._month_date(month),
                'debit_account_id': debit.id, 'credit_account_id': credit.id,
                'layer_ids': [(6, 0, group.ids)],
                'note': _("%(count)s valuation movement(s) without entry: %(kinds)s",
                          count=len(group), kinds=', '.join(kinds)),
            })
        return vals_list

    def _open_receivable_lines(self):
        return self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('account_id.account_type', '=', 'asset_receivable'), ('account_id.reconcile', '=', True),
            ('partner_id', '!=', False), ('reconciled', '=', False), ('amount_residual', '!=', 0),
        ], order='date, id')

    def _partner_matching_vals(self):
        """6) زبون عنده فاتورة مفتوحة ودفعة مفتوحة (ما انربطت بالفاتورة، مثلاً بعد إلغاء الفاتورة
        وإعادة إصدارها): منربطهن متل "Add outstanding credit". ما في قيود جديدة."""
        currency = self.currency_id
        groups = defaultdict(lambda: self.env['account.move.line'])
        for line in self._open_receivable_lines():
            groups[(line.partner_id.commercial_partner_id, line.account_id)] |= line
        vals_list = []
        for (partner, account), lines in groups.items():
            debits = lines.filtered(lambda l: l.amount_residual > 0)
            credits = lines.filtered(lambda l: l.amount_residual < 0)
            if not debits or not credits:
                continue
            amount = currency.round(min(sum(debits.mapped('amount_residual')), -sum(credits.mapped('amount_residual'))))
            left = currency.round(sum(lines.mapped('amount_residual')))
            note = _("Invoices %(inv)s with payments %(pay)s", inv=', '.join(debits.move_id.mapped('name')),
                     pay=', '.join(credits.move_id.mapped('name')))
            if left < 0:
                note += _(" — %s of payment left on the customer (check for a duplicate payment).", -left)
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'match', 'partner_id': partner.id,
                'amount': amount, 'date': fields.Date.context_today(self),
                'debit_account_id': account.id, 'credit_account_id': account.id,
                'match_line_ids': [(6, 0, lines.ids)],
                'note': note,
            })
        return vals_list

    def _stock_output_vals(self):
        """لكل منتج: الرصيد الباقي على حساب Stock Output (حساب عبور لازم يكون صفر).
        مدين = تسليم انقيّد وفاتورته ما فيها COGS: مدين المصروف / دائن Stock Output."""
        currency = self.currency_id
        rounding = currency.rounding
        categories = self.env['product.category'].with_company(self.company_id).search([])
        output_accounts = categories.property_stock_account_output_categ_id
        if not output_accounts:
            return []
        # الرصيد كامل (بدون فلتر التاريخ): فترة "Bills From/To" بتحدد الفواتير بس، وإلا قيود تصحيح
        # سابقة بعد هالتاريخ ما بتنحسب والقيد بيتكرّر
        domain = [('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
                  ('account_id', 'in', output_accounts.ids)]
        groups = self.env['account.move.line']._read_group(
            domain, groupby=['account_id', 'product_id'], aggregates=['balance:sum'])
        vals_list = []
        for account, product, balance in groups:
            balance = currency.round(balance)
            if float_is_zero(balance, precision_rounding=rounding):
                continue
            if not product:
                vals_list.append({
                    'wizard_id': self.id, 'correction_type': 'output', 'selected': False,
                    'amount': abs(balance), 'date': self.correction_date,
                    'debit_account_id': account.id, 'credit_account_id': account.id,
                    'note': _("Skipped: balance without product. Check manually."),
                })
                continue
            expense = self._product_accounts(product)['expense']
            if balance > 0:
                for date, part in self._split_output(product, account, balance):
                    vals_list.append({
                        'wizard_id': self.id, 'correction_type': 'output', 'product_id': product.id,
                        'amount': part, 'date': date,
                        'debit_account_id': expense.id, 'credit_account_id': account.id,
                        'note': _("Delivered and invoiced without cost of goods sold, %s.", date.strftime('%m/%Y')),
                    })
            else:
                vals_list.append({
                    'wizard_id': self.id, 'correction_type': 'output', 'selected': False,
                    'product_id': product.id, 'amount': -balance, 'date': self.correction_date,
                    'debit_account_id': account.id, 'credit_account_id': expense.id,
                    'note': _("Skipped: Stock Output has a credit for this product. Check manually."),
                })
        return vals_list

    # ------------------------------------------------------------------ summary
    @api.depends('line_ids.selected', 'line_ids.amount', 'state')
    def _compute_summary_html(self):
        for wizard in self:
            if wizard.state == 'draft' or not wizard.company_id:
                wizard.summary_html = False
                continue
            selected = wizard.line_ids.filtered('selected')
            if not wizard.line_ids:
                wizard.summary_html = Markup('<p>%s</p>') % _("Nothing to correct: no vendor bill line of a stored product is posted outside the stock accounts.")
                continue
            effect = defaultdict(float)
            for line in selected:
                effect[line.debit_account_id] += line.amount
                effect[line.credit_account_id] -= line.amount
            fmt = lambda v: wizard.currency_id.format(v)
            rows = Markup('')
            for account in sorted(effect, key=lambda a: a.code or ''):
                before = wizard._balance(account) if wizard.state == 'preview' else None
                if before is None:
                    rows += Markup('<tr><td>%s</td><td class="text-end">%s</td></tr>') % (
                        account.display_name, fmt(effect[account]))
                else:
                    rows += Markup('<tr><td>%s</td><td class="text-end">%s</td><td class="text-end">%s</td>'
                                   '<td class="text-end fw-bold">%s</td></tr>') % (
                        account.display_name, fmt(before), fmt(effect[account]), fmt(before + effect[account]))
            counts = Markup('')
            for ctype, label in [('reclass', _("Reclassification entries (one per bill)")),
                                 ('revalue', _("Stock revaluations (one per product)")),
                                 ('sold', _("Sold-part entries (one per product)")),
                                 ('output', _("Stock Output entries (one per product)")),
                                 ('layer', _("Missing valuation entries (per product and month)")),
                                 ('match', _("Customer payments matched with invoices (no entry)"))]:
                lines = selected.filtered(lambda l: l.correction_type == ctype)
                counts += Markup('<tr><td>%s</td><td class="text-end">%s</td><td class="text-end">%s</td></tr>') % (
                    label, len(lines), fmt(sum(lines.mapped('amount'))))
            if wizard.state == 'preview':
                head = Markup('<tr><th>%s</th><th class="text-end">%s</th><th class="text-end">%s</th><th class="text-end">%s</th></tr>') % (
                    _("Account"), _("Balance now"), _("Correction"), _("Balance after"))
            else:
                head = Markup('<tr><th>%s</th><th class="text-end">%s</th></tr>') % (_("Account"), _("Correction"))
            wizard.summary_html = Markup(
                '<table class="table table-sm o_main_table"><thead><tr><th>%s</th><th class="text-end">%s</th>'
                '<th class="text-end">%s</th></tr></thead><tbody>%s</tbody></table>'
                '<table class="table table-sm o_main_table"><thead>%s</thead><tbody>%s</tbody></table>') % (
                _("Entries to create"), _("Count"), _("Amount"), counts, head, rows)

    # ------------------------------------------------------------------ create
    def action_create_entries(self):
        self.ensure_one()
        if self.state != 'preview':
            raise UserError(_("Analyze first."))
        selected = self.line_ids.filtered('selected')
        if not selected:
            raise UserError(_("Select at least one line."))
        lock_date = self.company_id._get_user_fiscal_lock_date(self.journal_id)
        if any(line.date <= lock_date for line in selected):
            raise UserError(_("Some correction dates are on or before the lock date (%s).", lock_date))

        company = self.company_id
        batch = 'STKCORR/%s/%s' % (company.id, fields.Datetime.now().strftime('%Y%m%d-%H%M%S'))
        if self.mode == 'redate':
            self._create_redate(selected, batch)
            self.write({'state': 'done', 'batch': batch})
            return self.action_open_entries()
        Move = self.env['account.move'].with_company(company)
        chunk = 50

        def simple_move_vals(line, ref, ctype):
            name = line.note or ref
            product = line.product_id
            return {
                'move_type': 'entry',
                'journal_id': self.journal_id.id,
                'company_id': company.id,
                'date': line.date,
                'ref': ref,
                'stock_correction_batch': batch,
                'stock_correction_type': ctype,
                'stock_correction_monthly': ctype in ('sold', 'output'),
                'line_ids': [
                    (0, 0, {'account_id': line.debit_account_id.id, 'debit': line.amount, 'credit': 0.0,
                            'name': name, 'product_id': product.id}),
                    (0, 0, {'account_id': line.credit_account_id.id, 'debit': 0.0, 'credit': line.amount,
                            'name': name, 'product_id': product.id}),
                ],
            }

        # 1) إعادة التصنيف: قيد لكل فاتورة، بسطر لكل منتج (حتى Stock Input يبين على مستوى المنتج)
        wrong_lines = self._wrong_bill_lines()
        reclass = selected.filtered(lambda l: l.correction_type == 'reclass')
        for index in range(0, len(reclass), chunk):
            vals_list, bills = [], []
            for line in reclass[index:index + chunk]:
                bill = line.move_id
                bill_lines = wrong_lines.filtered(
                    lambda l: l.move_id == bill and l.account_id == line.credit_account_id)
                move_lines = []
                for bl in bill_lines:
                    move_lines += [
                        (0, 0, {'account_id': line.debit_account_id.id, 'debit': max(bl.balance, 0.0),
                                'credit': max(-bl.balance, 0.0), 'name': bl.name,
                                'product_id': bl.product_id.id, 'partner_id': bill.partner_id.id}),
                        (0, 0, {'account_id': line.credit_account_id.id, 'debit': max(-bl.balance, 0.0),
                                'credit': max(bl.balance, 0.0), 'name': bl.name,
                                'product_id': bl.product_id.id, 'partner_id': bill.partner_id.id}),
                    ]
                if not move_lines:
                    continue
                vals_list.append({
                    'move_type': 'entry',
                    'journal_id': self.journal_id.id,
                    'company_id': company.id,
                    'date': line.date,
                    'ref': _("Stock correction - reclassification of %s", bill.name),
                    'stock_correction_batch': batch,
                    'stock_correction_type': 'reclass',
                    'stock_correction_source_id': bill.id,
                    'line_ids': move_lines,
                })
                bills.append((bill, line))
            moves = Move.create(vals_list)
            moves.action_post()
            for move, (bill, line) in zip(moves, bills):
                bill.message_post(body=_("Stock accounting correction: product lines moved from %(old)s to %(new)s by %(move)s.",
                                         old=line.credit_account_id.display_name, new=line.debit_account_id.display_name,
                                         move=move._get_html_link()))
            self._commit_progress()

        # 2) إعادة تقييم المخزون الموجود (أداة Odoo: طبقة تقييم + قيد، وتكلفة المنتج بتتحدّث)
        SVL = self.env['stock.valuation.layer']
        revalue = selected.filtered(lambda l: l.correction_type == 'revalue')
        for index, line in enumerate(revalue, 1):
            last_id = SVL.search([], order='id desc', limit=1).id or 0
            self.env['stock.valuation.layer.revaluation'].with_company(company).create({
                'company_id': company.id,
                'product_id': line.product_id.id,
                'added_value': line.amount,
                'account_id': line.credit_account_id.id,
                'account_journal_id': self.journal_id.id,
                'date': line.date,
                'reason': _("Stock accounting correction (%s)", batch),
            }).action_validate_revaluation()
            SVL.search([('id', '>', last_id), ('product_id', '=', line.product_id.id)]).account_move_id.write(
                {'stock_correction_batch': batch, 'stock_correction_type': 'revalue'})
            if index % chunk == 0:
                self._commit_progress()
        self._commit_progress()

        # 5) قيود التقييم الناقصة: قيد لكل مجموعة، ومنربط الحركات فيه حتى ما تنعاد
        layer_lines = selected.filtered(lambda l: l.correction_type == 'layer' and l.amount)
        for index in range(0, len(layer_lines), chunk):
            lines = layer_lines[index:index + chunk]
            moves = Move.create([simple_move_vals(
                line, _("Stock correction - missing valuation entry of %s", line.product_id.display_name), 'layer')
                for line in lines])
            moves.action_post()
            for line, move in zip(lines, moves):
                line.layer_ids.write({'account_move_id': move.id})
            self._commit_progress()

        # 6) مطابقة دفعات الزبائن مع فواتيرهم
        for line in selected.filtered(lambda l: l.correction_type == 'match'):
            lines = line.match_line_ids.filtered(lambda l: not l.reconciled)
            if lines.filtered(lambda l: l.amount_residual > 0) and lines.filtered(lambda l: l.amount_residual < 0):
                lines.reconcile()
                for invoice in lines.move_id.filtered(lambda m: m.is_invoice()):
                    invoice.message_post(body=_("Stock accounting correction (%s): matched with the customer's open payment.", batch))
        self._commit_progress()

        # 3) الجزء المباع (باقي Stock Input للمصروف) و 4) Stock Output (تكلفة البضاعة المباعة الناقصة)
        labels = {'sold': _("Stock correction - sold part of %s"),
                  'output': _("Stock correction - cost of goods sold of %s")}
        simple = selected.filtered(lambda l: l.correction_type in ('sold', 'output'))
        for index in range(0, len(simple), chunk):
            lines = simple[index:index + chunk]
            Move.create([simple_move_vals(line, labels[line.correction_type] % line.product_id.display_name,
                                          line.correction_type) for line in lines]).action_post()
            self._commit_progress()

        self.write({'state': 'done', 'batch': batch})
        return {
            'type': 'ir.actions.act_window',
            'name': _("Stock Correction %s", batch),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('stock_correction_batch', '=', batch)],
            'context': {'create': False},
        }

    def _commit_progress(self):
        """حفظ التقدّم بعد كل دفعة: إذا انقطعت العملية (حد وقت السيرفر)، Analyze ثم Create
        بيكمّلوا من مطرح ما وقفت بدون تكرار (التحليل بيحسب من الأرصدة الحالية)."""
        if self.env.context.get('stock_correction_no_commit') or getattr(threading.current_thread(), 'testing', False):
            return
        self.env.cr.commit()

    def action_open_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Stock Correction %s", self.batch),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('stock_correction_batch', '=', self.batch)],
            'context': {'create': False},
        }


class StockAccountingCorrectionLine(models.TransientModel):
    _name = 'stock.accounting.correction.line'
    _description = 'Stock Accounting Correction Line'
    _order = 'correction_type, date, id'

    wizard_id = fields.Many2one('stock.accounting.correction.wizard', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    correction_type = fields.Selection(
        [('reclass', 'Reclassification'), ('revalue', 'Revaluation'), ('sold', 'Sold Part'),
         ('output', 'Stock Output'), ('layer', 'Missing Valuation Entry'),
         ('match', 'Customer Payment Matching')], required=True)
    layer_ids = fields.Many2many('stock.valuation.layer', string='Valuation Movements', readonly=True)
    match_line_ids = fields.Many2many('account.move.line', string='Lines to Match', readonly=True)
    selected = fields.Boolean(string='Apply', default=True)
    move_id = fields.Many2one('account.move', string='Bill', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    date = fields.Date(readonly=True)
    quantity = fields.Float(readonly=True, digits='Product Unit of Measure')
    unit_price = fields.Monetary(string='Billed Unit Price', readonly=True)
    amount = fields.Monetary(readonly=True)
    debit_account_id = fields.Many2one('account.account', string='Debit', readonly=True)
    credit_account_id = fields.Many2one('account.account', string='Credit', readonly=True)
    note = fields.Char(readonly=True)
