import logging
from datetime import timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    # انسكّرت لحالها (شبكة أمان) بدون جرد: الكاش المعدود انحط = المتوقع
    laundry_auto_closed = fields.Boolean(string='Closed Automatically', readonly=True, copy=False)

    def message_post(self, **kwargs):
        """pos_hr بيكتب "Opened register" / "Closed Register" باسم الكاشير المختار، وأغلب الموظفين
        ما إلهم إيميل، فـ Odoo بيرفض الرسالة وبيفشل فتح وإغلاق الصندوق ("configure the sender's email").
        الرسالة بتضل باسم الكاشير، والمرسل بيصير إيميل المحل (أو المستخدم الحالي، أو OdooBot)."""
        author = kwargs.get('author_id')
        if author and not kwargs.get('email_from'):
            partner = self.env['res.partner'].browse(author if isinstance(author, int) else author.id).exists()
            if partner and not partner.email:
                kwargs['email_from'] = (
                    self.company_id.partner_id.email_formatted
                    or self.env.user.partner_id.email_formatted
                    or self.env.ref('base.partner_root').email_formatted
                )
        return super().message_post(**kwargs)

    def _create_pay_later_receivable_lines(self, data):
        data = super()._create_pay_later_receivable_lines(data)
        # On Credit مفعّل عليه split_transactions: سطر ذمم لكل دفعة، بنفس ترتيب الإنشاء
        # (الـ combine أول، بعدين الـ split). منحفظ سطر كل دفعة تحصيل لنطابقه مع فاتورة طلبها.
        split = data.get('split_receivables_pay_later') or {}
        combine = data.get('combine_receivables_pay_later') or {}
        lines = data.get('pay_later_move_lines') or self.env['account.move.line']
        split_lines = lines[len(combine):]
        data['laundry_collection_lines'] = {
            payment: line
            for payment, line in zip(split.keys(), split_lines)
            if payment.laundry_collected_order_id
        } if len(split_lines) == len(split) else {}
        if len(split_lines) != len(split):
            _logger.warning("Session %s: pay-later receivable lines do not match the payments; "
                            "collections are left unreconciled.", self.name)
        return data

    def _reconcile_account_move_lines(self, data):
        data = super()._reconcile_account_move_lines(data)
        self._laundry_reconcile_collections(data.get('laundry_collection_lines') or {})
        return data

    def _laundry_reconcile_collections(self, collection_lines):
        """كل دفعة تحصيل بتنطابق مع فاتورة الطلب اللي اندفع.

        أي مشكلة ما بتوقف إغلاق الجلسة: الدفعة بتضل "معلّقة" (laundry_reconciled = False)
        ومنكتب السبب على الجلسة، والمبلغ بيضل رصيد للزبون لحتى المحاسب يطابقه يدوياً.
        """
        problems = []
        # إلغاء تحصيل بنفس الجلسة: سطر الإلغاء بيتطابق مع سطر التحصيل الأصلي (صافي صفر)،
        # والفاتورة ما بتنلمس
        for payment, line in list(collection_lines.items()):
            original = payment.laundry_reversed_payment_id
            if not original:
                continue
            collection_lines.pop(payment)
            original_line = collection_lines.pop(original, None)
            label = payment.laundry_collected_order_id.name
            if not original_line:
                problems.append(_("%(order)s: cancelled collection %(original)s is not in this session.",
                                  order=label, original=original.pos_order_id.name))
                continue
            try:
                with self.env.cr.savepoint():
                    (line | original_line).with_context(no_cash_basis=True).reconcile()
                    (payment | original).laundry_reconciled = True
            except Exception as error:  # noqa: BLE001 - never block the session closing
                _logger.exception("Session %s: cannot match collection cancel of %s", self.name, label)
                self.env.invalidate_all()
                problems.append(_("%(order)s: %(error)s", order=label, error=error))

        for payment, line in collection_lines.items():
            target = payment.laundry_collected_order_id
            invoice = target.account_move
            label = target.name
            if invoice.state != 'posted':
                problems.append(_("%(order)s: no posted invoice.", order=label))
                continue
            invoice_lines = invoice.line_ids.filtered(
                lambda l: l.account_id == line.account_id and not l.reconciled)
            if not invoice_lines:
                problems.append(_("%(order)s: invoice %(invoice)s is already paid.",
                                  order=label, invoice=invoice.name))
                continue
            if invoice.currency_id.compare_amounts(-payment.amount, invoice.amount_residual) > 0:
                problems.append(_("%(order)s: collected %(paid)s but only %(due)s was due; "
                                  "the difference stays as customer credit.",
                                  order=label, paid=-payment.amount, due=invoice.amount_residual))
            try:
                with self.env.cr.savepoint():
                    (line | invoice_lines).with_context(no_cash_basis=True).reconcile()
                    payment.laundry_reconciled = True
            except Exception as error:  # noqa: BLE001 - never block the session closing
                _logger.exception("Session %s: cannot reconcile collection of %s", self.name, label)
                self.env.invalidate_all()
                problems.append(_("%(order)s: %(error)s", order=label, error=error))
        if problems:
            self.message_post(body=_(
                "Collections not fully matched with their invoices (to check by the accountant):\n%s",
                "\n".join(problems)))

    # ------------------------------------------------------------------ auto-close
    @api.model
    def _cron_laundry_auto_close(self):
        """كل دقيقة: الجلسات اللي انفتحت قبل آخر وقت إغلاق (بتوقيت المغسلة) ولسا مفتوحة بعد المهلة بتتسكّر."""
        now = pytz.utc.localize(fields.Datetime.now())
        daily = self.env['london.laundry.daily.report']
        for config in self.env['pos.config'].search([('laundry_auto_close', '=', True)]):
            # شاشة الـ POS بتفتح الإغلاق بالوقت المحدد؛ السيرفر بيسكّر بس بعد المهلة (إذا ما حدا سكّر)
            grace = timedelta(minutes=max(config.laundry_auto_close_grace or 0, 0))
            local_now = (now - grace).astimezone(daily._config_tz(config))
            hours = config.laundry_auto_close_time or 0.0
            hour, minute = int(hours), int(round((hours - int(hours)) * 60))
            if minute == 60:
                hour, minute = hour + 1, 0
            cut = local_now.replace(hour=min(hour, 23), minute=minute, second=0, microsecond=0)
            if cut > local_now:
                cut -= timedelta(days=1)
            cut_utc = cut.astimezone(pytz.utc).replace(tzinfo=None)
            sessions = self.search([
                ('config_id', '=', config.id),
                ('state', 'in', ('opened', 'closing_control')),
                ('start_at', '<', cut_utc),
            ])
            for session in sessions:
                session._laundry_auto_close()
                # كل جلسة لحالها: مشكلة بوحدة ما بتلغي إغلاق التانية
                self.env.cr.commit()

    def _laundry_auto_close(self):
        self.ensure_one()
        drafts = self.order_ids.filtered(lambda o: o.state == 'draft')
        # تابات فاضية مفتوحة بالـ POS: ما فيها شي، منلغيها
        empty = drafts.filtered(lambda o: not o.lines and not o.payment_ids)
        if empty:
            empty.write({'state': 'cancel'})
        pending = drafts - empty
        if pending:
            self._laundry_auto_close_failed(_(
                "Not closed automatically: unfinished orders with items (%s). Finish or cancel them, then close the register.",
                ", ".join(pending.mapped('name'))))
            return False
        try:
            with self.env.cr.savepoint():
                if self.config_id.cash_control:
                    result = self.post_closing_cash_details(self.cash_register_balance_end)
                    if isinstance(result, dict) and not result.get('successful', True):
                        raise UserError(result.get('message') or _("The cash details could not be saved."))
                    # الفرق محسوب مع المتوقع وما بيتحدّث لما يتغيّر المعدود (depends ناقصة بـ Odoo)،
                    # وبنفس العملية بيضل الفرق القديم (معدود 0) وبينسجّل خسارة بكامل الكاش
                    self.invalidate_recordset(['cash_register_balance_end', 'cash_register_difference'])
                    if not self.currency_id.is_zero(self.cash_register_difference):
                        raise UserError(_("The cash difference is not zero after setting the counted cash."))
                self.update_closing_control_state_session(_("Closed automatically (no cash count)."))
                result = self.close_session_from_ui()
                if isinstance(result, dict) and not result.get('successful', True):
                    raise UserError(result.get('message') or _("The session could not be closed."))
                self.laundry_auto_closed = True
        except Exception as error:  # noqa: BLE001 - the cron must go on with the other sessions
            _logger.exception("Laundry auto-close failed for session %s", self.name)
            self.env.invalidate_all()
            self._laundry_auto_close_failed(_("Not closed automatically: %s", error))
            return False
        self.message_post(body=_(
            "Closed automatically at the end of the day. The cash was NOT counted: "
            "the counted amount was set to the expected amount."))
        return True

    def _laundry_auto_close_failed(self, message):
        try:
            with self.env.cr.savepoint():
                self.message_post(body=message)
        except Exception:  # noqa: BLE001
            _logger.exception("Laundry auto-close: cannot post on session %s", self.name)

