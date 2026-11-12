# models/orchida_purchase_invoice.py
from odoo import models, fields
import base64
import zlib
import xml.etree.ElementTree as ET

class OrchidaPurchaseInvoice(models.Model):
    _name = 'orchida.purchase.invoice'
    _description = 'Orchida AP Invoices'
    _rec_name = 'invoice_number'

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )

    invoice_number = fields.Char(index=True)
    status = fields.Selection([
        ('pending', 'pending'),
        ('valid', 'valid'),
        ('invalid', 'invalid'),
    ], string="Tax Status", default='pending')
    raw_response = fields.Text()

    # extracted data
    issue_date = fields.Date()
    currency = fields.Char()
    supplier_name = fields.Char()
    total_amount = fields.Float()
    invoice_xml = fields.Text()
    vendor_bill_id = fields.Many2one('account.move', readonly=True, copy=False)
    import_error = fields.Text(readonly=True, copy=False)

    def action_view_pdf(self):
        return self.env.ref(
            'orchida_uae_e_invoicing.report_orchida_invoice_pdf'
        ).report_action(self)


    def _decode_invoice(self, data):

        decoded = base64.b64decode(data)

        try:
            xml = zlib.decompress(decoded).decode()
        except:
            xml = zlib.decompress(decoded, -zlib.MAX_WBITS).decode()

        return xml

    def _parse_xml(self, xml):

        ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        }

        root = ET.fromstring(xml)

        invoice_number = root.find("cbc:ID", ns).text
        issue_date = root.find("cbc:IssueDate", ns).text
        currency = root.find("cbc:DocumentCurrencyCode", ns).text

        supplier = root.find(
            "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name",
            ns
        )

        supplier_name = supplier.text if supplier is not None else ""

        total = root.find("cac:LegalMonetaryTotal/cbc:PayableAmount", ns)

        total_amount = float(total.text) if total is not None else 0

        return {
            "invoice_number": invoice_number,
            "issue_date": issue_date,
            "currency": currency,
            "supplier_name": supplier_name,
            "total_amount": total_amount,
        }

    def action_view_ubl_pdf(self):

        parsed = self._parse_xml_ubl_pdf(self.invoice_xml)
        print(parsed)

        return self.env.ref(
            'orchida_uae_e_invoicing.report_orchida_invoice_ubl_pdf'
        ).report_action(self)

    def _find_or_create_supplier(self, parsed):
        supplier = parsed.get('supplier', {})
        supplier_name = (supplier.get('name') or self.supplier_name or 'Orchida Supplier').strip()
        supplier_vat = (supplier.get('vat') or '').strip()
        Partner = self.env['res.partner'].sudo()

        partner = False
        if supplier_vat:
            partner = Partner.search([
                '|',
                ('vat', '=', supplier_vat),
                ('trn_tin', '=', supplier_vat),
            ], limit=1)
        if not partner and supplier_name:
            partner = Partner.search([('name', '=', supplier_name)], limit=1)
        if partner:
            if not partner.supplier_rank:
                partner.sudo().write({'supplier_rank': 1})
            return partner

        vals = {
            'name': supplier_name,
            'supplier_rank': 1,
            'company_type': 'company',
        }
        if supplier_vat:
            vals['vat'] = supplier_vat
            vals['trn_tin'] = supplier_vat
        return Partner.create(vals)

    def _get_or_create_import_product(self, company, line_name):
        Product = self.env['product.product'].sudo().with_company(company)
        name = (line_name or '').strip()
        if name:
            product = Product.search([
                ('name', '=', name),
                ('company_id', 'in', [False, company.id]),
            ], limit=1)
            if product:
                return product

        fallback_name = 'Orchida Imported Purchase Line'
        product = Product.search([
            ('name', '=', fallback_name),
            ('company_id', 'in', [False, company.id]),
        ], limit=1)
        if product:
            return product

        return Product.create({
            'name': fallback_name,
            'type': 'service',
            'purchase_ok': True,
            'sale_ok': False,
            'company_id': company.id,
        })

    def _prepare_vendor_bill_line_vals(self, company, parsed_line):
        product = self._get_or_create_import_product(company, parsed_line.get('name'))
        quantity = parsed_line.get('qty') or 1.0
        if quantity <= 0:
            quantity = 1.0
        price = parsed_line.get('price') or parsed_line.get('total') or 0.0
        name_parts = [parsed_line.get('name') or product.display_name, parsed_line.get('description') or '']
        line_name = ' - '.join([part for part in name_parts if part])
        return {
            'product_id': product.id,
            'name': line_name,
            'quantity': quantity,
            'price_unit': price,
            'tax_ids': [(6, 0, [])],
        }

    def _prepare_vendor_bill_vals(self, parsed):
        self.ensure_one()
        company = self.company_id
        supplier = self._find_or_create_supplier(parsed)
        invoice_number = self.invoice_number or parsed.get('invoice_number')
        due_date = parsed.get('due_date') or False
        currency_code = parsed.get('currency') or self.currency or company.currency_id.name
        currency = self.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1) or company.currency_id
        line_values = [
            (0, 0, self._prepare_vendor_bill_line_vals(company, parsed_line))
            for parsed_line in parsed.get('lines', [])
        ]
        if not line_values:
            line_values = [
                (0, 0, self._prepare_vendor_bill_line_vals(company, {
                    'name': self.supplier_name or invoice_number or 'Imported line',
                    'description': '',
                    'qty': 1.0,
                    'price': self.total_amount or 0.0,
                }))
            ]

        return {
            'move_type': 'in_invoice',
            'company_id': company.id,
            'partner_id': supplier.id,
            'invoice_date': parsed.get('issue_date') or self.issue_date or fields.Date.today(),
            'invoice_date_due': due_date,
            'currency_id': currency.id,
            'ref': invoice_number,
            'payment_reference': invoice_number,
            'invoice_line_ids': line_values,
        }

    def _find_existing_vendor_bill(self, invoice_number):
        self.ensure_one()
        if self.vendor_bill_id:
            return self.vendor_bill_id
        if not invoice_number:
            return self.env['account.move']
        return self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('move_type', '=', 'in_invoice'),
            '|',
            ('ref', '=', invoice_number),
            ('payment_reference', '=', invoice_number),
        ], limit=1)

    def _create_vendor_bill_from_orchida(self):
        self.ensure_one()
        invoice_number = self.invoice_number
        existing = self._find_existing_vendor_bill(invoice_number)
        if existing:
            self.sudo().write({'vendor_bill_id': existing.id, 'import_error': False})
            return existing

        try:
            parsed = self._parse_xml_ubl_pdf(self.invoice_xml)
            vals = self._prepare_vendor_bill_vals(parsed)
            bill = self.env['account.move'].sudo().with_company(self.company_id).create(vals)
            self.sudo().write({'vendor_bill_id': bill.id, 'import_error': False})
            return bill
        except Exception as exc:
            self.sudo().write({'import_error': str(exc)})
            raise

    def _parse_xml_ubl_pdf(self, xml):

        ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        }

        root = ET.fromstring(xml)

        def get(node, path):
            el = node.find(path, ns)
            return el.text if el is not None else ""

        # ------------------------
        # Invoice Info
        # ------------------------

        invoice_number = get(root, "cbc:ID")
        uuid = get(root, "cbc:UUID")
        issue_date = get(root, "cbc:IssueDate")
        issue_time = get(root, "cbc:IssueTime")
        due_date = get(root, "cbc:DueDate")
        currency = get(root, "cbc:DocumentCurrencyCode")

        # ------------------------
        # Supplier
        # ------------------------

        supplier = root.find("cac:AccountingSupplierParty/cac:Party", ns)

        supplier_name = get(supplier, "cac:PartyName/cbc:Name")
        supplier_vat = get(supplier, "cac:PartyTaxScheme/cbc:CompanyID")

        supplier_city = get(supplier, "cac:PostalAddress/cbc:CityName")
        supplier_country = get(
            supplier,
            "cac:PostalAddress/cac:Country/cbc:IdentificationCode"
        )

        # ------------------------
        # Customer
        # ------------------------

        customer = root.find("cac:AccountingCustomerParty/cac:Party", ns)

        customer_name = get(customer, "cac:PartyName/cbc:Name")
        customer_vat = get(customer, "cac:PartyTaxScheme/cbc:CompanyID")

        customer_city = get(customer, "cac:PostalAddress/cbc:CityName")
        customer_country = get(
            customer,
            "cac:PostalAddress/cac:Country/cbc:IdentificationCode"
        )

        # ------------------------
        # Totals
        # ------------------------

        total_section = root.find("cac:LegalMonetaryTotal", ns)

        subtotal = float(get(total_section, "cbc:LineExtensionAmount") or 0)
        tax_exclusive = float(get(total_section, "cbc:TaxExclusiveAmount") or 0)
        tax_inclusive = float(get(total_section, "cbc:TaxInclusiveAmount") or 0)
        payable = float(get(total_section, "cbc:PayableAmount") or 0)

        # ------------------------
        # Tax
        # ------------------------

        tax_total = root.find("cac:TaxTotal", ns)

        tax_amount = float(get(tax_total, "cbc:TaxAmount") or 0)

        tax_percent = get(
            tax_total,
            "cac:TaxSubtotal/cac:TaxCategory/cbc:Percent"
        )

        # ------------------------
        # Payment
        # ------------------------

        payment = root.find("cac:PaymentMeans", ns)

        payment_code = get(payment, "cbc:PaymentMeansCode")

        card_number = get(payment, "cac:CardAccount/cbc:PrimaryAccountNumberID")
        card_network = get(payment, "cac:CardAccount/cbc:NetworkID")

        # ------------------------
        # Invoice Lines
        # ------------------------

        lines = []

        for line in root.findall("cac:InvoiceLine", ns):
            name = get(line, "cac:Item/cbc:Name")
            description = get(line, "cac:Item/cbc:Description")

            qty = float(get(line, "cbc:InvoicedQuantity") or 0)

            price = float(get(line, "cac:Price/cbc:PriceAmount") or 0)

            line_total = float(get(line, "cbc:LineExtensionAmount") or 0)

            line_tax = float(get(line, "cac:TaxTotal/cbc:TaxAmount") or 0)

            tax_percent = get(
                line,
                "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent"
            )

            # Detect allowance / charge from line-level AllowanceCharge
            is_allowance = False
            is_charge = False
            ac = line.find("cac:AllowanceCharge", ns)
            if ac is not None:
                indicator = get(ac, "cbc:ChargeIndicator").lower()
                if indicator == "false":
                    is_allowance = True
                elif indicator == "true":
                    is_charge = True

            lines.append({
                "name": name,
                "description": description,
                "qty": qty,
                "price": price,
                "tax": line_tax,
                "tax_percent": tax_percent,
                "total": line_total,
                "is_allowance": is_allowance,
                "is_charge": is_charge,
            })

        # ------------------------
        # Final Dictionary
        # ------------------------

        return {
            "invoice_number": invoice_number,
            "uuid": uuid,
            "issue_date": issue_date,
            "issue_time": issue_time,
            "due_date": due_date,
            "currency": currency,

            "supplier": {
                "name": supplier_name,
                "vat": supplier_vat,
                "city": supplier_city,
                "country": supplier_country,
            },

            "customer": {
                "name": customer_name,
                "vat": customer_vat,
                "city": customer_city,
                "country": customer_country,
            },

            "totals": {
                "subtotal": subtotal,
                "tax_exclusive": tax_exclusive,
                "tax_inclusive": tax_inclusive,
                "payable": payable,
            },

            "tax": {
                "amount": tax_amount,
                "percent": tax_percent
            },

            "payment": {
                "method": payment_code,
                "card": card_number,
                "network": card_network
            },

            "lines": lines
        }
