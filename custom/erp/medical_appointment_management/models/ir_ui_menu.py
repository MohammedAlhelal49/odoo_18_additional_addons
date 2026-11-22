# -*- coding: utf-8 -*-

from odoo import api, models, tools


def _is_param_enabled(icp, key, default='False'):
    val = icp.get_param(key, default)
    if isinstance(val, bool):
        return val
    return str(val or '').strip().lower() in ('true', '1')


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _load_menus_blacklist(self):
        res = super()._load_menus_blacklist()
        user = self.env.user
        if user._is_admin() or user._is_system() or self.env.su:
            return res

        icp = self.env['ir.config_parameter'].sudo()

        is_receptionist = user.has_group('medical_employee_management.group_medical_receptionist')
        receptionist_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_receptionist', 'True')

        is_sales = user.has_group('medical_employee_management.group_medical_sales')
        sales_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_sales', 'True')

        # If user has an enabled role allowing CRM access, do not blacklist CRM
        if (is_receptionist and receptionist_enabled) or (is_sales and sales_enabled):
            return res

        is_doctor = user.has_group('medical_employee_management.group_medical_doctor')
        doctor_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_doctor', 'False')

        is_nurse = user.has_group('medical_employee_management.group_medical_nurse')
        nurse_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_nurse', 'False')

        block_crm = False
        if is_doctor and not doctor_enabled:
            block_crm = True
        elif is_nurse and not nurse_enabled:
            block_crm = True
        elif is_receptionist and not receptionist_enabled:
            block_crm = True
        elif is_sales and not sales_enabled:
            block_crm = True

        if block_crm:
            crm_root = self.env.ref('crm.crm_menu_root', raise_if_not_found=False)
            if crm_root:
                crm_menus = self.search([('id', 'child_of', crm_root.id)])
                return list(set(res + crm_menus.ids))

        return res

    @api.model
    @api.returns('self')
    def get_user_roots(self):
        roots = super().get_user_roots()
        blacklist = self._load_menus_blacklist()
        if blacklist:
            roots = roots.filtered(lambda m: m.id not in blacklist)
        return roots
