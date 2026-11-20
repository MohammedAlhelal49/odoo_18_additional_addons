# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    paid_by = fields.Char(
        string='Paid By',
        compute='_compute_paid_by',
        store=True,
        index=True,
        help='Payment methods actually used to pay this invoice: POS payment '
             'methods for POS invoices, and the journals of registered payments.'
    )

    @api.depends('move_type', 'payment_state',
                 'pos_order_ids.payment_ids.payment_method_id',
                 'pos_order_ids.payment_ids.amount',
                 'line_ids.matched_debit_ids', 'line_ids.matched_credit_ids')
    def _compute_paid_by(self):
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                move.paid_by = False
                continue

            names = set()

            # POS invoices: the payment methods used on the POS order(s).
            for payment in move.pos_order_ids.payment_ids:
                if payment.amount and payment.payment_method_id:
                    names.add(payment.payment_method_id.name)

            # Registered payments / bank reconciliations: the journal of the
            # counterpart entry. POS payment and session entries are skipped
            # (already covered above), as are credit notes / other invoices.
            receivable_lines = move.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
            counterparts = (receivable_lines.matched_debit_ids.debit_move_id
                            | receivable_lines.matched_credit_ids.credit_move_id).move_id - move
            for counterpart in counterparts:
                if counterpart.is_invoice(include_receipts=True):
                    continue
                if counterpart.pos_payment_ids or counterpart.pos_session_ids:
                    continue
                if counterpart.journal_id:
                    names.add(counterpart.journal_id.name)

            move.paid_by = ', '.join(sorted(names)) if names else False
