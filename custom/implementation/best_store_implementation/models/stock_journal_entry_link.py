from odoo import _, api, fields, models

from .payment_invoice_link import _x2many_search

# قيد المخزون (STJ) مربوط بحركة المخزون مباشرة، أو بطبقة التقييم (قيود أداة التصحيح)
PICKING_ENTRY_PATHS = (
    'move_ids.account_move_ids',
    'move_ids.stock_valuation_layer_ids.account_move_id',
)
ENTRY_PICKING_PATHS = (
    'stock_move_id.picking_id',
    'stock_valuation_layer_ids.stock_move_id.picking_id',
)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bs_journal_entry_ids = fields.Many2many(
        'account.move', string='Journal Entries', compute='_compute_bs_journal_entries',
        search='_search_bs_journal_entry_ids',
        help="Inventory valuation entries (STJ) of this transfer.")
    bs_journal_entry_count = fields.Integer(compute='_compute_bs_journal_entries')
    bs_zero_valuation = fields.Boolean(
        compute='_compute_bs_journal_entries',
        help="Done transfer valued at zero: the product cost was zero, so there is no journal entry.")

    @api.depends('move_ids.account_move_ids', 'move_ids.stock_valuation_layer_ids.account_move_id',
                 'move_ids.stock_valuation_layer_ids.value', 'state')
    def _compute_bs_journal_entries(self):
        for picking in self:
            moves = picking.sudo().move_ids
            entries = (moves.account_move_ids | moves.stock_valuation_layer_ids.account_move_id).filtered(
                lambda m: m.state == 'posted')
            picking.bs_journal_entry_ids = entries
            picking.bs_journal_entry_count = len(entries)
            layers = moves.stock_valuation_layer_ids
            picking.bs_zero_valuation = bool(
                picking.state == 'done' and not entries and layers
                and all(picking.company_id.currency_id.is_zero(value) for value in layers.mapped('value')))

    def _search_bs_journal_entry_ids(self, operator, value):
        # "بدون قيد" = كل التحويلات ناقص اللي إلها قيد (النفي جوّا مسارات x2many بيضيّع السجلات الفاضية)
        if (operator == '=' and not value) or operator == 'not ilike':
            positive = self._search_bs_journal_entry_ids('!=' if operator == '=' else 'ilike', value)
            return [('id', 'not in', self._search(positive))]
        return _x2many_search(PICKING_ENTRY_PATHS, operator, value, extra=[('state', '=', 'posted')])

    def action_view_bs_journal_entries(self):
        self.ensure_one()
        entries = self.bs_journal_entry_ids
        action = {
            'type': 'ir.actions.act_window',
            'name': _("Journal Entries of %s", self.name),
            'res_model': 'account.move',
            'context': {'create': False},
        }
        if len(entries) == 1:
            return dict(action, view_mode='form', res_id=entries.id, views=[(self.env.ref('account.view_move_form').id, 'form')])
        # قائمة القيود اليومية (مش قائمة الفواتير)
        return dict(action, view_mode='list,form', domain=[('id', 'in', entries.ids)],
                    views=[(self.env.ref('account.view_move_tree').id, 'list'),
                           (self.env.ref('account.view_move_form').id, 'form')])


class AccountMove(models.Model):
    _inherit = 'account.move'

    bs_picking_ids = fields.Many2many(
        'stock.picking', string='Transfers', compute='_compute_bs_picking_ids', search='_search_bs_picking_ids',
        help="Receipts / deliveries this inventory valuation entry comes from.")

    @api.depends('stock_move_id', 'stock_valuation_layer_ids.stock_move_id')
    def _compute_bs_picking_ids(self):
        for move in self:
            sudo_move = move.sudo()
            move.bs_picking_ids = (sudo_move.stock_move_id.picking_id
                                   | sudo_move.stock_valuation_layer_ids.stock_move_id.picking_id)

    def _search_bs_picking_ids(self, operator, value):
        if (operator == '=' and not value) or operator == 'not ilike':
            positive = self._search_bs_picking_ids('!=' if operator == '=' else 'ilike', value)
            return [('id', 'not in', self._search(positive))]
        return _x2many_search(ENTRY_PICKING_PATHS, operator, value)
