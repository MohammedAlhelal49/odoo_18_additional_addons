# Export pricelists, their rules and customer assignments to JSON (run with odoo-bin shell).
#
#   ./odoo-bin shell -c london.conf -d london_laundry_erp --no-http < export_pricelists.py
#
# Writes pricelists.json next to the current directory (override with PRICELIST_JSON env var).
import json
import os

out = os.environ.get('PRICELIST_JSON', 'pricelists.json')
data = {'pricelists': [], 'partners': [], 'pos_configs': []}

for pl in env['product.pricelist'].search([], order='sequence, id'):
    rules = []
    for item in pl.item_ids:
        if item.applied_on != '1_product' or item.compute_price != 'fixed' or item.date_start or item.date_end:
            raise ValueError("Unsupported rule %s on pricelist %s: only fixed prices per product are handled"
                             % (item.id, pl.name))
        rules.append({
            'product': item.product_tmpl_id.name,
            'fixed_price': item.fixed_price,
            'min_quantity': item.min_quantity,
        })
    data['pricelists'].append({'name': pl.name, 'currency': pl.currency_id.name, 'rules': rules})

partners = env['res.partner'].with_context(active_test=False).search([('specific_property_product_pricelist', '!=', False)])
for partner in partners:
    data['partners'].append({'name': partner.name, 'pricelist': partner.specific_property_product_pricelist.name})

for config in env['pos.config'].search([]):
    data['pos_configs'].append({
        'name': config.name,
        'use_pricelist': config.use_pricelist,
        'default': config.pricelist_id.name,
        'available': config.available_pricelist_ids.mapped('name'),
    })

with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Exported %d pricelists, %d rules, %d customers to %s" % (
    len(data['pricelists']), sum(len(p['rules']) for p in data['pricelists']), len(data['partners']), out))
env.cr.rollback()
