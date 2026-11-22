from odoo import fields, models
from odoo.tools.misc import format_date


def _proforma_line(name, display_type='product', qty=0.0, uom=False, price_unit=0.0,
                   discount=0.0, taxes=False, subtotal=0.0):
    return {
        'display_type': display_type,
        'name': name,
        'qty': qty,
        'uom': uom,
        'price_unit': price_unit,
        'discount': discount,
        'taxes': ', '.join((tax.invoice_label or tax.name) for tax in taxes) if taxes else '',
        'subtotal': subtotal,
    }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_proforma_values(self):
        self.ensure_one()
        info = [('Pro Forma No', self.name),
                ('Date', format_date(self.env, self.date_order))]
        if self.validity_date:
            info.append(('Valid Until', format_date(self.env, self.validity_date)))
        if self.user_id:
            info.append(('Salesperson', self.user_id.name))
        if self.client_order_ref:
            info.append(('Customer Reference', self.client_order_ref))
        if self.payment_term_id:
            info.append(('Payment Terms', self.payment_term_id.name))

        lines = []
        for line in self.order_line.filtered(lambda l: not l.is_downpayment):
            if line.display_type:
                lines.append(_proforma_line(line.name, line.display_type))
                continue
            lines.append(_proforma_line(
                line.name, qty=line.product_uom_qty, uom=line.product_uom,
                price_unit=line.price_unit, discount=line.discount,
                taxes=line.tax_id, subtotal=line.price_subtotal,
            ))
        return {
            'partner': self.partner_id,
            'currency': self.currency_id,
            'info': info,
            'lines': lines,
            'amount_untaxed': self.amount_untaxed,
            'amount_tax': self.amount_tax,
            'amount_total': self.amount_total,
            'note': self.note,
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_proforma_values(self):
        self.ensure_one()
        info = [('Pro Forma No', self.name if self.name and self.name != '/' else ''),
                ('Date', format_date(self.env, self.invoice_date or fields.Date.context_today(self)))]
        if self.invoice_date_due:
            info.append(('Due Date', format_date(self.env, self.invoice_date_due)))
        if self.invoice_user_id:
            info.append(('Salesperson', self.invoice_user_id.name))
        if self.invoice_origin:
            info.append(('Source', self.invoice_origin))
        if self.ref:
            info.append(('Customer Reference', self.ref))
        if self.invoice_payment_term_id:
            info.append(('Payment Terms', self.invoice_payment_term_id.name))

        lines = []
        for line in self.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                lines.append(_proforma_line(line.name, line.display_type))
                continue
            lines.append(_proforma_line(
                line.name, qty=line.quantity, uom=line.product_uom_id,
                price_unit=line.price_unit, discount=line.discount,
                taxes=line.tax_ids, subtotal=line.price_subtotal,
            ))
        return {
            'partner': self.partner_id,
            'currency': self.currency_id,
            'info': [row for row in info if row[1]],
            'lines': lines,
            'amount_untaxed': self.amount_untaxed,
            'amount_tax': self.amount_tax,
            'amount_total': self.amount_total,
            'note': self.narration,
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_proforma_values(self):
        """Delivery notes carry no prices: take them from the linked sale order
        line, or fall back to the product's sales price and taxes."""
        self.ensure_one()
        order = self.sale_id
        currency = order.currency_id or self.company_id.currency_id
        partner = order.partner_id or self.partner_id

        info = [('Pro Forma No', self.name),
                ('Date', format_date(self.env, self.date_done or self.scheduled_date))]
        if order:
            info.append(('Sale Order', order.name))
            if order.user_id:
                info.append(('Salesperson', order.user_id.name))
            if order.client_order_ref:
                info.append(('Customer Reference', order.client_order_ref))
            if order.payment_term_id:
                info.append(('Payment Terms', order.payment_term_id.name))
        elif self.origin:
            info.append(('Source', self.origin))

        lines = []
        amount_untaxed = amount_total = 0.0
        for move in self.move_ids.filtered(lambda m: m.state != 'cancel'):
            qty = move.quantity if self.state == 'done' else move.product_uom_qty
            sale_line = move.sale_line_id
            if sale_line:
                price_unit = sale_line.product_uom._compute_price(sale_line.price_unit, move.product_uom)
                discount = sale_line.discount
                taxes = sale_line.tax_id
                name = sale_line.name
            else:
                price_unit = move.product_id.uom_id._compute_price(move.product_id.lst_price, move.product_uom)
                discount = 0.0
                taxes = move.product_id.taxes_id.filtered(lambda t: t.company_id == self.company_id)
                name = move.description_picking or move.product_id.display_name
            res = taxes.compute_all(
                price_unit * (1 - discount / 100.0), currency, qty,
                product=move.product_id, partner=partner,
            )
            amount_untaxed += res['total_excluded']
            amount_total += res['total_included']
            lines.append(_proforma_line(
                name, qty=qty, uom=move.product_uom, price_unit=price_unit,
                discount=discount, taxes=taxes, subtotal=res['total_excluded'],
            ))
        return {
            'partner': partner,
            'currency': currency,
            'info': info,
            'lines': lines,
            'amount_untaxed': amount_untaxed,
            'amount_tax': amount_total - amount_untaxed,
            'amount_total': amount_total,
            'note': order.note if order else False,
        }
