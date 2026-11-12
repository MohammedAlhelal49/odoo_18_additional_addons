import re

from .payload_mapper import (
    AE_RCM_RATE,
    _build_uom_code_map,
    _buyer_country_subentity,
    _document_ac_product_ids,
    _get_aed_currency,
    _is_regular_invoice_line,
)
from .product_identifier_resolver import is_valid_gtin, resolve_product_identifiers


AE_SUBENTITIES = {'AUH', 'DXB', 'SHJ', 'UAQ', 'FUJ', 'AJM', 'RAK'}
SUPPORTED_TAX_CATEGORIES = {'S', 'Z', 'E', 'O', 'AE', 'N'}
OUT_OF_SCOPE_TAX_CATEGORIES = {'E', 'O', 'Z'}
CREDIT_NOTE_REASONS = {
    'DL8.61.1.A': 'If the supply was cancelled.',
    'DL8.61.1.B': 'If the tax treatment of the supply has changed due to a change in the nature of the supply.',
    'DL8.61.1.C': 'If the previously agreed consideration for the supply was altered for any reason (i.e. bad debt relief).',
    'DL8.61.1.D': 'If the recipient of goods or recipient of services returned them to the registrant in full or in part and the Consideration was returned in full or in part.',
    'DL8.61.1.E': 'If the tax was charged or tax treatment was applied in error.',
    'VD': 'Volume Discount.',
}


def _records(value):
    if not value:
        return []
    try:
        return list(value)
    except TypeError:
        return [value]


def _text(value):
    return str(value or '').strip()


def is_export_country_code(country_code):
    code = _text(country_code).upper()
    return bool(code and code != 'AE')


def _regular_lines(move):
    ac_product_ids = _document_ac_product_ids(move)
    if not ac_product_ids:
        return [
            line for line in _records(getattr(move, 'invoice_line_ids', False))
            if _is_regular_invoice_line(line)
        ]
    return [
        line for line in _records(getattr(move, 'invoice_line_ids', False))
        if _is_regular_invoice_line(line)
        and not (line.product_id and getattr(line.product_id, 'id', None) in ac_product_ids)
    ]


def _document_ac_lines(move):
    ac_product_ids = _document_ac_product_ids(move)
    if not ac_product_ids:
        return [
            line for line in _records(getattr(move, 'invoice_line_ids', False))
            if getattr(line, 'orchida_is_document_ac', False)
        ]
    return [
        line for line in _records(getattr(move, 'invoice_line_ids', False))
        if getattr(line, 'orchida_is_document_ac', False)
        or (line.product_id and getattr(line.product_id, 'id', None) in ac_product_ids)
    ]


def _buyer_tax_id(move):
    method = getattr(move, '_orchida_get_buyer_tax_id', None)
    if method:
        return _text(method())
    partner = getattr(move, 'partner_id', False)
    vat = _text(getattr(partner, 'vat', False))
    return vat or _text(getattr(partner, 'trn_tin', False))


def _buyer_endpoint_id(move):
    method = getattr(move, '_orchida_get_buyer_endpoint_id', None)
    if method:
        return _text(method())
    return _text(getattr(getattr(move, 'partner_id', False), 'buyer_endpoint_id', False))


def _buyer_scheme_id(move):
    method = getattr(move, '_orchida_get_buyer_scheme_id', None)
    if method:
        return _text(method())
    return _text(getattr(getattr(move, 'partner_id', False), 'cfg_buyer_scheme_id', False))


def _tax_category(tax):
    return _text(getattr(tax, 'orchida_tax_category', False)).upper()


def _amount_is(value, expected, rounding=0.01):
    return abs(float(value or 0.0) - expected) <= max(rounding / 2.0, 0.000001)


def _currency_rounding(move):
    return float(getattr(getattr(move, 'currency_id', False), 'rounding', 0.01) or 0.01)


def _validate_tax(tax, line_name, errors):
    category = _tax_category(tax)
    prefix = f"Line '{line_name}'"
    if not category:
        errors.append(f"{prefix}: Tax '{getattr(tax, 'name', '')}' has no Orchida tax category")
        return category
    if category not in SUPPORTED_TAX_CATEGORIES:
        errors.append(f"{prefix}: Unsupported Orchida tax category '{category}'")
        return category

    amount_type = getattr(tax, 'amount_type', False)
    amount = getattr(tax, 'amount', False)
    if category in {'S', 'Z', 'AE'} and (amount_type != 'percent' or amount is False or amount is None):
        errors.append(f"{prefix}: Tax category '{category}' requires a percentage rate")
    elif category == 'S' and not _amount_is(amount, 5.0):
        errors.append(f"{prefix}: Standard rate tax must be exactly 5.00")
    elif category == 'Z' and not _amount_is(amount, 0.0):
        errors.append(f"{prefix}: Zero-rated tax must be exactly 0")
    elif category == 'E' and not _text(getattr(tax, 'orchida_exemption_code', False)):
        errors.append(f"{prefix}: Exempt tax requires an exemption code")
    elif category == 'N':
        errors.append(f"{prefix}: Tax category 'N' is unsupported")
    return category


def _validate_rcm_line(line, errors):
    product = getattr(line, 'product_id', False)
    name = getattr(line, 'name', '') or getattr(product, 'display_name', '')
    if not product:
        return

    data = resolve_product_identifiers(product, _records(getattr(line, 'tax_ids', False))[0])
    barcode = _text(getattr(product, 'barcode', False))
    standard_id = _text(data.get('StandardID'))
    if barcode and not is_valid_gtin(barcode):
        errors.append(f"Line '{name}': Product barcode must be a valid GTIN-8, GTIN-12, GTIN-13, or GTIN-14")
    elif not standard_id:
        errors.append(f"Line '{name}': RCM requires a StandardID GTIN")
    elif not is_valid_gtin(standard_id):
        errors.append(f"Line '{name}': RCM StandardID must be a valid GTIN")

    if data.get('StandardScheme') != '0160':
        errors.append(f"Line '{name}': RCM StandardScheme must be 0160")

    classification = (data.get('Classification') or [{}])[0]
    nature_code = _text(classification.get('NatureCode'))
    commodity_code = classification.get('CommodityCode')
    if not nature_code:
        errors.append(f"Line '{name}': RCM NatureCode is required")
    if commodity_code not in {'G', 'S', 'B'}:
        errors.append(f"Line '{name}': RCM CommodityCode must be G, S, or B")
    if commodity_code in {'G', 'B'}:
        if not _text(classification.get('ItemCode')):
            errors.append(f"Line '{name}': RCM goods require an HS code")
        elif classification.get('ListID') != 'HS':
            errors.append(f"Line '{name}': RCM HS classification ListID must be HS")
    if commodity_code in {'S', 'B'}:
        service_codes = data.get('ServiceAccountingcode') or []
        if not service_codes or not _text(service_codes[0].get('SacID')):
            errors.append(f"Line '{name}': RCM services require a SAC code")
        elif service_codes[0].get('SacSchemeID') != 'SAC':
            errors.append(f"Line '{name}': RCM SAC scheme must be SAC")


def _validate_rcm_tax_configuration(tax, line_name, errors):
    if getattr(tax, 'amount_type', False) != 'percent':
        errors.append(f"Line '{line_name}': RCM tax must be a percentage tax")
    elif not (
        _amount_is(getattr(tax, 'amount', None), 0.0)
        or _amount_is(getattr(tax, 'amount', None), AE_RCM_RATE)
    ):
        errors.append(f"Line '{line_name}': RCM tax rate must be 0 or 5")


def _validate_rcm_accounting(line, line_name, rounding, errors):
    taxes = _records(getattr(line, 'tax_ids', False))
    if len(taxes) != 1:
        errors.append(f"Line '{line_name}': RCM requires exactly one tax")
        return

    _validate_rcm_tax_configuration(taxes[0], line_name, errors)

    price_subtotal = getattr(line, 'price_subtotal', None)
    price_total = getattr(line, 'price_total', None)
    if price_subtotal is None or price_total is None:
        errors.append(f"Line '{line_name}': RCM tax impact cannot be verified")
    elif not _amount_is(price_total, price_subtotal, rounding):
        errors.append(
            f"Line '{line_name}': Reverse-charge tax must not increase the supplier invoice total"
        )


def _validate_buyer(move, regular_lines, errors):
    partner = getattr(move, 'partner_id', False)
    if not partner:
        return

    name = _text(getattr(partner, 'name', False))
    country = _text(getattr(getattr(partner, 'country_id', False), 'code', False)).upper()
    endpoint = _buyer_endpoint_id(move)
    scheme = _buyer_scheme_id(move)
    state = getattr(partner, 'state_id', False)
    if not name:
        errors.append('Buyer name is required on customer')
    if not country:
        errors.append('Buyer country is required on customer')
    if not endpoint:
        errors.append('Endpoint ID is required on customer')
    if not scheme:
        errors.append('Buyer endpoint scheme is required on customer')
    if not _text(getattr(partner, 'street', False)):
        errors.append('Buyer street (Address line 1) is required on customer')
    if not _text(getattr(partner, 'city', False)):
        errors.append('Buyer city is required on customer')
    if not state:
        errors.append('Buyer state/emirate (country subdivision) is required on customer')
    elif country == 'AE' and _buyer_country_subentity(partner) not in AE_SUBENTITIES:
        errors.append(
            'Buyer emirate must map to one of: AUH, DXB, SHJ, UAQ, FUJ, AJM, RAK '
            f"(current state code/name sent as '{_buyer_country_subentity(partner)}')"
        )

    buyer_tax_id = _buyer_tax_id(move)
    is_export = bool(getattr(move, 'orchida_is_export', False))
    endpoint_is_uae_tin = bool(re.fullmatch(r'[19]\d{9}', endpoint))
    if scheme == '0235' and not endpoint_is_uae_tin and not is_export and not (
        _text(getattr(partner, 'ref', False)) or buyer_tax_id
    ):
        errors.append('Buyer ID or buyer VAT ID is required for scheme 0235')

    legal_id = _text(getattr(partner, 'company_registry', False))
    # IBR-149-AE: legal registration identifier required when the buyer
    # endpoint uses scheme 0235, the endpoint does not start with 1 or 9,
    # and the buyer has no VAT/TIN identifier (PartyTaxScheme/CompanyID).
    if (
        scheme == '0235'
        and not re.match(r'^[19]', endpoint or '')
        and not buyer_tax_id
        and not legal_id
    ):
        errors.append('Buyer legal ID is required for scheme 0235 when endpoint is not a UAE TIN')
    agency_id = _text(getattr(partner, 'cfg_buyer_agency_id', False))
    agency_name = _text(getattr(partner, 'cfg_buyer_agency_name', False))
    if legal_id and not agency_id:
        errors.append('Buyer agency ID is required when buyer legal ID is provided')
    if agency_id == 'TL' and not agency_name:
        errors.append('Buyer agency name is required when buyer agency ID is TL')

    if getattr(move, 'orchida_document_scope', 'standard') == 'out_of_scope' and not legal_id:
        errors.append('Out-of-scope documents require buyer legal ID')

    if any(_tax_category(tax) == 'AE' for line in regular_lines for tax in _records(getattr(line, 'tax_ids', False))):
        if not buyer_tax_id:
            errors.append('RCM lines require buyer VAT ID')


def _validate_delivery(move, errors):
    is_export = bool(getattr(move, 'orchida_is_export', False))
    is_ecommerce = bool(getattr(move, 'orchida_is_ecommerce', False))
    if not (is_export or is_ecommerce):
        return

    shipping = getattr(move, 'partner_shipping_id', False)
    if not shipping:
        errors.append('Export and e-commerce documents require a delivery address')
        return
    for field, label in (
        ('street', 'delivery street'),
        ('city', 'delivery city'),
        ('state_id', 'delivery state/country subdivision'),
        ('country_id', 'delivery country'),
    ):
        if not getattr(shipping, field, False):
            errors.append(f'{label.capitalize()} is required for delivery')

    country = _text(getattr(getattr(shipping, 'country_id', False), 'code', False)).upper()
    if is_export and country == 'AE':
        errors.append('Export delivery country must not be AE')


def _validate_payment(move, errors):
    if getattr(move, 'move_type', False) == 'out_refund':
        return
    override = getattr(getattr(move, 'partner_id', False), 'orchida_payment_instruction', False) or False
    if override not in {False, '', 'cash', 'credit_transfer'}:
        errors.append(f"Unsupported e-invoice payment instruction override '{override}'")
        return
    if override == 'cash':
        return
    bank = getattr(move, 'partner_bank_id', False)
    if not bank:
        errors.append('Bank transfer payment requires an invoice receiving bank account')
    elif not _text(getattr(bank, 'acc_number', False)):
        errors.append('Invoice receiving bank account must have an account number')


def _validate_credit_note(move, errors):
    if getattr(move, 'move_type', False) != 'out_refund':
        return
    reason = _text(getattr(move, 'orchida_credit_note_reason_code', False))
    if reason not in CREDIT_NOTE_REASONS:
        errors.append('Customer credit notes require an approved credit-note reason code')
        return
    original = getattr(move, 'orchida_original_invoice_id', False) or getattr(move, 'reversed_entry_id', False)
    if reason != 'VD' and not original:
        errors.append('Credit notes require an original invoice unless the reason is VD')
    if reason != 'VD' and original:
        if (
            getattr(original, 'move_type', 'out_invoice') != 'out_invoice'
            or getattr(original, 'state', 'posted') != 'posted'
            or getattr(original, 'company_id', move.company_id) != move.company_id
            or getattr(original, 'partner_id', move.partner_id) != move.partner_id
        ):
            errors.append('Original invoice must be a posted customer invoice for the same customer and company')
        if not _text(getattr(original, 'name', False)) or getattr(original, 'name', False) == '/':
            errors.append('Credit-note BillingRef requires the original invoice number')
        if not getattr(original, 'invoice_date', False):
            errors.append('Credit-note BillingRef requires the original invoice issue date')


def _validate_document_lines(move, regular_lines, ac_lines, errors):
    if not regular_lines:
        errors.append('Invoice has no regular product lines')
    uom_lines = []
    for line in regular_lines:
        product = getattr(line, 'product_id', False)
        line_name = _text(getattr(line, 'name', False)) or 'Unnamed line'
        if not product:
            errors.append(f"Line '{line_name}': Product is required")
        if not _text(getattr(line, 'name', False)):
            errors.append(f"Line '{line_name}': Description is required")
        if getattr(line, 'quantity', False) in (False, None, 0):
            errors.append(f"Line '{line_name}': Quantity is required")
        if product and not _text(getattr(product, 'default_code', False)):
            errors.append(f"Line '{line_name}': Product default_code is required")
        if not getattr(line, 'product_uom_id', False):
            errors.append(f"Line '{line_name}': Unit of measure is required")
        else:
            uom_lines.append(line)

        taxes = _records(getattr(line, 'tax_ids', False))
        if not taxes:
            errors.append(f"Line '{line_name}': At least one tax is required")
            continue
        categories = {_tax_category(tax) for tax in taxes if _tax_category(tax)}
        if len(categories) > 1:
            errors.append(f"Line '{line_name}': Multiple Orchida tax categories are not allowed")
        for tax in taxes:
            category = _validate_tax(tax, line_name, errors)
            if category == 'AE':
                _validate_rcm_line(line, errors)
        if 'AE' in categories:
            _validate_rcm_accounting(line, line_name, _currency_rounding(move), errors)

    if getattr(move, 'company_id', False):
        _, missing_uom = _build_uom_code_map(move, move.company_id, lines=uom_lines)
        if missing_uom:
            errors.append('Missing UnitCode mapping for UoM: ' + ', '.join(missing_uom))

    rounding = _currency_rounding(move)
    for line in ac_lines:
        line_name = _text(getattr(line, 'name', False)) or 'Unnamed line'
        legacy = getattr(line, 'orchida_is_document_ac', False)
        if legacy:
            if getattr(line, 'orchida_ac_indicator', False) not in {'allowance', 'charge'}:
                errors.append(f"Line '{line_name}': Document AC type is required")
            amount = float(getattr(line, 'orchida_ac_amount', 0.0) or 0.0)
        else:
            amount = abs(float(getattr(line, 'price_subtotal', 0.0) or 0.0))
        if amount <= 0:
            errors.append(f"Line '{line_name}': Document AC amount must be > 0")
        if legacy:
            reason_code = getattr(line, 'orchida_ac_reason_code', False)
            reason = getattr(line, 'orchida_ac_reason', False)
        else:
            template = getattr(getattr(line, 'product_id', False), 'product_tmpl_id', False)
            reason_code = getattr(template, 'orchida_doc_ac_reason_code', False) if template else False
            reason = False
        if not _text(reason_code) and not _text(reason):
            errors.append(f"Line '{line_name}': Document AC requires Reason Code or Reason")
        if legacy and not _amount_is(amount, abs(float(getattr(line, 'price_subtotal', 0.0) or 0.0)), rounding):
            errors.append(f"Line '{line_name}': Document AC amount must equal the accounting line subtotal")
        taxes = _records(getattr(line, 'tax_ids', False))
        if not taxes:
            errors.append(f"Line '{line_name}': Document AC requires at least one tax")
        for tax in taxes:
            _validate_tax(tax, line_name, errors)


def _validate_currency(move, errors):
    currency = getattr(move, 'currency_id', False)
    if not currency:
        errors.append('Invoice currency is required')
        return
    if _text(getattr(currency, 'name', False)).upper() == 'AED':
        return
    try:
        aed = _get_aed_currency(move)
    except (AttributeError, KeyError, TypeError):
        aed = False
    if not aed:
        errors.append('AED currency is required to calculate the invoice currency rate')
        return
    try:
        rate = currency._get_conversion_rate(currency, aed, move.company_id, move.invoice_date)
    except (AttributeError, TypeError, ValueError):
        rate = 0
    if not rate or rate <= 0:
        errors.append('Invoice currency conversion rate to AED must be positive')


def validate_orchida_credentials(company):
    errors = []
    if not company:
        return ['Invoice company is missing']
    base_url = _text(getattr(company, 'orchida_base_url', False))
    if not base_url:
        errors.append('Company Orchida Base URL is empty')
    elif not (base_url.startswith('http://') or base_url.startswith('https://')):
        errors.append('Company Orchida Base URL must start with http:// or https://')
    if not _text(getattr(company, 'api_token', False)):
        errors.append('Company API token is empty')
    if not _text(getattr(company, 'companyid', False)):
        errors.append('Company ID is empty')
    return errors


def validate_invoice_document_for_orchida(move):
    errors = []
    company = getattr(move, 'company_id', False)
    if not company:
        errors.append('Invoice company is missing')

    if not getattr(move, 'partner_id', False):
        errors.append('Invoice customer is missing')
    if not getattr(move, 'invoice_date', False):
        errors.append('Invoice date is required')
    if not getattr(move, 'currency_id', False):
        errors.append('Invoice currency is required')
    else:
        _validate_currency(move, errors)
    if getattr(move, 'state', 'draft') == 'posted' and _text(getattr(move, 'name', False)) in {'', '/'}:
        errors.append('Assigned invoice number is required before Orchida submission')

    scope = getattr(move, 'orchida_document_scope', 'standard') or 'standard'
    if scope not in {'standard', 'out_of_scope'}:
        errors.append("Document scope must be 'standard' or 'out_of_scope'")
    if getattr(move, 'orchida_is_free_trade_zone', False) and not _text(getattr(move, 'orchida_beneficiary_id', False)):
        errors.append('Free Trade Zone documents require a beneficiary ID')

    regular_lines = _regular_lines(move)
    ac_lines = _document_ac_lines(move)
    _validate_document_lines(move, regular_lines, ac_lines, errors)
    _validate_buyer(move, regular_lines, errors)
    _validate_delivery(move, errors)
    _validate_payment(move, errors)
    _validate_credit_note(move, errors)

    categories = {
        _tax_category(tax)
        for line in regular_lines + ac_lines
        for tax in _records(getattr(line, 'tax_ids', False))
        if _tax_category(tax)
    }
    if scope == 'out_of_scope':
        unsupported = sorted(categories - OUT_OF_SCOPE_TAX_CATEGORIES)
        if unsupported:
            errors.append('Out-of-scope documents permit only E, O, and Z tax categories')
    elif categories and categories <= {'E', 'O'}:
        errors.append(
            'Documents with only Exempt (E) and/or Out-of-scope (O) tax categories '
            'must be marked as out-of-scope documents (type io/co)'
        )

    return errors


def validate_invoice_for_orchida(move):
    company = getattr(move, 'company_id', False)
    credential_errors = validate_orchida_credentials(company) if company else []
    return credential_errors + validate_invoice_document_for_orchida(move)
