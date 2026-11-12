import logging

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from ..services.invoice_validator import (
    CREDIT_NOTE_REASONS,
    is_export_country_code,
    validate_invoice_document_for_orchida,
    validate_invoice_for_orchida,
)
from ..services.payload_mapper import build_invoice_payload
from ..services.product_identifier_resolver import is_valid_gtin, resolve_product_identifiers
from ..services.submission_client import classify_failure, submit_payload


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    orchida_send_attempt_ids = fields.One2many(
        'api.sent.invoice',
        'move_id',
        string='Orchida Send Attempts',
    )
    orchida_original_invoice_id = fields.Many2one(
        'account.move',
        string='Original Invoice',
        copy=False,
        check_company=True,
    )
    orchida_submission_state = fields.Selection(
        [
            ('not_applicable', 'Not Applicable'),
            ('to_send', 'To Submit'),
            ('failed', 'Action Required'),
            ('unknown', 'Processing'),
            ('valid', 'Valid'),
        ],
        string='E-Invoice Submission',
        compute='_compute_orchida_submission_state',
        store=True,
        index=True,
    )
    orchida_submission_failure_type = fields.Selection(
        [
            ('document', 'Document'),
            ('configuration', 'Configuration'),
            ('technical', 'Technical'),
        ],
        string='E-Invoice Failure Type',
        compute='_compute_orchida_submission_state',
        store=True,
        readonly=True,
    )

    @api.depends(
        'state',
        'move_type',
        'journal_id.orchida_submit_einvoice',
        'orchida_send_attempt_ids.outcome',
        'orchida_send_attempt_ids.success',
        'orchida_send_attempt_ids.sent_date',
        'orchida_send_attempt_ids.failure_type',
    )
    def _compute_orchida_submission_state(self):
        for move in self:
            if not move._orchida_is_enabled():
                move.orchida_submission_state = 'not_applicable'
                move.orchida_submission_failure_type = False
                continue
            if move.state != 'posted' or not move._orchida_should_submit_einvoice():
                move.orchida_submission_state = 'not_applicable'
                move.orchida_submission_failure_type = False
                continue
            attempts = move.orchida_send_attempt_ids.sorted('id')
            if any(attempt.outcome == 'valid' for attempt in attempts):
                move.orchida_submission_state = 'valid'
                move.orchida_submission_failure_type = False
            elif not attempts:
                move.orchida_submission_state = 'to_send'
                move.orchida_submission_failure_type = False
            else:
                latest = attempts[-1]
                move.orchida_submission_state = (
                    'unknown' if latest.outcome == 'unknown' else 'failed'
                )
                move.orchida_submission_failure_type = latest.failure_type

    def _orchida_get_buyer_tax_id(self):
        """Buyer tax ID for e-invoice payload (overridable by bridge modules).

        The standard partner VAT field is the primary source; the custom
        trn_tin field is a fallback for partners that only store it there.
        """
        self.ensure_one()
        partner = self.partner_id
        vat = (getattr(partner, 'vat', False) or "").strip()
        if vat:
            return vat
        return (partner.trn_tin or "").strip() or False

    def _orchida_get_buyer_endpoint_id(self):
        """Buyer Endpoint ID for e-invoice payload (overridable by bridge modules)."""
        self.ensure_one()
        if self.orchida_is_export:
            return '9900000099'
        if self.orchida_document_scope == 'out_of_scope':
            return '9900000098'
        return (self.partner_id.buyer_endpoint_id or "").strip() or False

    def _orchida_get_buyer_scheme_id(self):
        """Buyer Endpoint scheme for e-invoice payload (overridable by bridge modules)."""
        self.ensure_one()
        if self.orchida_is_export or self.orchida_document_scope == 'out_of_scope':
            return '0235'
        return (self.partner_id.cfg_buyer_scheme_id or "").strip() or False

    def _extract_missing_uom_errors(self, errors):
        return [error for error in (errors or []) if error.startswith("Missing UnitCode mapping for UoM:")]

    def _raise_missing_uom_mapping_error(self, errors):
        missing_errors = self._extract_missing_uom_errors(errors)
        if not missing_errors:
            return
        prefix = 'Missing UnitCode mapping for UoM: '
        details = "\n".join(
            f"- {(error[len(prefix):] if error.startswith(prefix) else error).strip()}"
            for error in missing_errors
        )
        raise UserError(_(
            "Cannot submit this invoice because some invoice line UoMs are not mapped to Orchida UnitCodes.\n\n"
            "Missing mappings:\n%(details)s\n\n"
            "Open the mapping screen from this invoice or go to:\n"
            "Orchida-E-invoicing > Orchida-E_invoicing_settings > UoM Unit Code Mapping",
            details=details,
        ))

    amount_orchida_allowance_total = fields.Monetary(
        string='Doc Allowances',
        compute='_compute_orchida_ac_totals',
        store=False,
        help='Sum of document-level allowance lines (absolute value).',
    )
    amount_orchida_charge_total = fields.Monetary(
        string='Doc Charges',
        compute='_compute_orchida_ac_totals',
        store=False,
        help='Sum of document-level charge lines (absolute value).',
    )

    orchida_document_scope = fields.Selection(
        [('standard', 'Standard'), ('out_of_scope', 'Out of scope')],
        string='E-Invoice Document Scope',
        default='standard',
        copy=False,
    )
    orchida_is_free_trade_zone = fields.Boolean(string='Free Trade Zone', copy=False)
    orchida_is_export = fields.Boolean(
        string='Export',
        compute='_compute_orchida_is_export',
        store=True,
        readonly=True,
        copy=False,
    )
    orchida_is_ecommerce = fields.Boolean(string='E-commerce supply', copy=False)
    orchida_beneficiary_id = fields.Char(string='FTZ Beneficiary ID', copy=False)
    orchida_credit_note_reason_code = fields.Selection(
        [(code, f'{code} - {desc}') for code, desc in sorted(CREDIT_NOTE_REASONS.items())],
        string='Credit Note Reason',
        copy=False,
    )
    orchida_payment_code = fields.Selection(
        [
            ('10', '10 - Cash'),
            ('30', '30 - Bank transfer'),
        ],
        string='Resolved E-Invoice Payment',
        compute='_compute_orchida_payment_code',
        readonly=True,
        copy=False,
    )
    orchida_rcm_readiness = fields.Char(
        string='RCM Readiness',
        compute='_compute_orchida_rcm_readiness',
        readonly=True,
    )

    @api.depends('partner_id.country_id.code')
    def _compute_orchida_is_export(self):
        for move in self:
            country = move.partner_id.country_id if move.partner_id else False
            move.orchida_is_export = is_export_country_code(country.code if country else False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reversed_entry_id') and not vals.get('orchida_original_invoice_id'):
                vals['orchida_original_invoice_id'] = vals['reversed_entry_id']
        return super().create(vals_list)

    @api.constrains('orchida_original_invoice_id', 'move_type', 'partner_id', 'company_id')
    def _check_orchida_original_invoice(self):
        for move in self.filtered('orchida_original_invoice_id'):
            if not move._orchida_is_enabled():
                continue
            original = move.orchida_original_invoice_id
            if move.move_type == 'out_refund' and (
                original.move_type != 'out_invoice'
                or original.state != 'posted'
                or original.company_id != move.company_id
                or original.partner_id != move.partner_id
            ):
                raise UserError(_(
                    'Original Invoice must be a posted customer invoice for the same customer and company.'
                ))

    @api.depends('partner_id.orchida_payment_instruction')
    def _compute_orchida_payment_code(self):
        for move in self:
            override = move.partner_id.orchida_payment_instruction if move.partner_id else False
            move.orchida_payment_code = {'cash': '10', 'credit_transfer': '30'}.get(override, False)

    @api.depends(
        'invoice_line_ids.tax_ids.orchida_tax_category',
        'invoice_line_ids.product_id',
        'invoice_line_ids.product_id.barcode',
        'invoice_line_ids.product_id.orchida_standard_id',
        'invoice_line_ids.product_id.product_tmpl_id.orchida_hs_code',
        'invoice_line_ids.product_id.product_tmpl_id.orchida_sac_code',
    )
    def _compute_orchida_rcm_readiness(self):
        for move in self:
            rcm_lines = move.invoice_line_ids.filtered(
                lambda line: any(tax.orchida_tax_category == 'AE' for tax in line.tax_ids)
            )
            if not rcm_lines:
                move.orchida_rcm_readiness = 'Not applicable'
                continue
            missing = []
            for line in rcm_lines:
                product = line.product_id
                tax = line.tax_ids.filtered(lambda item: item.orchida_tax_category == 'AE')[:1]
                data = resolve_product_identifiers(product, tax)
                if not data.get('StandardID') or not is_valid_gtin(data['StandardID']):
                    missing.append('GTIN')
                classification = (data.get('Classification') or [{}])[0]
                if classification.get('CommodityCode') in ('G', 'B') and not classification.get('ItemCode'):
                    missing.append('HS')
                if classification.get('CommodityCode') in ('S', 'B') and not data.get('ServiceAccountingcode'):
                    missing.append('SAC')
                if not classification.get('NatureCode'):
                    missing.append('NatureCode')
            move.orchida_rcm_readiness = 'Ready' if not missing else 'Incomplete: ' + ', '.join(sorted(set(missing)))

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.orchida_is_document_ac', 'invoice_line_ids.orchida_ac_indicator')
    def _compute_orchida_ac_totals(self):
        for move in self:
            allowance = 0.0
            charge = 0.0
            for line in move.invoice_line_ids:
                if line.orchida_is_document_ac:
                    amt = abs(line.price_subtotal)
                    if line.orchida_ac_indicator == 'allowance':
                        allowance += amt
                    elif line.orchida_ac_indicator == 'charge':
                        charge += amt
            move.amount_orchida_allowance_total = allowance
            move.amount_orchida_charge_total = charge

    def _get_or_create_orchida_doc_ac_product(self, indicator):
        self.ensure_one()
        company = self.company_id
        config_field = (
            'orchida_doc_allowance_product_id'
            if indicator == 'allowance'
            else 'orchida_doc_charge_product_id'
        )
        product = company[config_field]
        if product:
            return product

        product_name = _(
            "Document %(type)s",
            type="Allowance" if indicator == 'allowance' else "Charge",
        )
        Product = self.env['product.product'].sudo()
        existing = Product.search([
            ('name', 'in', [product_name, 'Orchida ' + product_name]),
            ('type', '=', 'service'),
            ('company_id', 'in', [False, company.id]),
        ], limit=1)
        if existing:
            company.sudo()[config_field] = existing.id
            return existing

        categ_all = self.env.ref('product.product_category_all', raise_if_not_found=False)
        vals = {
            'name': product_name,
            'type': 'service',
            'sale_ok': True,
            'purchase_ok': False,
            'company_id': company.id,
            'default_code': 'DOC_ALLOW' if indicator == 'allowance' else 'DOC_CHARGE',
            'description_sale': _(
                "Document-level %(type)s used for e-invoicing.",
                type="allowance" if indicator == 'allowance' else "charge",
            ),
            'taxes_id': [(6, 0, [])],
            'supplier_taxes_id': [(6, 0, [])],
        }
        if categ_all:
            vals['categ_id'] = categ_all.id
        # Odoo 17 does not expose account_sale_income_id on res.company.
        # Use it when available, otherwise fall back to the discount income account.
        default_income = getattr(company, 'account_sale_income_id', False) or getattr(
            company,
            'account_discount_income_allocation_id',
            False,
        ) or False
        if default_income:
            vals['property_account_income_id'] = default_income.id

        new_product = Product.create(vals)
        company.sudo()[config_field] = new_product.id
        return new_product

    def action_add_document_allowance_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Document Allowance'),
            'res_model': 'orchida.document.ac.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_indicator': 'allowance',
            },
        }

    def action_add_document_charge_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Document Charge'),
            'res_model': 'orchida.document.ac.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_indicator': 'charge',
            },
        }

    def action_open_orchida_uom_mapping(self):
        self.ensure_one()
        action = self.env.ref('orchida_uae_e_invoicing.action_orchida_uom_api_map').read()[0]
        action['domain'] = [('company_id', '=', self.company_id.id)]
        action['context'] = {
            'default_company_id': self.company_id.id,
            'search_default_company_id': self.company_id.id,
        }
        return action

    def _orchida_is_enabled(self):
        return bool(getattr((self.company_id or self.env.company), "orchida_connector_enabled", True))

    def _orchida_should_submit_einvoice(self):
        """True when this move participates in Orchida e-invoicing."""
        self.ensure_one()
        if not self._orchida_is_enabled():
            return False
        return (
            self.move_type in ("out_invoice", "out_refund")
            and bool(self.journal_id.orchida_submit_einvoice)
        )

    @api.constrains('amount_total', 'state', 'move_type')
    def _check_orchida_negative_total(self):
        for move in self:
            if not move._orchida_is_enabled():
                continue
            if (
                move.state == 'posted'
                and move._orchida_should_submit_einvoice()
                and move.move_type == 'out_invoice'
                and move.amount_total < 0
                and not self.env.context.get('bypass_negative_total_check')
            ):
                raise UserError(_(
                    "Invoice total is negative (%(amt)s). "
                    "Please check Document Allowance/Charge lines.",
                    amt=move.amount_total,
                ))

    def _orchida_format_validation_errors(self, errors):
        return "\n".join(f"- {error}" for error in (errors or []))

    def action_post(self):
        einvoice_moves = self.filtered(lambda m: m._orchida_should_submit_einvoice())
        for move in einvoice_moves:
            if any(attempt.outcome == 'valid' for attempt in move.orchida_send_attempt_ids):
                raise UserError(_('%s was already sent successfully.', move.display_name))
            validation_errors = validate_invoice_document_for_orchida(move)
            if validation_errors:
                # Dedicated message when UoM mapping is missing
                move._raise_missing_uom_mapping_error(validation_errors)
                raise UserError(_(
                    "Cannot confirm invoice %(name)s. Fix these e-invoicing checks first:\n\n%(errors)s",
                    name=move.display_name or move.name or _("Draft"),
                    errors=self._orchida_format_validation_errors(validation_errors),
                ))

        res = super().action_post()

        if len(self) > 1:
            return res

        for move in einvoice_moves:
            if move.state != 'posted' or not move.company_id.orchida_auto_submit_einvoice:
                continue
            result = self._orchida_submit_invoice(move)
            if not result['success']:
                raise UserError(_(
                    'E-invoice submission failed for %(name)s.\n'
                    'The invoice was NOT confirmed.\n\n%(details)s',
                    name=move.name,
                    details=result['error_message'],
                ))
            self._record_send_result(move, result, 'automatic')
        return res

    def _record_send_result(self, move, result, source):
        return self.env['api.sent.invoice'].sudo().create({
            'move_id': move.id,
            'sent_date': fields.Datetime.now(),
            'company_id': move.company_id.id,
            'response': result['response_text'],
            'status_response': result['status_response'],
            'orchida_tax_status': result['tax_status'],
            'orchida_receiver_status': result['receiver_status'],
            'success': result['success'],
            'outcome': result['outcome'],
            'source': source,
            'internal_code': result['internal_code'],
            'request_payload': result['request_payload'],
            'http_status': result['http_status'],
            'attempt_count': result['attempt_count'],
            'api_uuid': result['api_uuid'],
            'failure_type': (
                False if result['success'] else result.get('failure_type') or classify_failure(result)
            ),
        })

    def _orchida_submit_invoice(self, move):
        """Submit invoice to Orchida API. Returns result dict; does not write api.sent.invoice."""
        validation_errors = validate_invoice_for_orchida(move)
        if validation_errors:
            message = 'Pre-submission validation failed:\n' + self._orchida_format_validation_errors(validation_errors)
            return self._orchida_failed_submission_result(move, message)

        try:
            payload = build_invoice_payload(move)
        except Exception as exc:
            message = f'Payload build error: {exc}'
            _logger.exception('[Invoice %s] Payload build failed', move.name)
            return self._orchida_failed_submission_result(move, message)

        result = submit_payload(move.company_id, payload)
        _logger.info(
            '[Invoice %s] API submit outcome: %s after %s attempt(s)',
            move.name,
            result['outcome'],
            result['attempt_count'],
        )
        return result

    def _orchida_failed_submission_result(self, move, message):
        return {
            'success': False,
            'outcome': 'failed',
            'response_text': message,
            'status_response': '',
            'tax_status': 'invalid',
            'receiver_status': 'invalid',
            'error_message': message,
            'http_status': 0,
            'attempt_count': 0,
            'internal_code': (move.name or '').replace('/', '-'),
            'request_payload': '',
            'api_uuid': '',
            'failure_type': classify_failure({
                'outcome': 'failed',
                'http_status': 0,
                'error_message': message,
            }),
        }

    def action_orchida_send(self):
        if not self.env.user.has_group('account.group_account_user'):
            raise AccessError(_('Only accounting users can send e-invoices.'))

        sent = 0
        failed = []
        skipped = []
        for move in self.sorted('id'):
            if not move._orchida_is_enabled():
                message = _('Connector is disabled for company %s.', move.company_id.display_name)
                if len(self) == 1:
                    raise UserError(message)
                skipped.append(message)
                continue
            # Serialize each invoice send so concurrent users cannot submit it twice.
            self.env.cr.execute(
                'SELECT id FROM account_move WHERE id = %s FOR UPDATE',
                [move.id],
            )
            move.invalidate_recordset([
                'state',
                'orchida_submission_state',
                'orchida_send_attempt_ids',
            ])
            if move.state != 'posted' or not move._orchida_should_submit_einvoice():
                message = _('%s is not an eligible posted invoice.', move.display_name)
                if len(self) == 1:
                    raise UserError(message)
                skipped.append(message)
                continue
            if move.orchida_submission_state == 'valid':
                message = _('%s was already sent successfully.', move.display_name)
                if len(self) == 1:
                    raise UserError(message)
                skipped.append(message)
                continue
            latest_attempt = move.orchida_send_attempt_ids.sorted('id')[-1:]
            if latest_attempt and latest_attempt.failure_type == 'document':
                message = _('%s needs correction before it can be submitted again.', move.display_name)
                if len(self) == 1:
                    raise UserError(message)
                skipped.append(message)
                continue
            if move.orchida_submission_state == 'unknown':
                latest_attempt = move.orchida_send_attempt_ids.sorted('id')[-1]
                status = latest_attempt._refresh_status_from_api()
                if status != 'not_found':
                    skipped.append(_(
                        '%(name)s was not resent because its remote status is %(status)s.',
                        name=move.display_name,
                        status=status,
                    ))
                    continue

            source = 'retry' if move.orchida_send_attempt_ids else 'manual'
            result = move._orchida_submit_invoice(move)
            attempt = move._record_send_result(move, result, source)
            if result['success']:
                sent += 1
            else:
                failed.append(f"{move.display_name}: {result['error_message']}")

        messages = [_('%s invoice(s) sent successfully.', sent)]
        if failed:
            messages.append(_('%s invoice(s) failed.', len(failed)))
        if skipped:
            messages.append(_('%s invoice(s) skipped.', len(skipped)))
        params = {
            'title': _('E-Invoice'),
            'message': '\n'.join(messages + failed + skipped),
            'type': 'success' if sent and not failed else 'warning',
            'sticky': bool(failed or skipped),
        }
        if len(self) == 1 and sent == 1:
            params['links'] = [{
                'label': _('Open Submission'),
                'url': f'#id={attempt.id}&model=api.sent.invoice',
            }]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params,
        }

    def action_open_latest_einvoice_submission(self):
        """Open the Orchida connector form for this invoice's latest submission."""
        self.ensure_one()
        attempt = self.orchida_send_attempt_ids.sorted('id')[-1:]
        if not attempt:
            raise UserError(_(
                'This invoice has no Orchida e-invoice submission yet. '
                'Submit it with "Submit E-Invoice" first.'
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': _('E-Invoice Submission'),
            'res_model': 'api.sent.invoice',
            'view_mode': 'form',
            'res_id': attempt.id,
        }

    def action_open_einvoice_submissions(self):
        return self.action_open_latest_einvoice_submission()

    def _send_invoice_to_api(self, move):
        """Compatibility entry point for existing resend actions."""
        move.action_orchida_send()
        return move.orchida_submission_state == 'valid'
