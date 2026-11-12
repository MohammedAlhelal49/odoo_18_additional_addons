#!/usr/bin/env python3
"""Create pricelists, their fixed-price rules and customer assignments on a target Odoo over XML-RPC.

Input is the JSON written by export_pricelists.py. Dry run by default: it prints what it would do and
writes nothing. Add --apply to write. Safe to run again: existing pricelists, rules and assignments
are reused, not duplicated.

Products and customers are matched by name (ignoring case and extra spaces) with search_read, not
name_search, so overridden name searches do not interfere.

    export ODOO_URL=https://example.com ODOO_DB=dbname ODOO_USER=login ODOO_API_KEY=...
    python3 migrate_pricelists.py pricelists.json            # dry run
    python3 migrate_pricelists.py pricelists.json --apply    # write
"""
import argparse
import json
import os
import sys
import xmlrpc.client


def norm(value):
    return ' '.join((value or '').split()).casefold()


class Odoo:
    def __init__(self, url, db, user, key):
        self.db, self.key = db, key
        self.uid = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/common').authenticate(db, user, key, {})
        if not self.uid:
            sys.exit("Authentication failed for %s on %s" % (user, db))
        self.models = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/object', allow_none=True)

    def call(self, model, method, *args, **kwargs):
        kwargs.setdefault('context', {}).setdefault('lang', 'en_US')
        return self.models.execute_kw(self.db, self.uid, self.key, model, method, list(args), kwargs)


def index_by_name(records):
    """{normalized name: id}; names used by more than one record are reported, not guessed."""
    index, dupes = {}, set()
    for rec in records:
        key = norm(rec['name'])
        if key in index:
            dupes.add(key)
        index[key] = rec['id']
    return index, dupes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', help="JSON file from export_pricelists.py")
    parser.add_argument('--apply', action='store_true', help="write the changes (default: dry run)")
    args = parser.parse_args()

    missing = [v for v in ('ODOO_URL', 'ODOO_DB', 'ODOO_USER', 'ODOO_API_KEY') if not os.environ.get(v)]
    if missing:
        sys.exit("Missing environment variables: %s" % ', '.join(missing))
    with open(args.source, encoding='utf-8') as f:
        data = json.load(f)

    odoo = Odoo(os.environ['ODOO_URL'].rstrip('/'), os.environ['ODOO_DB'], os.environ['ODOO_USER'], os.environ['ODOO_API_KEY'])
    print("Connected to %s as uid %s — %s\n" % (os.environ['ODOO_DB'], odoo.uid, 'APPLY' if args.apply else 'DRY RUN'))
    problems = []

    # --- resolve everything first; nothing is written if anything is missing or ambiguous
    currencies = {c['name']: c['id'] for c in odoo.call(
        'res.currency', 'search_read', [], fields=['name'], context={'active_test': False})}

    wanted_products = {norm(r['product']): r['product'] for p in data['pricelists'] for r in p['rules']}
    products, product_dupes = index_by_name(
        odoo.call('product.template', 'search_read', [], fields=['name']))
    for key, name in sorted(wanted_products.items()):
        if key not in products:
            problems.append("Product not found: %r" % name)
        elif key in product_dupes:
            problems.append("Product name used more than once: %r" % name)

    target_pricelists = odoo.call('product.pricelist', 'search_read', [], fields=['name', 'currency_id'])
    existing_pl = {}
    for pl in target_pricelists:
        existing_pl.setdefault((norm(pl['name']), pl['currency_id'][0]), []).append(pl['id'])

    plan_pricelists = []  # (source pricelist, target id or None)
    for src in data['pricelists']:
        currency_id = currencies.get(src['currency'])
        if not currency_id:
            problems.append("Currency not found: %s (pricelist %r)" % (src['currency'], src['name']))
            continue
        ids = existing_pl.get((norm(src['name']), currency_id), [])
        if len(ids) > 1:
            problems.append("Pricelist exists more than once in target: %r" % src['name'])
            continue
        plan_pricelists.append((src, currency_id, ids[0] if ids else None))

    source_pl_names = {norm(p['name']) for p in data['pricelists']}
    plan_partners = []
    for src in data['partners']:
        if norm(src['pricelist']) not in source_pl_names:
            problems.append("Customer %r uses pricelist %r which is not in the export" % (src['name'], src['pricelist']))
            continue
        found = [p for p in odoo.call('res.partner', 'search_read', [('name', 'ilike', ' '.join(src['name'].split()))],
                                      fields=['name', 'property_product_pricelist'])
                 if norm(p['name']) == norm(src['name'])]
        if len(found) != 1:
            problems.append("Customer %s: %r" % ('not found' if not found else 'found %d times' % len(found), src['name']))
            continue
        plan_partners.append((src, found[0]))

    if problems:
        print("STOPPED — fix these in the target first, nothing was written:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)

    # --- pricelists and rules
    stats = dict.fromkeys(['pl_new', 'pl_kept', 'rule_new', 'rule_same', 'rule_price', 'cust_set', 'cust_same'], 0)
    pricelist_ids = {}
    for src, currency_id, target_id in plan_pricelists:
        if target_id:
            stats['pl_kept'] += 1
            existing_rules = odoo.call('product.pricelist.item', 'search_read',
                                       [('pricelist_id', '=', target_id), ('applied_on', '=', '1_product')],
                                       fields=['product_tmpl_id', 'min_quantity', 'fixed_price', 'compute_price'])
            print("= %-20s exists (id %s)" % (src['name'], target_id))
        else:
            stats['pl_new'] += 1
            existing_rules = []
            print("+ %-20s new" % src['name'])
            if args.apply:
                target_id = odoo.call('product.pricelist', 'create', {'name': src['name'], 'currency_id': currency_id})
        pricelist_ids[norm(src['name'])] = target_id
        rules_by_key = {(r['product_tmpl_id'][0], r['min_quantity']): r for r in existing_rules if r['product_tmpl_id']}

        for rule in src['rules']:
            product_id = products[norm(rule['product'])]
            current = rules_by_key.get((product_id, rule['min_quantity']))
            if current and current['compute_price'] == 'fixed' and current['fixed_price'] == rule['fixed_price']:
                stats['rule_same'] += 1
                continue
            if current:
                stats['rule_price'] += 1
                print("    ~ %-20s %s -> %s" % (rule['product'].strip(), current['fixed_price'], rule['fixed_price']))
                if args.apply:
                    odoo.call('product.pricelist.item', 'write', [current['id']],
                              {'compute_price': 'fixed', 'fixed_price': rule['fixed_price']})
                continue
            stats['rule_new'] += 1
            print("    + %-20s %s" % (rule['product'].strip(), rule['fixed_price']))
            if args.apply:
                odoo.call('product.pricelist.item', 'create', {
                    'pricelist_id': target_id, 'applied_on': '1_product', 'product_tmpl_id': product_id,
                    'compute_price': 'fixed', 'fixed_price': rule['fixed_price'], 'min_quantity': rule['min_quantity'],
                })

    # --- customers
    print()
    for src, partner in plan_partners:
        current = partner['property_product_pricelist']
        target_id = pricelist_ids[norm(src['pricelist'])]
        if current and target_id and current[0] == target_id:
            stats['cust_same'] += 1
            continue
        stats['cust_set'] += 1
        print("@ %-40s %s -> %s" % (partner['name'], current[1] if current else '-', src['pricelist']))
        if args.apply:
            odoo.call('res.partner', 'write', [partner['id']], {'property_product_pricelist': target_id})

    print("\nPricelists: %(pl_new)d new, %(pl_kept)d existing | Rules: %(rule_new)d new, %(rule_price)d price changed, "
          "%(rule_same)d unchanged | Customers: %(cust_set)d to set, %(cust_same)d already set" % stats)
    for config in data.get('pos_configs', []):
        print("POS %r (set by hand): Flexible Pricelists=%s, Default=%s, Available=%s"
              % (config['name'], config['use_pricelist'], config['default'], ', '.join(config['available'])))
    if not args.apply:
        print("\nDry run: nothing was written. Re-run with --apply to write.")


if __name__ == '__main__':
    main()
