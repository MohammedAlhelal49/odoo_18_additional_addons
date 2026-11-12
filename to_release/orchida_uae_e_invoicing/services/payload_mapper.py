import re


# PINT AE IBT-054 / ibr-128-ae: CountrySubentity must be one of these when country is AE.
_AE_SUBENTITY_BY_CODE = {
    'AZ': 'AUH',
    'AUH': 'AUH',
    'DU': 'DXB',
    'DXB': 'DXB',
    'SH': 'SHJ',
    'SHJ': 'SHJ',
    'UQ': 'UAQ',
    'UAQ': 'UAQ',
    'FU': 'FUJ',
    'FUJ': 'FUJ',
    'AJ': 'AJM',
    'AJM': 'AJM',
    'RK': 'RAK',
    'RAK': 'RAK',
}
_AE_SUBENTITY_BY_NAME = {
    'abu dhabi': 'AUH',
    'dubai': 'DXB',
    'sharjah': 'SHJ',
    'umm al quwain': 'UAQ',
    'umm al-quwain': 'UAQ',
    'fujairah': 'FUJ',
    'ajman': 'AJM',
    'ras al khaimah': 'RAK',
    'ras al-khaimah': 'RAK',
}
AE_RCM_RATE = 5.0

from .product_identifier_resolver import resolve_product_identifiers
from ..constants import UNCL5189_ALLOWANCE_CODES, UNCL7161_CHARGE_CODES


_AC_REASON_TEXTS = {
    code: label.split(' - ', 1)[1]
    for code, label in UNCL5189_ALLOWANCE_CODES + UNCL7161_CHARGE_CODES
}


def _buyer_country_subentity(partner):
    """Return PINT-compliant buyer CountrySubentity (IBT-054)."""
    state = partner.state_id
    country_code = (partner.country_id.code or '').upper()
    if not state:
        return ''

    raw_code = (state.code or '').strip().upper()
    if raw_code.startswith('AE-'):
        raw_code = raw_code[3:]

    if country_code == 'AE' or (state.country_id and (state.country_id.code or '').upper() == 'AE'):
        if raw_code in _AE_SUBENTITY_BY_CODE:
            return _AE_SUBENTITY_BY_CODE[raw_code]
        name_key = (state.name or '').strip().lower()
        if name_key in _AE_SUBENTITY_BY_NAME:
            return _AE_SUBENTITY_BY_NAME[name_key]
        if raw_code in ('AUH', 'DXB', 'SHJ', 'UAQ', 'FUJ', 'AJM', 'RAK'):
            return raw_code

    return raw_code or (state.name or '')


def _is_regular_invoice_line(line):
    display_type = getattr(line, 'display_type', False)
    return (
        not getattr(line, 'orchida_is_document_ac', False)
        and (not display_type or display_type == 'product')
    )


def _build_uom_code_map(move, company, lines=None):
    lines = lines if lines is not None else move.invoice_line_ids
    uom_ids = [line.product_uom_id.id for line in lines if line.product_uom_id]
    if not uom_ids:
        return {}, []

    records = move.env['orchida.uom.api.map'].search(
        [('company_id', '=', company.id), ('uom_id', 'in', uom_ids), ('active', '=', True)]
    )
    code_map = {record.uom_id.id: record.unit_code_id.code for record in records if record.unit_code_id}
    missing = sorted({
        (line.product_uom_id.name or 'Unknown UoM')
        for line in lines
        if line.product_uom_id and line.product_uom_id.id not in code_map
    })
    return code_map, missing


def build_submit_context(company):
    base = (company.orchida_base_url or '').rstrip('/')
    url = f'{base}/InvSubmit'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {company.api_token}',
        'Company-id': company.companyid,
    }
    return url, headers, {'format': 'integrator'}


def _tax_info_from_line(line):
    """Return validated tax data without inventing a category or rate."""
    tax = list(line.tax_ids)[0]
    category = tax.orchida_tax_category
    rate = (
        AE_RCM_RATE
        if category == 'AE'
        else tax.amount if tax.amount_type == 'percent' and category not in {'E', 'O'} else None
    )
    exemption_code = tax.orchida_exemption_code if category == 'E' else None
    exemption_desc = None
    if exemption_code and hasattr(tax, 'fields_get'):
        try:
            selection = tax.fields_get(['orchida_exemption_code'])['orchida_exemption_code']['selection']
            exemption_desc = dict(selection).get(exemption_code, '')
        except (KeyError, TypeError):
            exemption_desc = None
    return category, rate, exemption_code, exemption_desc


def _build_line_tax_payload(category, rate, exemption_code, exemption_desc):
    tax_payload = {'lineVATSubtype': category}
    if rate is not None:
        tax_payload['lineVATRate'] = rate
    if category == 'E' and exemption_code:
        tax_payload['lineVATReason'] = exemption_code
        if exemption_desc:
            tax_payload['lineVATReasonDesc'] = exemption_desc
    return tax_payload


def _build_line_payload(line, uom_code_map):
    category, rate, exemption_code, exemption_desc = _tax_info_from_line(line)
    product = line.product_id
    line_payload = {
        'Description': line.name,
        'Name': product.name,
        'Quantity': line.quantity,
        'UnitCode': uom_code_map[line.product_uom_id.id],
        'UnitValue': line.price_unit,
        **_build_line_tax_payload(category, rate, exemption_code, exemption_desc),
    }
    if product.default_code:
        line_payload['itemCode'] = product.default_code
    if line.orchida_buyer_item_code:
        line_payload['buyerItemCode'] = line.orchida_buyer_item_code
    if line.orchida_line_note:
        line_payload['Note'] = line.orchida_line_note
    if line.discount:
        line_payload['itemDiscountAmount'] = line.price_unit * line.discount / 100.0
    if category == 'AE':
        line_payload.update(resolve_product_identifiers(product, list(line.tax_ids)[0]))
    return line_payload


def _build_ac_object(indicator, amount, tax, reason_code, reason):
    category = tax.orchida_tax_category
    if category in {'Z', 'E', 'AE'}:
        rate = 0
    elif category == 'O':
        rate = None
    else:
        rate = tax.amount if tax.amount_type == 'percent' else None
    ac = {
        'Indicator': 'true' if indicator == 'charge' else 'false',
        'Amount': amount,
        'TaxCatID': category,
    }
    if reason_code:
        ac['ReasonCode'] = reason_code
    if not reason:
        reason = _AC_REASON_TEXTS.get(reason_code, '')
    if reason:
        ac['Reason'] = reason
    if rate is not None:
        ac['TaxPercent'] = rate
    if category == 'E' and tax.orchida_exemption_code:
        ac['ExemptionCode'] = tax.orchida_exemption_code
        exemption_desc = None
        if hasattr(tax, 'fields_get'):
            try:
                selection = tax.fields_get(['orchida_exemption_code'])['orchida_exemption_code']['selection']
                exemption_desc = dict(selection).get(tax.orchida_exemption_code, '')
            except (KeyError, TypeError):
                exemption_desc = None
        if exemption_desc:
            ac['ExemptionReason'] = exemption_desc
    return ac


def _build_ac_payload(line):
    """Legacy single-category AC object from a flagged AC line."""
    return _build_ac_object(
        line.orchida_ac_indicator,
        line.orchida_ac_amount,
        list(line.tax_ids)[0],
        line.orchida_ac_reason_code,
        line.orchida_ac_reason,
    )


def _document_ac_product_ids(move):
    company = getattr(move, 'company_id', False)
    if not company:
        return set()
    products = (
        getattr(company, 'orchida_doc_allowance_product_id', False),
        getattr(company, 'orchida_doc_charge_product_id', False),
    )
    ids = set()
    for product in products:
        if not product:
            continue
        ids.add(getattr(product, 'id', product))
    return ids


def _build_ac_payloads(regular_lines, ac_lines):
    """Split each document AC line across the VAT categories present on the invoice."""
    if not ac_lines:
        return []
    category_totals = {}
    for line in regular_lines:
        tax = list(line.tax_ids)[0]
        category = tax.orchida_tax_category
        entry = category_totals.setdefault(category, {'subtotal': 0.0, 'tax': tax})
        entry['subtotal'] += float(line.price_subtotal or 0.0)
    total = sum(entry['subtotal'] for entry in category_totals.values())
    if not total:
        return []

    payloads = []
    for line, indicator, amount in ac_lines:
        if getattr(line, 'orchida_is_document_ac', False):
            reason_code = line.orchida_ac_reason_code
            reason = line.orchida_ac_reason
        else:
            template = getattr(getattr(line, 'product_id', False), 'product_tmpl_id', False)
            reason_code = getattr(template, 'orchida_doc_ac_reason_code', False) if template else False
            reason = False
        categories = sorted(category_totals)
        allocated = 0.0
        last_idx = len(categories) - 1
        for idx, category in enumerate(categories):
            entry = category_totals[category]
            if idx == last_idx:
                share = round(amount - allocated, 2)
            else:
                share = round(amount * entry['subtotal'] / total, 2)
                allocated += share
            payloads.append(_build_ac_object(indicator, share, entry['tax'], reason_code, reason))
    return payloads


def _buyer_value(move, method_name, fallback):
    method = getattr(move, method_name, None)
    if method:
        return method() or ''
    return fallback or ''


def _payment_account_scheme(account):
    account = re.sub(r'\s+', '', account or '').upper()
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{10,30}', account):
        return 'BBAN'

    rearranged = account[4:] + account[:4]
    numeric = ''.join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    return 'IBAN' if int(numeric) % 97 == 1 else 'BBAN'


def _payment_means(move):
    override = getattr(move.partner_id, 'orchida_payment_instruction', False) or False
    if override == 'cash':
        return {'Name': 'Cash', 'Code': '10'}

    bank = move.partner_bank_id
    payment = {'Name': 'Credit transfer', 'Code': '30'}
    if bank:
        payment.update({
            'account': bank.acc_number,
            'accountSchemeID': _payment_account_scheme(bank.acc_number),
            'accountName': bank.acc_holder_name or (bank.partner_id.name if bank.partner_id else '') or '',
            'branch': bank.bank_id.bic if bank.bank_id else '',
        })
    return payment


def _build_delivery(move):
    shipping = move.partner_shipping_id
    if not shipping:
        return None
    country = shipping.country_id.code or ''
    delivery = {
        'streetName': shipping.street or '',
        'additionalStreetName': shipping.street2 or '',
        'cityName': shipping.city or '',
        'postalZone': shipping.zip or '',
        'countrySubentity': _buyer_country_subentity(shipping),
        'country': country,
        'partyName': shipping.name or '',
    }
    return {key: value for key, value in delivery.items() if value}


def _get_aed_currency(move):
    if (move.currency_id.name or '').upper() == 'AED':
        return move.currency_id
    currency_model = move.env['res.currency'].with_context(active_test=False)
    if move.company_id:
        currency_model = currency_model.with_company(move.company_id)
    return currency_model.search([('name', '=', 'AED')], limit=1)


def _document_type(move):
    if move.orchida_document_scope == 'out_of_scope':
        return 'co' if move.move_type == 'out_refund' else 'io'
    return 'c' if move.move_type == 'out_refund' else 'i'


def _build_document_header(move):
    return {
        'internalCode': (move.name or '').replace('/', '-'),
        'type': _document_type(move),
        'dateTimeIssued': move.invoice_date.strftime('%Y-%m-%dT00:00:00'),
        'currency': move.currency_id.name,
        'total': move.amount_total,
        'rounding': 0,
    }


def _add_currency_rate(move, payload, company):
    if (move.currency_id.name or '').upper() == 'AED':
        return
    aed_currency = _get_aed_currency(move)
    rate = move.currency_id._get_conversion_rate(
        move.currency_id,
        aed_currency,
        company,
        move.invoice_date,
    )
    payload['currRate'] = round(rate, 6)


def _add_document_references(move, payload):
    if move.narration:
        payload['Note'] = move.narration
    if move.invoice_date_due:
        payload['DueDate'] = move.invoice_date_due.strftime('%Y-%m-%d')
    if move.ref:
        payload['buyerReference'] = move.ref
    if move.invoice_origin:
        payload['orderReferenceID'] = move.invoice_origin
        payload['salesOrderID'] = move.invoice_origin
    prepaid = move.amount_total - move.amount_residual
    if prepaid > 0:
        payload['prepaid'] = prepaid


def _add_scenario_payload(move, payload):
    if move.orchida_is_free_trade_zone:
        payload['isFreeTradeZone'] = '1'
        payload['beneficiarID'] = move.orchida_beneficiary_id
    if move.orchida_is_export:
        payload['isExport'] = '1'
    if move.orchida_is_ecommerce:
        payload['isECommerceSupply'] = '1'
    if (move.orchida_is_export or move.orchida_is_ecommerce) and move.partner_shipping_id:
        payload['Delivery'] = _build_delivery(move)
    incoterm = getattr(move, 'invoice_incoterm_id', False)
    if move.orchida_is_export and incoterm:
        payload['DeliveryTerms'] = {'ID': incoterm.code, 'SchemeID': 'Incoterms'}


def _add_credit_note_payload(move, payload):
    if move.move_type != 'out_refund':
        return
    payload['creditNoteReasonCode'] = move.orchida_credit_note_reason_code
    original = getattr(move, 'orchida_original_invoice_id', False) or move.reversed_entry_id
    if move.orchida_credit_note_reason_code != 'VD' and original:
        payload['BillingRef'] = [{
            'ID': (original.name or '').replace('/', '-'),
            'IssueDate': original.invoice_date.strftime('%Y-%m-%d'),
        }]


def _build_buyer_payload(move):
    partner = move.partner_id
    buyer_tax_id = _buyer_value(move, '_orchida_get_buyer_tax_id', (getattr(partner, 'vat', False) or '').strip() or partner.trn_tin)
    buyer = {
        'buyerEndpointID': _buyer_value(move, '_orchida_get_buyer_endpoint_id', partner.buyer_endpoint_id),
        'buyerSchemeID': _buyer_value(move, '_orchida_get_buyer_scheme_id', partner.cfg_buyer_scheme_id),
        'buyerName': partner.name,
        'buyerStreet': ' '.join(value for value in (partner.street, partner.street2) if value),
        'buyerCity': partner.city,
        'buyerSubentity': _buyer_country_subentity(partner),
        'buyerCountry': partner.country_id.code,
        'buyerType': partner.cfg_buyer_tax_scheme,
        'buyerAgencyID': partner.cfg_buyer_agency_id,
        'buyerAgencyName': partner.cfg_buyer_agency_name,
    }
    if buyer_tax_id:
        buyer['buyerTaxID'] = buyer_tax_id
    if partner.ref:
        buyer['buyerId'] = partner.ref
    if partner.company_registry:
        buyer['buyerLegalID'] = partner.company_registry
    return buyer


def build_invoice_payload(move):
    company = move.company_id
    allowance_product = getattr(company, 'orchida_doc_allowance_product_id', False) if company else False
    charge_product = getattr(company, 'orchida_doc_charge_product_id', False) if company else False

    regular_lines = []
    ac_lines = []
    for line in move.invoice_line_ids:
        if line.display_type and line.display_type != 'product':
            continue
        if getattr(line, 'orchida_is_document_ac', False):
            ac_lines.append((line, line.orchida_ac_indicator, line.orchida_ac_amount))
        elif allowance_product and line.product_id == allowance_product:
            ac_lines.append((line, 'allowance', abs(float(line.price_subtotal or 0.0))))
        elif charge_product and line.product_id == charge_product:
            ac_lines.append((line, 'charge', abs(float(line.price_subtotal or 0.0))))
        else:
            regular_lines.append(line)

    uom_code_map, _ = _build_uom_code_map(move, company, lines=regular_lines)
    payload = _build_document_header(move)
    _add_currency_rate(move, payload, company)
    _add_document_references(move, payload)
    _add_scenario_payload(move, payload)
    _add_credit_note_payload(move, payload)
    payload.update(_build_buyer_payload(move))
    if move.move_type != 'out_refund':
        payload['PaymentMeans'] = [_payment_means(move)]
    payload['AllowanceCharge'] = _build_ac_payloads(regular_lines, ac_lines)
    payload['lines'] = [_build_line_payload(line, uom_code_map) for line in regular_lines]
    return payload
