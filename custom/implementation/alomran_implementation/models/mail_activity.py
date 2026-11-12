from odoo import api, fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    # Used by "My Tasks" to hide activities on opportunities of branches that
    # are not selected in the company switcher (opening them raises an
    # access error).
    alomran_in_active_company = fields.Boolean(
        compute='_compute_alomran_in_active_company',
        search='_search_alomran_in_active_company',
    )

    @api.depends_context('allowed_company_ids')
    def _compute_alomran_in_active_company(self):
        companies = self.env.companies
        for activity in self:
            if activity.res_model != 'crm.lead':
                activity.alomran_in_active_company = True
                continue
            company = self.env['crm.lead'].sudo().browse(activity.res_id).company_id
            activity.alomran_in_active_company = not company or company in companies

    def _search_alomran_in_active_company(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise NotImplementedError()
        self.env['crm.lead'].flush_model(['company_id'])
        self.env.cr.execute("""
            SELECT a.id FROM mail_activity a
              JOIN crm_lead l ON l.id = a.res_id
             WHERE a.res_model = 'crm.lead'
               AND l.company_id IS NOT NULL
               AND l.company_id != ALL(%s)
        """, [self.env.companies.ids])
        outside_ids = [r[0] for r in self.env.cr.fetchall()]
        positive = (operator == '=') == value
        return [('id', 'not in' if positive else 'in', outside_ids)]
