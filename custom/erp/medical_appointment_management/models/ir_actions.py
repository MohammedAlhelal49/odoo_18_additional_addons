# -*- coding: utf-8 -*-

from odoo import api, models, _


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _get_action_dict(self):
        res = super()._get_action_dict()
        if not res:
            return res

        user = self.env.user
        if user._is_admin() or user._is_system() or self.env.su:
            return res

        # Check if the window action is a CRM action on crm.lead
        res_model = res.get('res_model')
        if res_model == 'crm.lead':
            ctx = self.env.context or {}
            # Allow relational sub-actions or actions inside medical appointment
            if ctx.get('active_model') not in ('medical.appointment', 'appointment.from.lead.wizard') and \
               ctx.get('params', {}).get('model') != 'medical.appointment' and \
               not ctx.get('skip_crm_access_check'):
                self.env['crm.lead']._check_medical_crm_access()

        return res
