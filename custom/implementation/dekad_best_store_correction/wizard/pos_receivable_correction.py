import re
from collections import defaultdict

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SESSION_RE = re.compile(r'(POS/\d+)')
REVERSAL_REF_RE = re.compile(r'for order (.+) from session (\S+)$')
# سياق best_store_implementation: بيسمح يرجّع فاتورة نقطة البيع لمسودة (ما بيأثر إذا الموديول مش منصّب)
ALLOW_POS_RESET = 'bs_allow_pos_invoice_reset'
FIX_TYPES = ('reverse', 'reinvoice', 'missing')


class PosReceivableCorrectionWizard(models.TransientModel):
    """تصحيح الرصيد المفتوح على حساب نقطة البيع (Cashier Account) بعد إلغاء فواتير نقطة البيع
    أو إعادة إصدارها أو تعديلها بعد إغلاق الجلسة. الأداة ما بتعدّل قيود الجلسات: بتعمل قيود
    تصحيح بعد المعاينة، وبتطابق الحساب جلسة جلسة."""
    _name = 'pos.receivable.correction.wizard'
    _description = 'POS Receivable Correction'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    account_id = fields.Many2one(
        'account.account', string='POS Receivable Account', required=True,
        default=lambda self: self.env.company.account_default_pos_receivable_account_id,
        domain="[('company_ids', 'in', company_id), ('reconcile', '=', True)]")
    journal_id = fields.Many2one(
        'account.journal', string='Correction Journal', required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        default=lambda self: self._default_journal())
    state = fields.Selection(
        [('draft', 'Draft'), ('preview', 'Preview'), ('done', 'Done')], default='draft', required=True)
    batch = fields.Char(string='Batch', readonly=True)

    line_ids = fields.One2many('pos.receivable.correction.line', 'wizard_id', string='Lines')
    reverse_line_ids = fields.One2many(
        'pos.receivable.correction.line', 'wizard_id', domain=[('correction_type', '=', 'reverse')])
    reinvoice_line_ids = fields.One2many(
        'pos.receivable.correction.line', 'wizard_id', domain=[('correction_type', '=', 'reinvoice')])
    missing_line_ids = fields.One2many(
        'pos.receivable.correction.line', 'wizard_id', domain=[('correction_type', '=', 'missing')])
    match_line_ids = fields.One2many(
        'pos.receivable.correction.line', 'wizard_id', domain=[('correction_type', '=', 'match')])
    summary_html = fields.Html(string='Summary', compute='_compute_summary_html', sanitize=False)

    # ------------------------------------------------------------------ helpers
    @api.model
    def _default_journal(self, company=None):
        journals = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', (company or self.env.company).id)])
        return journals.filtered(lambda j: j.code == 'MISC')[:1] or journals[:1]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.account_id = self.company_id.account_default_pos_receivable_account_id
        self.journal_id = self._default_journal(self.company_id)

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _open_lines(self):
        return self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id), ('account_id', '=', self.account_id.id),
            ('parent_state', '=', 'posted'), ('reconciled', '=', False), ('amount_residual', '!=', 0),
        ], order='date, id')

    def _session_key(self, line):
        """اسم الجلسة اللي بيخصّها سطر على حساب نقطة البيع (حتى لو الجلسة انحذفت)."""
        move = line.move_id.sudo()
        session = (move.pos_session_ids[:1] or move.pos_correction_session_id
                   or move.pos_payment_ids.pos_order_id.session_id[:1]
                   or move.reversed_pos_order_id.session_id
                   or move.origin_payment_id.pos_session_id)
        if session:
            return session.name
        match = (REVERSAL_REF_RE.search(move.ref or '') and REVERSAL_REF_RE.search(move.ref).group(2)) or None
        if match:
            return match
        for text in (line.name, move.ref):
            found = SESSION_RE.search(text or '')
            if found:
                return found.group(1)
        return False

    def _origin_invoices(self, names):
        """فواتير الزبون حسب اسم طلب نقطة البيع (Correct Order بيحذف الطلب الأصلي، فبيبقى الاسم بس)."""
        invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id), ('move_type', '=', 'out_invoice'),
            ('invoice_origin', 'in', list(names))])
        by_origin = defaultdict(lambda: self.env['account.move'])
        for invoice in invoices:
            by_origin[invoice.invoice_origin] |= invoice
        return by_origin

    @staticmethod
    def _before_closing(invoices, session):
        if not session.stop_at:
            return invoices.browse()
        return invoices.filtered(lambda i: i.create_date and i.create_date <= session.stop_at)

    def _real_payments(self, order):
        return order.payment_ids.filtered(lambda p: p.payment_method_id.type != 'pay_later')

    def _receivable_lines(self, move):
        return move.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

    # ------------------------------------------------------------------ analyze
    def action_analyze(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("This correction is already done. Start a new one."))
        if not self.account_id:
            raise UserError(_("Set the POS receivable account."))
        self.line_ids.unlink()
        vals_list = self._wrong_reversal_vals() + self._reinvoice_vals() + self._missing_payment_vals()
        vals_list += self._match_vals()
        self.env['pos.receivable.correction.line'].create(vals_list)
        self.state = 'preview'
        return self._reopen()

    def _wrong_reversal_vals(self):
        """1) قيد "Reversal of POS closing entry" لطلب كان مفوتر وقت إغلاق الجلسة: قيد الإغلاق
        ما فيه مبيعات للطلب، فالقيد العكسي نقّص المبيعات بالغلط. منعكسه بنفس تاريخه.
        إذا الفاتورة الأصلية لسا مرحّلة (ما انلغت)، المبيعات صحيحة بس في فاتورة مكرّرة: سطر للمراجعة بس."""
        Move = self.env['account.move']
        reversals = Move.search([
            ('company_id', '=', self.company_id.id), ('state', '=', 'posted'), ('move_type', '=', 'entry'),
            ('pos_correction_batch', '=', False),
            '|', ('reversed_pos_order_id', '!=', False), ('ref', '=like', 'Reversal of POS closing entry %')])
        corrected = Move.search([('pos_correction_source_id', 'in', reversals.ids), ('state', '=', 'posted')])
        reversals -= corrected.pos_correction_source_id
        reversals = reversals.filtered(lambda m: not m.reversal_move_ids.filtered(lambda r: r.state == 'posted'))

        items = []
        for move in reversals:
            order = move.sudo().reversed_pos_order_id
            session = order.session_id
            if not order:
                found = REVERSAL_REF_RE.search(move.ref or '')
                if not found:
                    continue
                order = self.env['pos.order'].search(
                    [('company_id', '=', self.company_id.id), ('name', '=', found.group(1))], limit=1)
                session = order.session_id or self.env['pos.session'].search([('name', '=', found.group(2))], limit=1)
            if not order or not session:
                continue
            amount = -sum(move.line_ids.filtered(lambda l: l.account_id == self.account_id).mapped('balance'))
            if self.currency_id.is_zero(amount):
                continue
            items.append((move, order, session, amount))

        invoices = self._origin_invoices({order.name for __, order, __, __ in items})
        vals_list = []
        for move, order, session, amount in items:
            order_invoices = invoices[order.name]
            before = self._before_closing(order_invoices, session)
            if not before:
                continue  # الطلب انفوتر بعد الإغلاق لأول مرة: القيد العكسي صحيح
            still_posted = before.filtered(lambda i: i.state == 'posted')
            new_invoice = (order_invoices - before).filtered(lambda i: i.state == 'posted')[-1:]
            if still_posted:
                note = _("The invoice issued before the closing %(old)s is still posted: sales are right, "
                         "but %(new)s is a duplicate invoice. Review it instead of reversing.",
                         old=', '.join(still_posted.mapped('name')), new=new_invoice.name or _('the new invoice'))
            else:
                note = _("Invoice %(old)s (before the closing) cancelled, %(new)s issued after the closing.",
                         old=', '.join(before.mapped('name')), new=new_invoice.name or '-')
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'reverse', 'selected': not still_posted,
                'source_move_id': move.id, 'order_name': order.name, 'session_name': session.name,
                'session_id': session.id, 'invoice_id': new_invoice.id, 'partner_id': order.partner_id.id,
                'date': move.date, 'amount': amount, 'note': note,
            })
        return vals_list

    def _reinvoice_vals(self):
        """2) طلب كان مفوتر وقت الإغلاق، فاتورته انلغت وما انعادت: قيد الإغلاق سجّل القبض بس،
        فالمبيعات ناقصة. منرجّع الفاتورة الملغاة نفسها (نفس الرقم والتاريخ) ومنسجّل قبضها من حساب نقطة البيع."""
        cancelled = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id), ('move_type', '=', 'out_invoice'),
            ('state', '=', 'cancel'), ('invoice_origin', '!=', False)])
        names = set(cancelled.mapped('invoice_origin'))
        if not names:
            return []
        orders = self.env['pos.order'].search([
            ('company_id', '=', self.company_id.id), ('name', 'in', list(names)),
            ('session_id.state', '=', 'closed'), ('account_move', '=', False), ('state', 'in', ('paid', 'done'))])
        invoices = self._origin_invoices(orders.mapped('name'))
        vals_list = []
        for order in orders:
            order_invoices = invoices[order.name]
            if order_invoices.filtered(lambda i: i.state == 'posted'):
                continue
            before = self._before_closing(order_invoices, order.session_id).filtered(lambda i: i.state == 'cancel')
            if not before:
                continue
            invoice = before.sorted('id')[-1]
            payments = self._real_payments(order)
            amount = sum(payments.mapped('amount'))
            notes, selected = [], True
            if self.currency_id.compare_amounts(invoice.amount_total, order.amount_total):
                notes.append(_("Invoice total %(inv)s differs from the order total %(order)s.",
                               inv=invoice.amount_total, order=order.amount_total))
                selected = False
            if order.payment_ids - payments:
                notes.append(_("The order is partly paid on credit."))
                selected = False
            notes.insert(0, _("Post %(inv)s again and book its payment (%(methods)s).",
                              inv=invoice.name, methods=', '.join(payments.payment_method_id.mapped('name'))))
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'reinvoice', 'selected': selected,
                'invoice_id': invoice.id, 'order_id': order.id, 'order_name': order.name,
                'session_name': order.session_id.name, 'session_id': order.session_id.id,
                'partner_id': invoice.commercial_partner_id.id, 'date': invoice.invoice_date or invoice.date,
                'amount': amount, 'note': ' '.join(notes),
            })
        return vals_list

    def _missing_payment_vals(self):
        """3) فاتورة نقطة بيع مرحّلة بس دفعات طلبها بدون قيد دفعة (الفاتورة انرجعت مسودة وانحذف قيد
        الدفعة، وغالباً انسجّلت دفعة يدوية). قيد الإغلاق سجّل القبض، فالدفعة اليدوية مكرّرة."""
        Move = self.env['account.move']
        invoices = Move.search([
            ('company_id', '=', self.company_id.id), ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'), ('pos_order_ids', '!=', False)])
        # فواتير صحّحتها الأداة قبل (دفعتها صارت قيد تصحيح، مش قيد دفعة نقطة بيع)
        done = Move.search([('pos_correction_type', 'in', ('missing', 'reinvoice')), ('state', '=', 'posted'),
                            ('pos_correction_source_id', 'in', invoices.ids)]).pos_correction_source_id
        vals_list = []
        for invoice in invoices - done:
            orders = invoice.sudo().pos_order_ids.filtered(lambda o: o.session_id.state == 'closed')
            payments = orders.payment_ids.filtered(
                lambda p: p.payment_method_id.type != 'pay_later' and not p.account_move_id)
            amount = sum(payments.mapped('amount'))
            if not payments or self.currency_id.is_zero(amount):
                continue
            receivable = self._receivable_lines(invoice)
            counterparts = (receivable.matched_credit_ids.credit_move_id
                            | receivable.matched_debit_ids.debit_move_id)
            if counterparts:
                note = _("Paid by %(pays)s although the POS already received %(amount)s (%(methods)s): "
                         "the manual payment stays open on the customer, cancel it if it is a duplicate.",
                         pays=', '.join(counterparts.move_id.mapped('name')), amount=amount,
                         methods=', '.join(payments.payment_method_id.mapped('name')))
            else:
                note = _("Unpaid, although the POS received %(amount)s (%(methods)s).",
                         amount=amount, methods=', '.join(payments.payment_method_id.mapped('name')))
            if self.currency_id.compare_amounts(abs(amount), invoice.amount_total) < 0:
                note += ' ' + _("The invoice (%s) is higher than the POS payment.", invoice.amount_total)
            session = orders.session_id[:1]
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'missing', 'selected': not counterparts,
                'invoice_id': invoice.id, 'order_id': orders[:1].id, 'order_name': ', '.join(orders.mapped('name')),
                'session_name': session.name, 'session_id': session.id,
                'partner_id': invoice.commercial_partner_id.id, 'date': invoice.invoice_date or invoice.date,
                'amount': amount, 'note': note,
            })
        return vals_list

    def _match_vals(self):
        """4) مطابقة الأسطر المفتوحة على حساب نقطة البيع جلسة جلسة (بدون قيود)."""
        groups = defaultdict(lambda: self.env['account.move.line'])
        unknown = self.env['account.move.line']
        for line in self._open_lines():
            key = self._session_key(line)
            if key:
                groups[key] |= line
            else:
                unknown |= line
        vals_list = []
        for key, lines in sorted(groups.items()):
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'match', 'session_name': key,
                'amount': sum(lines.mapped('amount_residual')),
                'match_line_ids': [(6, 0, lines.ids)],
                'note': _("%s open lines", len(lines)),
            })
        if unknown:
            vals_list.append({
                'wizard_id': self.id, 'correction_type': 'match', 'selected': False,
                'session_name': _("No session"), 'amount': sum(unknown.mapped('amount_residual')),
                'match_line_ids': [(6, 0, unknown.ids)],
                'note': _("Lines not linked to a session: match them by hand."),
            })
        return vals_list

    # ------------------------------------------------------------------ summary
    @api.depends('line_ids.selected', 'line_ids.amount', 'state')
    def _compute_summary_html(self):
        for wizard in self:
            if wizard.state == 'draft' or not wizard.account_id:
                wizard.summary_html = False
                continue
            fmt = wizard.currency_id.format
            selected = wizard.line_ids.filtered('selected')
            labels = [
                ('reverse', _("1. Wrong sales reversals reversed (Dr POS receivable / Cr Sales)")),
                ('reinvoice', _("2. Cancelled invoices posted again (Dr POS receivable / Cr Customer)")),
                ('missing', _("3. Missing POS payment entries (Dr POS receivable / Cr Customer)")),
            ]
            balance = sum(wizard._open_lines().mapped('amount_residual')) if wizard.state == 'preview' else None
            rows = Markup('')
            effect = 0.0
            for ctype, label in labels:
                lines = wizard.line_ids.filtered(lambda l: l.correction_type == ctype)
                chosen = lines & selected
                effect += sum(chosen.mapped('amount'))
                rows += Markup('<tr><td>%s</td><td class="text-end">%s / %s</td><td class="text-end">%s</td></tr>') % (
                    label, len(chosen), len(lines), fmt(sum(chosen.mapped('amount'))))
            matched = selected.filtered(lambda l: l.correction_type == 'match')
            rows += Markup('<tr><td>%s</td><td class="text-end">%s</td><td class="text-end">-</td></tr>') % (
                _("4. Sessions to match (no entry)"), len(matched))
            if balance is not None:
                rows += Markup('<tr class="fw-bold"><td>%s</td><td></td><td class="text-end">%s</td></tr>') % (
                    _("Open balance of %s now", wizard.account_id.display_name), fmt(balance))
                rows += Markup('<tr class="fw-bold"><td>%s</td><td></td><td class="text-end">%s</td></tr>') % (
                    _("Open balance after the corrections"), fmt(balance + effect))
            wizard.summary_html = Markup(
                '<table class="table table-sm o_main_table"><thead><tr><th>%s</th><th class="text-end">%s</th>'
                '<th class="text-end">%s</th></tr></thead><tbody>%s</tbody></table>') % (
                _("Correction"), _("Selected"), _("Amount"), rows)

    # ------------------------------------------------------------------ create
    def action_create_entries(self):
        self.ensure_one()
        if self.state != 'preview':
            raise UserError(_("Analyze first."))
        selected = self.line_ids.filtered('selected')
        if not selected:
            raise UserError(_("Select at least one line."))
        lock_date = self.company_id._get_user_fiscal_lock_date(self.journal_id)
        if any(line.date and line.date <= lock_date for line in selected.filtered(lambda l: l.correction_type in FIX_TYPES)):
            raise UserError(_("Some correction dates are on or before the lock date (%s).", lock_date))

        batch = 'POSCORR/%s/%s' % (self.company_id.id, fields.Datetime.now().strftime('%Y%m%d-%H%M%S'))
        tags = {'pos_correction_batch': batch}
        for line in selected.filtered(lambda l: l.correction_type == 'reverse'):
            self._apply_reverse(line, tags)
        for line in selected.filtered(lambda l: l.correction_type == 'reinvoice'):
            self._apply_reinvoice(line, tags)
        for line in selected.filtered(lambda l: l.correction_type == 'missing'):
            self._apply_missing(line, tags)
        self._apply_matching(selected.filtered(lambda l: l.correction_type == 'match').mapped('session_name'))
        self.write({'state': 'done', 'batch': batch})
        return self.action_open_entries()

    def _apply_reverse(self, line, tags):
        source = line.source_move_id
        reverse = source._reverse_moves([dict(
            tags, journal_id=self.journal_id.id, date=source.date, reversed_pos_order_id=False,
            ref=_("POS correction - reversal of %(move)s (order %(order)s was invoiced before the closing)",
                  move=source.name, order=line.order_name),
            pos_correction_type='reverse', pos_correction_source_id=source.id,
            pos_correction_session_id=line.session_id.id)])
        reverse.action_post()

    def _receivable_entry(self, line, invoice, tags, ctype, ref):
        """مدين حساب نقطة البيع / دائن ذمم الزبون، ومطابقته مع الفاتورة."""
        receivable = self._receivable_lines(invoice)[:1]
        amount = line.amount
        move = self.env['account.move'].with_company(self.company_id).create(dict(
            tags, move_type='entry', journal_id=self.journal_id.id, company_id=self.company_id.id,
            date=line.date, ref=ref, pos_correction_type=ctype, pos_correction_source_id=invoice.id,
            pos_correction_session_id=line.session_id.id,
            line_ids=[
                (0, 0, {'account_id': self.account_id.id, 'name': ref,
                        'debit': max(amount, 0.0), 'credit': max(-amount, 0.0)}),
                (0, 0, {'account_id': receivable.account_id.id, 'partner_id': invoice.commercial_partner_id.id,
                        'name': ref, 'debit': max(-amount, 0.0), 'credit': max(amount, 0.0)}),
            ]))
        move.action_post()
        (receivable | move.line_ids.filtered(lambda l: l.account_id == receivable.account_id)).reconcile()
        return move

    def _apply_reinvoice(self, line, tags):
        invoice = line.invoice_id.with_context(**{ALLOW_POS_RESET: True})
        if invoice.state == 'cancel':
            invoice.button_draft()
        if invoice.state == 'draft':
            invoice.action_post()
        order = line.order_id.sudo()
        order.write({'account_move': invoice.id, 'state': 'invoiced'})
        self._receivable_entry(line, invoice, tags, 'reinvoice', _(
            "POS correction - payment of %(inv)s received in session %(session)s (order %(order)s)",
            inv=invoice.name, session=line.session_name, order=line.order_name))
        invoice.message_post(body=_("Posted again by the POS receivable correction (%s): the order was invoiced "
                                    "before its session was closed and the invoice had been cancelled.", tags['pos_correction_batch']))

    def _apply_missing(self, line, tags):
        invoice = line.invoice_id
        receivable = self._receivable_lines(invoice)
        counterparts = (receivable.matched_credit_ids.credit_move_id | receivable.matched_debit_ids.debit_move_id)
        if counterparts:
            receivable.remove_move_reconcile()
        self._receivable_entry(line, invoice, tags, 'missing', _(
            "POS correction - POS payment of %(inv)s received in session %(session)s (order %(order)s)",
            inv=invoice.name, session=line.session_name, order=line.order_name))
        # الدفعة اليدوية: منرجّع منها بس الجزء اللي الفاتورة لسا بحاجته، والباقي بيضل مفتوح على الزبون
        remaining = receivable.filtered(lambda l: not l.reconciled)
        if remaining and counterparts:
            (remaining | counterparts.filtered(lambda l: not l.reconciled)).reconcile()
        if counterparts:
            invoice.message_post(body=_(
                "POS receivable correction (%(batch)s): the invoice is now paid by its POS payment. "
                "Payment(s) %(pays)s stay open on the customer: cancel them if they are duplicates.",
                batch=tags['pos_correction_batch'], pays=', '.join(counterparts.move_id.mapped('name'))))

    def _apply_matching(self, session_names):
        if not session_names:
            return
        wanted = set(session_names)
        groups = defaultdict(lambda: self.env['account.move.line'])
        for line in self._open_lines():
            key = self._session_key(line)
            if key in wanted:
                groups[key] |= line
        for lines in groups.values():
            if lines.filtered(lambda l: l.amount_residual > 0) and lines.filtered(lambda l: l.amount_residual < 0):
                lines.reconcile()

    def action_open_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("POS Correction %s", self.batch),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('pos_correction_batch', '=', self.batch)],
            'context': {'create': False},
        }


class PosReceivableCorrectionLine(models.TransientModel):
    _name = 'pos.receivable.correction.line'
    _description = 'POS Receivable Correction Line'
    _order = 'correction_type, date, id'

    wizard_id = fields.Many2one('pos.receivable.correction.wizard', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    correction_type = fields.Selection(
        [('reverse', 'Wrong Sales Reversal'), ('reinvoice', 'Cancelled Invoice Posted Again'),
         ('missing', 'Missing POS Payment Entry'), ('match', 'Session Matching')], required=True)
    selected = fields.Boolean(string='Apply', default=True)
    date = fields.Date(readonly=True)
    session_name = fields.Char(string='Session', readonly=True)
    session_id = fields.Many2one('pos.session', string='POS Session', readonly=True)
    order_name = fields.Char(string='Order', readonly=True)
    order_id = fields.Many2one('pos.order', string='POS Order', readonly=True)
    source_move_id = fields.Many2one('account.move', string='Entry to Reverse', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    amount = fields.Monetary(readonly=True)
    residual_after = fields.Monetary(string='Open After', compute='_compute_residual_after')
    match_line_ids = fields.Many2many('account.move.line', string='Open Lines', readonly=True)
    note = fields.Char(readonly=True)

    @api.depends('amount', 'wizard_id.line_ids.selected')
    def _compute_residual_after(self):
        for line in self:
            if line.correction_type != 'match':
                line.residual_after = 0.0
                continue
            fixes = line.wizard_id.line_ids.filtered(
                lambda l: l.selected and l.correction_type in FIX_TYPES and l.session_name == line.session_name)
            line.residual_after = line.amount + sum(fixes.mapped('amount'))
