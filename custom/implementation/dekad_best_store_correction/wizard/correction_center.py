import re
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# أنواع الحسابات الصحيحة (قالب الحسابات الإماراتي بيعرّف الأصول الثابتة ومجمع إهلاكها أصول متداولة)
ACCOUNT_TYPE_RULES = [
    (('102001', '102002'), 'asset_current'),
    (('106001', '106002', '106003', '106004', '106006', '106007', '106008', '106009'), 'asset_fixed'),
    (('106005', '106010'), 'asset_non_current'),
    (('106011',), 'asset_prepayments'),
    (('400064', '400065', '400066', '400070'), 'expense_depreciation'),
]
CASH_DIFFERENCE_REF = 'Cash difference observed during the counting'
CATEGORIES = [('auto', 'Automatic Fix'), ('decision', 'Fix After Decision'), ('branch', 'Review List')]


class BestStoreCorrectionCenter(models.TransientModel):
    """مركز تصحيح بيست ستور: كل المشاكل المكتشفة بقاعدة البيانات بشاشة وحدة، حالتها الحالية،
    وزر لكل مشكلة: التصحيح (مع معاينة) أو فتح السجلات."""
    _name = 'bs.correction.center'
    _description = 'Best Store Correction Center'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    line_ids = fields.One2many('bs.correction.check', 'center_id', string='Checks')
    auto_line_ids = fields.One2many('bs.correction.check', 'center_id', domain=[('category', '=', 'auto')])
    decision_line_ids = fields.One2many('bs.correction.check', 'center_id', domain=[('category', '=', 'decision')])
    branch_line_ids = fields.One2many('bs.correction.check', 'center_id', domain=[('category', '=', 'branch')])
    checked_at = fields.Datetime(string='Checked At', readonly=True)
    summary = fields.Char(compute='_compute_summary')

    @api.depends('line_ids.state')
    def _compute_summary(self):
        for center in self:
            states = center.line_ids.mapped('state')
            center.summary = _("%(issues)s to fix · %(decisions)s waiting for a decision · %(lists)s to review · %(ok)s OK",
                               issues=states.count('issue'), decisions=states.count('decision'),
                               lists=states.count('review'), ok=states.count('ok'))

    @api.model
    def action_open_center(self):
        center = self.create({})
        center.action_refresh()
        return center._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Best Store Correction Center"),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_refresh(self):
        self.ensure_one()
        self.line_ids.unlink()
        vals_list = []
        # الفحوصات بحسابات وإعدادات الشركة المختارة
        checker = self.with_company(self.company_id)
        for sequence, (code, category, method) in enumerate(checker._check_definitions(), 1):
            vals = method()
            if vals is None:
                continue
            vals.update({'center_id': self.id, 'code': code, 'category': category, 'sequence': sequence})
            vals_list.append(vals)
        self.env['bs.correction.check'].create(vals_list)
        self.checked_at = fields.Datetime.now()
        return self._reopen()

    def _check_definitions(self):
        return [
            ('stock', 'auto', self._check_stock),
            ('pos', 'auto', self._check_pos_receivable),
            ('account_types', 'auto', self._check_account_types),
            ('avco', 'auto', self._check_avco),
            ('pos_categories', 'auto', self._check_pos_categories),
            ('stock_input', 'decision', self._check_stock_input),
            ('assets', 'decision', self._check_assets),
            ('cash_account', 'decision', self._check_cash_account),
            ('duplicate_invoices', 'decision', self._check_duplicate_invoices),
            ('customer_credits', 'decision', self._check_customer_credits),
            ('pending_pickings', 'branch', self._check_pending_pickings),
            ('transit', 'branch', self._check_transit),
            ('negative_stock', 'branch', self._check_negative_stock),
            ('zero_price', 'branch', self._check_zero_price),
            ('no_pos_category', 'branch', self._check_no_pos_category),
            ('duplicate_barcodes', 'branch', self._check_duplicate_barcodes),
            ('duplicate_customers', 'branch', self._check_duplicate_customers),
            ('default_customer', 'branch', self._check_default_customer),
            ('cash_differences', 'branch', self._check_cash_differences),
            ('tax', 'branch', self._check_tax),
            ('unreconciled_payments', 'branch', self._check_unreconciled_payments),
            ('intercompany', 'branch', self._check_intercompany),
            ('customer_debts', 'branch', self._check_customer_debts),
        ]

    # ------------------------------------------------------------------ helpers
    def _result(self, name, records, state=None, amount=0.0, note='', fixable=False):
        """records: السجلات المعنية (لزر Open)."""
        count = len(records)
        return {
            'name': name,
            'state': state or ('ok' if not count else 'issue'),
            'count': count,
            'amount': amount,
            'note': note,
            'fixable': fixable and bool(count),
            'res_model': records._name,
            'res_ids': ','.join(map(str, records.ids)),
        }

    def _company_categories(self):
        return self.env['product.category'].with_company(self.company_id).search([])

    def _stock_accounts(self, key):
        field = {'input': 'property_stock_account_input_categ_id',
                 'output': 'property_stock_account_output_categ_id',
                 'valuation': 'property_stock_valuation_account_id'}[key]
        return self._company_categories().mapped(field)

    def _balance(self, accounts, extra=None):
        if not accounts:
            return 0.0
        groups = self.env['account.move.line']._read_group(
            [('company_id', '=', self.company_id.id), ('account_id', 'in', accounts.ids),
             ('parent_state', '=', 'posted')] + (extra or []), aggregates=['balance:sum'])
        return groups[0][0] or 0.0 if groups else 0.0

    def _internal_quants(self):
        return self.env['stock.quant'].search([
            ('company_id', '=', self.company_id.id), ('location_id.usage', '=', 'internal')])

    # ------------------------------------------------------------------ automatic fixes
    def _check_stock(self):
        wizard = self.env['stock.accounting.correction.wizard'].new({'company_id': self.company_id.id})
        wrong = wizard._wrong_bill_lines()
        valuation = self._balance(self._stock_accounts('valuation'))
        layers = self.env['stock.valuation.layer']._read_group(
            [('company_id', '=', self.company_id.id)], aggregates=['value:sum'])
        layer_value = layers[0][0] or 0.0 if layers else 0.0
        output = self._balance(self._stock_accounts('output'))
        cur = self.company_id.currency_id
        # حركات تقييم بدون قيد: بتحتاج تصحيح بس إذا مجموعها للمنتج مش صفر
        # (تغيير طريقة التقييم بيطلّع البضاعة وبيرجّعها بنفس القيمة)
        unposted = self.env['stock.valuation.layer']._read_group(
            [('company_id', '=', self.company_id.id), ('account_move_id', '=', False), ('value', '!=', 0)],
            groupby=['product_id'], aggregates=['value:sum'])
        missing = len([1 for __, value in unposted if not cur.is_zero(value)])
        gap = layer_value - valuation
        bad = bool(wrong) or not cur.is_zero(gap) or not cur.is_zero(output) or missing
        return self._result(
            _("Stock accounting (vendor bills, stock value, cost of goods sold)"), wrong.move_id,
            state='issue' if bad else 'ok', amount=sum(wrong.mapped('balance')),
            note=_("Bills on a wrong account: %(bills)s · Inventory %(gl)s vs valuation %(svl)s (gap %(gap)s) · "
                   "Stock Output %(out)s · products with valuation movements without entry: %(missing)s",
                   bills=len(wrong.move_id), gl=cur.format(valuation), svl=cur.format(layer_value),
                   gap=cur.format(gap), out=cur.format(output), missing=missing),
            fixable=True) | {'fixable': True}

    def _check_pos_receivable(self):
        account = self.company_id.account_default_pos_receivable_account_id
        if not account:
            return None
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('account_id', '=', account.id),
            ('parent_state', '=', 'posted'), ('reconciled', '=', False), ('amount_residual', '!=', 0)])
        residual = sum(lines.mapped('amount_residual'))
        open_sessions = self.env['pos.session'].search_count([
            ('config_id.company_id', '=', self.company_id.id), ('state', '!=', 'closed')])
        return self._result(
            _("POS receivable account %s (cancelled / edited POS invoices)", account.display_name), lines,
            amount=residual,
            note=_("Open balance %(res)s on %(n)s lines (%(open)s sessions still open: their lines match at closing).",
                   res=self.company_id.currency_id.format(residual), n=len(lines), open=open_sessions),
            fixable=True) | {'fixable': bool(lines)}

    def _wrong_type_accounts(self):
        Account = self.env['account.account'].with_company(self.company_id)
        wrong = []
        for codes, account_type in ACCOUNT_TYPE_RULES:
            for account in Account.search([('code', 'in', codes), ('company_ids', 'in', self.company_id.id)]):
                if account.account_type != account_type:
                    wrong.append((account, account_type))
        return wrong

    def _check_account_types(self):
        wrong = self._wrong_type_accounts()
        accounts = self.env['account.account'].browse([a.id for a, __ in wrong])
        return self._result(
            _("Account types in the chart of accounts (fixed assets, depreciation, Stock Input/Output)"), accounts,
            note=', '.join(f"{a.code} → {t}" for a, t in wrong) or _("All correct."), fixable=True)

    def _wrong_cost_categories(self):
        return self._company_categories().filtered(lambda c: c.property_cost_method != 'average')

    def _check_avco(self):
        categories = self._wrong_cost_categories()
        return self._result(
            _("Product categories not on Average Cost (AVCO)"), categories,
            note=', '.join(categories.mapped('complete_name')[:10]) or _("All on AVCO."), fixable=True)

    def _missing_pos_categories(self):
        """تصنيفات نقطة البيع لمنتجات موجودة بمستودعات الشركة بس مش مسموحة بنقاط بيعها."""
        quants = self._internal_quants().filtered(lambda q: q.quantity > 0)
        products = quants.product_id.filtered(lambda p: p.available_in_pos)
        used = products.pos_categ_ids
        result = {}
        for config in self.env['pos.config'].search([('company_id', '=', self.company_id.id), ('limit_categories', '=', True)]):
            allowed = config.iface_available_categ_ids
            allowed |= self.env['pos.category'].search([('id', 'child_of', allowed.ids)])
            missing = used - allowed
            if missing:
                result[config] = missing
        return result

    def _check_pos_categories(self):
        missing = self._missing_pos_categories()
        categories = self.env['pos.category'].browse({c.id for cats in missing.values() for c in cats})
        return self._result(
            _("POS categories of products in stock not allowed in the Points of Sale"), categories,
            note=' · '.join(f"{config.name}: {len(cats)}" + (_(" (session open)") if config.current_session_id else '')
                            for config, cats in missing.items()) or _("All allowed."),
            fixable=True)

    # ------------------------------------------------------------------ fixes after a decision
    def _stock_input_lines(self):
        accounts = self._stock_accounts('input')
        if not accounts:
            return {}
        groups = self.env['account.move.line']._read_group(
            [('company_id', '=', self.company_id.id), ('account_id', 'in', accounts.ids),
             ('parent_state', '=', 'posted')],
            groupby=['account_id', 'product_id'], aggregates=['balance:sum'])
        cur = self.company_id.currency_id
        return {(account, product): balance for account, product, balance in groups if not cur.is_zero(balance)}

    def _check_stock_input(self):
        lines = self._stock_input_lines()
        products = self.env['product.product'].browse({p.id for __, p in lines if p})
        return self._result(
            _("Stock Input balance left on products"), products, state='decision' if lines else 'ok',
            amount=sum(lines.values()),
            note=_("Each product needs one entry against an account the accountant chooses "
                   "(cost of goods sold, opening balance, ...)."), fixable=True)

    def _asset_bill_lines(self):
        Line = self.env['account.move.line']
        domain = [
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ('in_invoice', 'in_refund')), ('display_type', '=', 'product'),
            '|', ('account_id.account_type', 'in', ('asset_fixed', 'asset_non_current')),
            ('account_id.code', '=like', '106%'),
        ]
        if 'asset_ids' in Line._fields:
            domain.append(('asset_ids', '=', False))
        return Line.search(domain)

    def _check_assets(self):
        if 'account.asset' not in self.env:
            return None
        lines = self._asset_bill_lines()
        return self._result(
            _("Fixed asset purchases without an asset (no depreciation)"), lines,
            state='decision' if lines else 'ok', amount=sum(lines.mapped('balance')),
            note=_("The accountant chooses the asset model (useful life); assets are created as drafts."),
            fixable=True)

    def _wrong_cash_difference_lines(self):
        """فرق الصندوق عند إغلاق الجلسة انقيّد على حساب غير حسابي الربح والخسارة تبع الدفتر."""
        statement_lines = self.env['account.bank.statement.line'].search([
            ('company_id', '=', self.company_id.id), ('pos_session_id', '!=', False),
            ('payment_ref', '=like', CASH_DIFFERENCE_REF + '%')])
        corrected = self.env['account.move'].search([
            ('bs_correction_source_id', 'in', statement_lines.move_id.ids), ('state', '=', 'posted')]).bs_correction_source_id
        wrong = self.env['account.move.line']
        for st_line in statement_lines.filtered(lambda l: l.move_id not in corrected):
            journal = st_line.journal_id
            allowed = journal.default_account_id | journal.loss_account_id | journal.profit_account_id
            wrong |= st_line.move_id.line_ids.filtered(lambda l: l.account_id not in allowed)
        return wrong

    def _check_cash_account(self):
        lines = self._wrong_cash_difference_lines()
        return self._result(
            _("POS cash differences booked on an account other than Cash Difference Loss / Profit"), lines,
            state='decision' if lines else 'ok', amount=sum(lines.mapped('balance')),
            note=', '.join(f"{l.move_id.name}: {l.account_id.display_name} {l.balance:,.2f}" for l in lines)
            or _("All on the loss / profit accounts."), fixable=True)

    def _duplicate_invoice_groups(self):
        invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
            ('invoice_origin', '!=', False)])
        groups = defaultdict(lambda: self.env['account.move'])
        for invoice in invoices:
            groups[(invoice.invoice_origin, invoice.commercial_partner_id.id)] |= invoice
        pos_names = set(self.env['pos.order'].search([
            ('company_id', '=', self.company_id.id),
            ('name', 'in', [origin for (origin, __), moves in groups.items() if len(moves) > 1])]).mapped('name'))
        return {origin: moves for (origin, __), moves in groups.items() if len(moves) > 1 and origin in pos_names}

    def _check_duplicate_invoices(self):
        groups = self._duplicate_invoice_groups()
        invoices = self.env['account.move'].browse([m.id for moves in groups.values() for m in moves])
        return self._result(
            _("POS orders with more than one posted invoice"), invoices,
            state='decision' if groups else 'ok', amount=sum(m.amount_total for moves in groups.values() for m in moves[1:]),
            note=', '.join(f"{origin}: {', '.join(moves.mapped('name'))}" for origin, moves in groups.items())
            or _("None."), fixable=True)

    def _open_customer_credits(self):
        return self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('account_id.account_type', '=', 'asset_receivable'), ('partner_id', '!=', False),
            ('reconciled', '=', False), ('amount_residual', '<', 0),
            ('account_id', '!=', self.company_id.account_default_pos_receivable_account_id.id)])

    def _check_customer_credits(self):
        lines = self._open_customer_credits()
        return self._result(
            _("Customer payments not matched with an invoice (possible duplicate payments)"), lines,
            state='decision' if lines else 'ok', amount=sum(lines.mapped('amount_residual')),
            note=_("Match them with the customer's invoice, or cancel them if the money was already received in the POS."))

    # ------------------------------------------------------------------ review lists (branch)
    def _check_pending_pickings(self):
        pickings = self.env['stock.picking'].search([
            ('company_id', '=', self.company_id.id), ('state', 'not in', ('done', 'cancel'))])
        oldest = min(pickings.mapped('scheduled_date')) if pickings else False
        return self._result(_("Deliveries / receipts not done"), pickings, state='review' if pickings else 'ok',
                            note=_("Oldest: %s", fields.Date.to_string(oldest)) if oldest else '')

    def _check_transit(self):
        quants = self.env['stock.quant'].sudo().search([
            ('location_id.usage', '=', 'transit'), ('company_id', 'in', (False, self.company_id.id)),
            ('quantity', '!=', 0)])
        return self._result(_("Inter-company transit not balanced (should be zero)"), quants,
                            state='review' if quants else 'ok',
                            note=', '.join(f"{q.product_id.display_name[:30]} {q.quantity:g}" for q in quants[:8]))

    def _check_negative_stock(self):
        quants = self._internal_quants().filtered(lambda q: q.quantity < 0)
        return self._result(_("Negative stock"), quants, state='review' if quants else 'ok',
                            note=', '.join(f"{q.product_id.display_name[:30]} {q.quantity:g}" for q in quants[:8]))

    def _check_zero_price(self):
        products = self.env['product.template'].search([
            ('sale_ok', '=', True), ('available_in_pos', '=', True), ('list_price', '=', 0),
            ('company_id', 'in', (False, self.company_id.id))])
        return self._result(_("Products sold in the POS with a zero sales price"), products,
                            state='review' if products else 'ok')

    def _check_no_pos_category(self):
        products = self.env['product.template'].search([
            ('available_in_pos', '=', True), ('pos_categ_ids', '=', False),
            ('company_id', 'in', (False, self.company_id.id))])
        return self._result(_("POS products without a POS category"), products, state='review' if products else 'ok')

    def _check_duplicate_barcodes(self):
        groups = self.env['product.product']._read_group(
            [('barcode', '!=', False), ('company_id', 'in', (False, self.company_id.id))],
            groupby=['barcode'], aggregates=['id:recordset'], having=[('__count', '>', 1)])
        products = self.env['product.product'].browse([p.id for __, recs in groups for p in recs])
        return self._result(_("Duplicate barcodes"), products, state='review' if products else 'ok',
                            note=_("%s barcodes used more than once", len(groups)) if groups else '')

    def _check_duplicate_customers(self):
        partners = self.env['res.partner'].search([
            ('is_company', '=', False), '|', ('phone', '!=', False), ('mobile', '!=', False),
            ('company_id', 'in', (False, self.company_id.id))])
        by_phone = defaultdict(lambda: self.env['res.partner'])
        for partner in partners:
            digits = re.sub(r'\D', '', partner.mobile or partner.phone or '')
            digits = re.sub(r'^(00971|971|0+)', '', digits)
            if len(digits) >= 7:
                by_phone[digits] |= partner
        duplicates = [p for p in by_phone.values() if len(p) > 1]
        records = self.env['res.partner'].browse([r.id for p in duplicates for r in p])
        return self._result(_("Customers with the same phone number"), records, state='review' if records else 'ok',
                            note=_("%s groups", len(duplicates)) if duplicates else '')

    def _check_default_customer(self):
        partners = self.env['res.partner'].search([('name', '=', 'Default Customer')])
        configs = self.env['pos.config'].search([('company_id', '=', self.company_id.id)])
        if 'default_partner_id' in configs._fields:
            partners |= configs.default_partner_id
        orders = self.env['pos.order'].search([
            ('company_id', '=', self.company_id.id), ('partner_id', 'in', partners.ids),
            ('state', 'in', ('paid', 'done', 'invoiced'))])
        return self._result(_("POS sales to the default customer (real customer not recorded)"), orders,
                            state='review' if orders else 'ok', amount=sum(orders.mapped('amount_total')))

    def _check_cash_differences(self):
        statement_lines = self.env['account.bank.statement.line'].search([
            ('company_id', '=', self.company_id.id), ('pos_session_id', '!=', False),
            ('payment_ref', '=like', CASH_DIFFERENCE_REF + '%')])
        losses = statement_lines.filtered(lambda l: l.amount < 0)
        return self._result(_("POS cash differences at session closing"), statement_lines,
                            state='review' if statement_lines else 'ok', amount=sum(statement_lines.mapped('amount')),
                            note=_("Shortages: %(n)s (%(amount)s)", n=len(losses),
                                   amount=self.company_id.currency_id.format(sum(losses.mapped('amount')))))

    def _check_tax(self):
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ('out_invoice', 'out_refund')), ('display_type', '=', 'product'),
            ('tax_ids', '=', False)])
        note = _("Company VAT number (TRN): %s", self.company_id.vat or _("missing"))
        return self._result(_("Sales lines without tax"), lines, state='review' if lines else 'ok', note=note)

    def _check_unreconciled_payments(self):
        payments = self.env['account.payment'].search([
            ('company_id', '=', self.company_id.id), ('state', '=', 'in_process')])
        by_journal = defaultdict(float)
        for payment in payments:
            by_journal[payment.journal_id.name] += payment.amount
        return self._result(_("Payments not matched with a bank statement"), payments,
                            state='review' if payments else 'ok', amount=sum(payments.mapped('amount')),
                            note=' · '.join(f"{j}: {a:,.2f}" for j, a in by_journal.items()))

    def _check_intercompany(self):
        companies = self.env['res.company'].search([('id', '!=', self.company_id.id)]).partner_id
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', ('liability_payable', 'asset_receivable')),
            ('partner_id', 'in', companies.ids), ('reconciled', '=', False), ('amount_residual', '!=', 0)])
        by_partner = defaultdict(float)
        for line in lines:
            by_partner[line.partner_id.name] += line.amount_residual
        return self._result(_("Open balances with the other Best Store companies"), lines,
                            state='review' if lines else 'ok', amount=sum(lines.mapped('amount_residual')),
                            note=' · '.join(f"{p}: {a:,.2f}" for p, a in by_partner.items()))

    def _check_customer_debts(self):
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            ('account_id.account_type', '=', 'asset_receivable'), ('partner_id', '!=', False),
            ('reconciled', '=', False), ('amount_residual', '>', 0),
            ('account_id', '!=', self.company_id.account_default_pos_receivable_account_id.id)])
        by_partner = defaultdict(float)
        for line in lines:
            by_partner[line.partner_id.commercial_partner_id.name] += line.amount_residual
        top = sorted(by_partner.items(), key=lambda x: -x[1])[:5]
        return self._result(_("Customer debts (unpaid invoices)"), lines, state='review' if lines else 'ok',
                            amount=sum(lines.mapped('amount_residual')),
                            note=' · '.join(f"{p}: {a:,.2f}" for p, a in top))

    # ------------------------------------------------------------------ actions
    def _open_wizard(self, model, extra=None):
        wizard = self.env[model].create(dict({'company_id': self.company_id.id}, **(extra or {})))
        return {
            'type': 'ir.actions.act_window',
            'res_model': model,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _fix_stock(self, check):
        return self._open_wizard('stock.accounting.correction.wizard')

    def _fix_pos(self, check):
        return self._open_wizard('pos.receivable.correction.wizard', {
            'account_id': self.company_id.account_default_pos_receivable_account_id.id})

    def _fix_account_types(self, check):
        for account, account_type in self._wrong_type_accounts():
            account.account_type = account_type
        return self.action_refresh()

    def _fix_avco(self, check):
        self._wrong_cost_categories().with_company(self.company_id).write({'property_cost_method': 'average'})
        return self.action_refresh()

    def _fix_pos_categories(self, check):
        # أودو ما بيسمح يتعدّل تصنيفات نقطة بيع وجلستها مفتوحة: منطبّق على المسكّرة بس،
        # والمفتوحة بتضل بالفحص مكتوب جنبها "session open" لحتى تتسكّر جلستها
        missing = self._missing_pos_categories()
        if all(config.current_session_id for config in missing):
            raise UserError(_("Close the session of %s first, then press Fix again.",
                              ', '.join(config.name for config in missing)))
        for config, categories in missing.items():
            if not config.current_session_id:
                config.iface_available_categ_ids = [(4, c.id) for c in categories]
        return self.action_refresh()

    def _fix_stock_input(self, check):
        wizard = self.env['bs.stock.input.fix'].create({'company_id': self.company_id.id})
        wizard._load_lines(self._stock_input_lines())
        return wizard._reopen()

    def _fix_assets(self, check):
        wizard = self.env['bs.asset.create'].create({'company_id': self.company_id.id})
        wizard.line_ids = [(0, 0, {'move_line_id': line.id}) for line in self._asset_bill_lines()]
        return wizard._reopen()

    def _fix_cash_account(self, check):
        wizard = self.env['bs.cash.difference.fix'].create({'company_id': self.company_id.id})
        wizard.line_ids = [(0, 0, {'move_line_id': line.id}) for line in self._wrong_cash_difference_lines()]
        return wizard._reopen()

    def _fix_duplicate_invoices(self, check):
        wizard = self.env['bs.duplicate.invoice.fix'].create({'company_id': self.company_id.id})
        wizard._load_groups(self._duplicate_invoice_groups())
        return wizard._reopen()


class BestStoreCorrectionCheck(models.TransientModel):
    _name = 'bs.correction.check'
    _description = 'Best Store Correction Check'
    _order = 'sequence'

    center_id = fields.Many2one('bs.correction.center', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='center_id.currency_id')
    sequence = fields.Integer()
    code = fields.Char(required=True)
    category = fields.Selection(CATEGORIES, required=True)
    name = fields.Char(string='Check', required=True)
    state = fields.Selection(
        [('issue', 'To Fix'), ('decision', 'Needs a Decision'), ('review', 'To Review'), ('ok', 'OK')],
        string='Status', required=True)
    count = fields.Integer(string='Records')
    amount = fields.Monetary()
    note = fields.Char(string='Details')
    fixable = fields.Boolean()
    res_model = fields.Char()
    res_ids = fields.Char()

    def action_fix(self):
        self.ensure_one()
        center = self.center_id.with_company(self.center_id.company_id)
        method = getattr(center, f'_fix_{self.code}', None)
        if not method:
            raise UserError(_("No automatic fix for this check."))
        return method(self)

    def action_open_records(self):
        self.ensure_one()
        ids = [int(i) for i in (self.res_ids or '').split(',') if i]
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': self.res_model,
            'view_mode': 'list,form',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
        }
