# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import _, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_invoice_lines(self):
        """الملاحظة الداخلية (Internal Note) على سطر الطلب بتنطبع بالفاتورة تحت المنتج
        (سطر ملاحظة، متل ملاحظة الزبون تبع Odoo)."""
        invoice_lines = super()._prepare_invoice_lines()
        # ملاحظات أسطر الطلب، بنفس الترتيب، لكل منتج
        notes = defaultdict(list)
        for line_values in self._prepare_tax_base_line_values():
            line = line_values['record']
            notes[line.product_id.id].append((line.note or '').strip())
        result = []
        for command in invoice_lines:
            result.append(command)
            vals = command[2] if len(command) > 2 and isinstance(command[2], dict) else {}
            if not vals.get('product_id') or vals.get('display_type'):
                continue
            queue = notes.get(vals['product_id'])
            note = queue.pop(0) if queue else ''
            if note:
                result.append((0, None, {
                    'name': _("Note: %s", note),
                    'display_type': 'line_note',
                }))
        return result
