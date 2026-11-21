from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # قيود أداة تصحيح محاسبة المخزون
    stock_correction_batch = fields.Char(string='Stock Correction Batch', copy=False, readonly=True, index=True)
    stock_correction_type = fields.Selection(
        [('reclass', 'Reclassification'), ('revalue', 'Revaluation'), ('sold', 'Sold Part'),
         ('output', 'Stock Output'), ('layer', 'Missing Valuation Entry')],
        string='Stock Correction Type', copy=False, readonly=True)
    stock_correction_redated = fields.Boolean(
        string='Redistributed by Month', copy=False, readonly=True,
        help='This correction entry was reversed and replaced by monthly entries.')
    stock_correction_monthly = fields.Boolean(
        string='Dated by Month', copy=False, readonly=True,
        help='Sold-part / Stock Output entry dated in the month of the sales.')
    stock_correction_source_id = fields.Many2one(
        'account.move', string='Corrected Bill', copy=False, readonly=True, index='btree_not_null')

    # قيود أداة تصحيح حساب نقطة البيع
    pos_correction_batch = fields.Char(string='POS Correction Batch', copy=False, readonly=True, index=True)
    pos_correction_type = fields.Selection(
        [('reverse', 'Wrong Sales Reversal'), ('reinvoice', 'Cancelled Invoice Posted Again'),
         ('missing', 'Missing POS Payment Entry')],
        string='POS Correction Type', copy=False, readonly=True)
    pos_correction_source_id = fields.Many2one(
        'account.move', string='Corrected Entry', copy=False, readonly=True, index='btree_not_null')
    pos_correction_session_id = fields.Many2one(
        'pos.session', string='Corrected Session', copy=False, readonly=True)

    # قيود مركز التصحيح (القرارات: Stock Input، فرق الصندوق)
    bs_correction_batch = fields.Char(string='Correction Center Batch', copy=False, readonly=True, index=True)
    bs_correction_source_id = fields.Many2one(
        'account.move', string='Corrected Entry (Center)', copy=False, readonly=True, index='btree_not_null')
