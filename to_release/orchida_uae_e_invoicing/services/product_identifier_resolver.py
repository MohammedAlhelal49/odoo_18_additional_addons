GTIN_LENGTHS = {8, 12, 13, 14}


def is_valid_gtin(value):
    digits = str(value or '').strip()
    if len(digits) not in GTIN_LENGTHS or not digits.isdigit():
        return False

    total = 0
    weight = 3
    for digit in reversed(digits[:-1]):
        total += int(digit) * weight
        weight = 1 if weight == 3 else 3
    return (10 - total % 10) % 10 == int(digits[-1])


def _call_or_value(record, method_name, field_name):
    method = getattr(record, method_name, None)
    if method:
        value = method()
        if value:
            return value
    return getattr(record, field_name, False)


def _resolve_classification(product, template, tax):
    item_type = _call_or_value(product, '_orchida_get_rcm_item_type', 'orchida_rcm_item_type')
    item_type = item_type or getattr(template, 'orchida_rcm_item_type', False)
    product_type = getattr(product, 'detailed_type', False) or getattr(product, 'type', False)
    commodity_code = item_type or ('S' if product_type == 'service' else 'G')
    nature_code = getattr(tax, 'orchida_rcm_goods_type', False) if tax else False
    nature_code = nature_code or getattr(tax, 'orchida_rcm_nature_code', False) if tax else nature_code
    hs_code = _call_or_value(product, '_orchida_get_hs_code', 'orchida_hs_code')
    hs_code = hs_code or getattr(template, 'orchida_hs_code', False)
    classification = {
        key: field_value
        for key, field_value in (
            ('NatureCode', nature_code),
            ('CommodityCode', commodity_code),
            ('ItemCode', hs_code),
            ('ListID', 'HS' if hs_code else False),
            ('ListVer', getattr(template, 'orchida_hs_list_version', False)),
        )
        if field_value
    }
    return classification


def _resolve_service_accounting_code(product, template):
    sac_code = _call_or_value(product, '_orchida_get_sac_code', 'orchida_sac_code')
    sac_code = sac_code or getattr(template, 'orchida_sac_code', False)
    if not sac_code:
        return []
    service_code = {'SacID': sac_code, 'SacSchemeID': 'SAC'}
    version = getattr(template, 'orchida_sac_scheme_version', False)
    if version:
        service_code['SacSchemeVer'] = version
    return [service_code]


def resolve_product_identifiers(product, tax=None):
    template = getattr(product, 'product_tmpl_id', False)
    standard_id = getattr(product, 'barcode', False) or getattr(product, 'orchida_standard_id', False)
    classification = _resolve_classification(product, template, tax)
    identifiers = {
        'StandardID': standard_id,
        'StandardScheme': '0160' if standard_id else False,
        'Classification': [classification] if classification else [],
        'ServiceAccountingcode': _resolve_service_accounting_code(product, template),
    }
    return {key: field_value for key, field_value in identifiers.items() if field_value}
