# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_default_duration = fields.Float(
        string='Default Appointment Duration (Hours)',
        default=0.5,
        config_parameter='medical_appointment.default_duration',
        help='Default duration used when creating a new appointment without a specific service'
    )
    allow_conflict_override = fields.Boolean(
        string='Allow Conflict Overrides',
        default=True,
        config_parameter='medical_appointment.allow_conflict_override',
        help='Permit authorized supervisors to override doctor schedule conflicts'
    )
    require_override_reason = fields.Boolean(
        string='Mandatory Override Reason',
        default=True,
        config_parameter='medical_appointment.require_override_reason',
        help='Require users to type a justification reason whenever overriding a conflict'
    )
    auto_followup_call_days = fields.Integer(
        string='Default Follow-up Call Delay (Days)',
        default=2,
        config_parameter='medical_appointment.auto_followup_days',
        help='Default number of days ahead to schedule next follow-up activity on unanswered calls'
    )

    # CRM Role-based Access Controls
    crm_enable_doctor = fields.Boolean(
        string='Allow Doctors CRM Access',
        default=False,
        config_parameter='medical_appointment.crm_enable_doctor',
        help='When disabled, Doctors cannot access the CRM module or leads and will see a guidance message.'
    )
    crm_enable_nurse = fields.Boolean(
        string='Allow Nurses CRM Access',
        default=False,
        config_parameter='medical_appointment.crm_enable_nurse',
        help='When disabled, Nurses cannot access the CRM module or leads and will see a guidance message.'
    )
    crm_enable_receptionist = fields.Boolean(
        string='Allow Receptionists CRM Access',
        default=True,
        config_parameter='medical_appointment.crm_enable_receptionist',
        help='Permits receptionists to access CRM leads and pipeline for booking confirmations and arrivals.'
    )
    crm_enable_sales = fields.Boolean(
        string='Allow Sales Employees CRM Access',
        default=True,
        config_parameter='medical_appointment.crm_enable_sales',
        help='Permits sales staff to follow up on leads and book appointments.'
    )
    crm_sales_only_unassigned_and_own = fields.Boolean(
        string='Salesperson: Unassigned & Own Leads Only',
        default=True,
        config_parameter='medical_appointment.crm_sales_only_unassigned_and_own',
        help='Strictly restrict salespeople so they only see leads not assigned to anyone or assigned to them.'
    )

    def set_values(self):
        super().set_values()
        self._sync_medical_crm_roles()
        self.env['ir.ui.menu'].clear_caches()

def _is_param_enabled(icp, key, default='False'):
    val = icp.get_param(key, default)
    if isinstance(val, bool):
        return val
    return str(val or '').strip().lower() in ('true', '1')


    @api.model
    def _sync_medical_crm_roles(self):
        """Synchronize user groups and permissions based on medical CRM settings"""
        icp = self.env['ir.config_parameter'].sudo()
        doc_crm = _is_param_enabled(icp, 'medical_appointment.crm_enable_doctor', 'False')
        nurse_crm = _is_param_enabled(icp, 'medical_appointment.crm_enable_nurse', 'False')
        recep_crm = _is_param_enabled(icp, 'medical_appointment.crm_enable_receptionist', 'True')

        sale_own = self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        sale_all = self.env.ref('sales_team.group_sale_salesman_all_leads', raise_if_not_found=False)
        sale_mgr = self.env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
        sales_groups = [g for g in [sale_own, sale_all, sale_mgr] if g]

        grp_doctor = self.env.ref('medical_employee_management.group_medical_doctor', raise_if_not_found=False)
        grp_nurse = self.env.ref('medical_employee_management.group_medical_nurse', raise_if_not_found=False)
        grp_sales = self.env.ref('medical_employee_management.group_medical_sales', raise_if_not_found=False)
        grp_sales_mgr = self.env.ref('medical_employee_management.group_medical_sales_manager', raise_if_not_found=False)
        grp_recep = self.env.ref('medical_employee_management.group_medical_receptionist', raise_if_not_found=False)
        admin_grp = self.env.ref('base.group_system', raise_if_not_found=False)

        # 1. Doctor users: Strip sales groups if CRM disabled
        if grp_doctor and not doc_crm:
            for user in grp_doctor.users:
                if user._is_admin() or user._is_system() or (admin_grp and admin_grp in user.groups_id):
                    continue
                if (grp_sales and grp_sales in user.groups_id) or (grp_recep and grp_recep in user.groups_id):
                    continue
                to_remove = [sg.id for sg in sales_groups if sg in user.groups_id]
                if to_remove:
                    user.sudo().write({'groups_id': [(3, gid) for gid in to_remove]})

        # 2. Nurse users: Strip sales groups if CRM disabled
        if grp_nurse and not nurse_crm:
            for user in grp_nurse.users:
                if user._is_admin() or user._is_system() or (admin_grp and admin_grp in user.groups_id):
                    continue
                if (grp_sales and grp_sales in user.groups_id) or (grp_recep and grp_recep in user.groups_id):
                    continue
                to_remove = [sg.id for sg in sales_groups if sg in user.groups_id]
                if to_remove:
                    user.sudo().write({'groups_id': [(3, gid) for gid in to_remove]})

        # 3. Receptionist users: Ensure All Leads access if enabled
        if grp_recep and sale_all and recep_crm:
            for user in grp_recep.users:
                if sale_all not in user.groups_id:
                    user.sudo().write({'groups_id': [(4, sale_all.id)]})

        # 4. Sales users: Ensure standard salesmen have ONLY 'User: Own Documents Only'
        if grp_sales and sale_own:
            for user in grp_sales.users:
                if user._is_admin() or user._is_system() or (admin_grp and admin_grp in user.groups_id):
                    continue
                is_mgr = bool(grp_sales_mgr and grp_sales_mgr in user.groups_id)
                if not is_mgr:
                    to_remove = []
                    if sale_all and sale_all in user.groups_id:
                        to_remove.append(sale_all.id)
                    if sale_mgr and sale_mgr in user.groups_id:
                        to_remove.append(sale_mgr.id)
                    if to_remove:
                        user.sudo().write({'groups_id': [(3, gid) for gid in to_remove]})
                    if sale_own not in user.groups_id:
                        user.sudo().write({'groups_id': [(4, sale_own.id)]})
