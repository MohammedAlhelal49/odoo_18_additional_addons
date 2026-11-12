from odoo import api, fields, models


def _project_code_from(code):
    """Project code printed on the Viewsport documents: the account code without its leading 'J' (J703 -> 703).
    Only numeric codes qualify; anything else (e.g. "Stock") gives False."""
    code = (code or '').strip()
    if code[:1] in ('J', 'j'):
        code = code[1:]
    return code if code.isdigit() else False


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    custom_project_code = fields.Char(string='Project Code')

    def _vs_is_project(self):
        self.ensure_one()
        plan = self.plan_id.root_id or self.plan_id
        return 'project' in (plan.name or '').lower()

    def _vs_fill_project_code(self):
        """Fill an empty Project Code from the account code; a code typed by hand is never overwritten."""
        for account in self:
            if not account.custom_project_code and account._vs_is_project() and _project_code_from(account.code):
                account.custom_project_code = _project_code_from(account.code)

    @api.model_create_multi
    def create(self, vals_list):
        accounts = super().create(vals_list)
        accounts._vs_fill_project_code()
        return accounts

    def write(self, vals):
        res = super().write(vals)
        if 'code' in vals or 'plan_id' in vals:
            self._vs_fill_project_code()
        return res

    @api.model
    def _vs_fill_existing_project_codes(self):
        """Run on module install/upgrade for the projects created before this module version."""
        self.with_context(active_test=False).search([('custom_project_code', '=', False)])._vs_fill_project_code()
