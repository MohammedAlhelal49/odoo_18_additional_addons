from odoo import _, api, fields, models
from odoo.exceptions import UserError

# رصيد الغسيل (شحن مسبق مع بونص): طريقتين دفع خاصّين بنقطة البيع
#   balance: "Laundry Balance" - سالب على طلب الشحن (الرصيد بيزيد)، موجب لما الزبون يدفع فيه طلب.
#            قيده على حساب "رصيد الزبائن المسبق" (التزام) باسم الزبون.
#   bonus:   "Prepaid Bonus" - موجب على طلب الشحن بقيمة البونص، قيده على حساب مصروف البونص.
# طلب الشحن: كاش 100 + بونص 25 - رصيد 125 = 0 (بدون أصناف وبدون فاتورة).
PREPAID_ROLES = [('balance', 'Laundry Balance'), ('bonus', 'Prepaid Bonus')]


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    laundry_prepaid_role = fields.Selection(
        PREPAID_ROLES, string='Laundry Prepaid Role', copy=False,
        help='Laundry Balance: the customer prepaid balance (top-up and paying from the balance).\n'
             'Prepaid Bonus: the bonus given on a top-up (not shown on the payment screen).')

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        return fields_list + ['laundry_prepaid_role']

    # ------------------------------------------------------------------ setup
    @api.model
    def _laundry_free_code(self, company, start):
        Account = self.env['account.account'].with_company(company)
        code = start
        while Account.search_count([('code', '=', str(code)), ('company_ids', 'in', company.id)]):
            code += 1
        return str(code)

    @api.model
    def _laundry_prepaid_account(self, company, name, account_type, start):
        """الحساب بهالاسم، أو حساب جديد بأول رقم فاضي من start وطالع."""
        Account = self.env['account.account'].with_company(company).sudo()
        account = Account.search([('name', '=', name), ('company_ids', 'in', company.id)], limit=1)
        if not account:
            account = Account.create({
                'name': name,
                'code': self._laundry_free_code(company, start),
                'account_type': account_type,
                'reconcile': account_type == 'liability_current',
                'company_ids': [(6, 0, company.ids)],
            })
        return account

    @api.model
    def _laundry_prepaid_journal(self, company, code, name, account):
        Journal = self.env['account.journal'].with_company(company).sudo()
        journal = Journal.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
        if not journal:
            journal = Journal.create({
                'name': name, 'code': code, 'type': 'bank', 'company_id': company.id,
                'default_account_id': account.id,
            })
        return journal

    @api.model
    def laundry_setup_prepaid(self, company=None):
        """ينشئ (إذا مش موجودين) حسابات وطرق دفع رصيد الغسيل، ويضيفهن لنقاط البيع.

        بيتعاد بأمان: اللي موجود ما بيتغيّر.
        """
        company = company or self.env.company
        result = self.browse()
        deposit = self._laundry_prepaid_account(company, 'Customer Prepaid Balance', 'liability_current', 201018)
        bonus = self._laundry_prepaid_account(company, 'Prepaid Balance Bonus', 'expense', 400014)
        for role, name, code, account in (
                ('balance', 'Laundry Balance', 'LBAL', deposit),
                ('bonus', 'Prepaid Bonus', 'LBON', bonus)):
            method = self.sudo().search([('laundry_prepaid_role', '=', role), ('company_id', '=', company.id)], limit=1)
            if not method:
                journal = self._laundry_prepaid_journal(company, code, name, account)
                method = self.sudo().create({
                    'name': name,
                    'company_id': company.id,
                    'journal_id': journal.id,
                    'outstanding_account_id': account.id,
                    # سطر لكل دفعة باسم الزبون: رصيد كل زبون بيبيّن بحساب الرصيد المسبق
                    'split_transactions': role == 'balance',
                    'laundry_prepaid_role': role,
                })
            result |= method
        # Odoo ما بيسمح يتغيّروا طرق دفع نقطة بيع جلستها مفتوحة: بتنضاف بعد إغلاقها (Set Up مرة تانية)
        configs = self.env['pos.config'].sudo().search([('company_id', '=', company.id)])
        for config in configs.filtered(lambda c: not c.has_active_session):
            missing = result - config.payment_method_ids
            if missing:
                config.payment_method_ids = [(4, m.id) for m in missing]
        return result

    @api.model
    def _laundry_prepaid_pending_configs(self, company=None):
        """نقاط البيع اللي لسا ما انضافلها طرق دفع الرصيد."""
        company = company or self.env.company
        methods = self.sudo().search([('laundry_prepaid_role', '!=', False), ('company_id', '=', company.id)])
        configs = self.env['pos.config'].sudo().search([('company_id', '=', company.id)])
        return configs.filtered(lambda c: len(methods) < 2 or methods - c.payment_method_ids)

    @api.model
    def _laundry_prepaid_methods(self, company=None):
        company = company or self.env.company
        methods = self.sudo().search([('laundry_prepaid_role', '!=', False), ('company_id', '=', company.id)])
        return {m.laundry_prepaid_role: m for m in methods}
