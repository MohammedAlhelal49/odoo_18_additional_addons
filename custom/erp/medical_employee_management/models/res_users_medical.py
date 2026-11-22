# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResUsersMedical(models.Model):
    _inherit = 'res.users'

    medical_staff_role = fields.Selection([
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('sales', 'Sales Employee'),
        ('manager', 'Appointment Manager'),
    ], string='Primary Medical Role', compute='_compute_medical_roles', inverse='_inverse_medical_staff_role', store=False)

    medical_is_doctor = fields.Boolean(
        string='Doctor',
        compute='_compute_medical_roles',
        inverse='_inverse_medical_roles',
        help='Doctor: Start/End consultations, clinical notes, diagnosis, prescriptions, follow-up bookings, and patient medical history'
    )
    medical_is_nurse = fields.Boolean(
        string='Nurse',
        compute='_compute_medical_roles',
        inverse='_inverse_medical_roles',
        help='Nurse: Patient vitals triage (BP, temp, pulse, SpO2, weight, height, BMI, blood sugar), nurse notes, and ready-for-doctor status'
    )
    medical_is_receptionist = fields.Boolean(
        string='Receptionist',
        compute='_compute_medical_roles',
        inverse='_inverse_medical_roles',
        help='Receptionist: Day-before confirmation calls, confirm bookings, reschedule appointment date & doctor, and patient arrival check-in'
    )
    medical_is_sales = fields.Boolean(
        string='Sales Employee',
        compute='_compute_medical_roles',
        inverse='_inverse_medical_roles',
        help='Sales Employee: CRM lead follow-up, call logging, book appointments from leads, choose doctor & service, finish lead, sales commission tracking'
    )
    medical_is_manager = fields.Boolean(
        string='Appointment Manager',
        compute='_compute_medical_roles',
        inverse='_inverse_medical_roles',
        help='Manager: Full supervisory access across all staff actions, supervisor schedule conflict override, and configurations'
    )

    def _compute_medical_roles(self):
        doctor_grp = self.env.ref('medical_employee_management.group_medical_doctor', raise_if_not_found=False)
        nurse_grp = self.env.ref('medical_employee_management.group_medical_nurse', raise_if_not_found=False)
        receptionist_grp = self.env.ref('medical_employee_management.group_medical_receptionist', raise_if_not_found=False)
        sales_grp = self.env.ref('medical_employee_management.group_medical_sales', raise_if_not_found=False)
        manager_grp = self.env.ref('medical_appointment_management.group_medical_appointment_manager', raise_if_not_found=False)
        system_grp = self.env.ref('base.group_system', raise_if_not_found=False)

        for user in self:
            groups = user.groups_id
            is_system = bool(system_grp and system_grp in groups)
            is_mgr = bool(manager_grp and manager_grp in groups) or is_system

            user.medical_is_doctor = bool(doctor_grp and doctor_grp in groups) or is_mgr
            user.medical_is_nurse = bool(nurse_grp and nurse_grp in groups) or is_mgr
            user.medical_is_receptionist = bool(receptionist_grp and receptionist_grp in groups) or is_mgr
            user.medical_is_sales = bool(sales_grp and sales_grp in groups) or is_mgr
            user.medical_is_manager = is_mgr

            if user.medical_is_manager:
                user.medical_staff_role = 'manager'
            elif user.medical_is_doctor:
                user.medical_staff_role = 'doctor'
            elif user.medical_is_nurse:
                user.medical_staff_role = 'nurse'
            elif user.medical_is_receptionist:
                user.medical_staff_role = 'receptionist'
            elif user.medical_is_sales:
                user.medical_staff_role = 'sales'
            else:
                user.medical_staff_role = False

    def _inverse_medical_staff_role(self):
        for user in self:
            role = user.medical_staff_role
            if role == 'doctor':
                user.medical_is_doctor = True
            elif role == 'nurse':
                user.medical_is_nurse = True
            elif role == 'receptionist':
                user.medical_is_receptionist = True
            elif role == 'sales':
                user.medical_is_sales = True
            elif role == 'manager':
                user.medical_is_manager = True
            self._inverse_medical_roles()

    def _inverse_medical_roles(self):
        doctor_grp = self.env.ref('medical_employee_management.group_medical_doctor', raise_if_not_found=False)
        nurse_grp = self.env.ref('medical_employee_management.group_medical_nurse', raise_if_not_found=False)
        receptionist_grp = self.env.ref('medical_employee_management.group_medical_receptionist', raise_if_not_found=False)
        sales_grp = self.env.ref('medical_employee_management.group_medical_sales', raise_if_not_found=False)
        manager_grp = self.env.ref('medical_appointment_management.group_medical_appointment_manager', raise_if_not_found=False)

        role_mapping = [
            ('medical_is_doctor', doctor_grp),
            ('medical_is_nurse', nurse_grp),
            ('medical_is_receptionist', receptionist_grp),
            ('medical_is_sales', sales_grp),
            ('medical_is_manager', manager_grp),
        ]

        for user in self:
            current_groups = set(user.groups_id.ids)
            for field_name, grp in role_mapping:
                if not grp:
                    continue
                is_active = getattr(user, field_name)
                if is_active:
                    current_groups.add(grp.id)
                else:
                    current_groups.discard(grp.id)
            user.write({'groups_id': [(6, 0, list(current_groups))]})

            # Auto-ensure or update linked hr.employee record
            user._sync_or_create_medical_employee()

    def _sync_or_create_medical_employee(self):
        if self.env.context.get('skip_medical_sync'):
            return
        self.ensure_one()
        if not self.name or not self.id:
            return
        has_any_role = (self.medical_is_doctor or self.medical_is_nurse or
                        self.medical_is_receptionist or self.medical_is_sales or self.medical_is_manager)
        if not has_any_role:
            return

        Employee = self.env['hr.employee'].sudo()
        emp = Employee.search([('user_id', '=', self.id)], limit=1)

        primary_role = False
        if self.medical_is_doctor:
            primary_role = 'doctor'
        elif self.medical_is_nurse:
            primary_role = 'nurse'
        elif self.medical_is_receptionist:
            primary_role = 'receptionist'
        elif self.medical_is_sales:
            primary_role = 'sales'

        vals = {
            'is_appointment_provider': bool(self.medical_is_doctor or self.medical_is_manager),
        }
        if primary_role:
            vals['medical_employee_type'] = primary_role

        if emp:
            emp.with_context(skip_medical_sync=True).write(vals)
        elif self.name:
            vals.update({
                'name': self.name,
                'user_id': self.id,
                'work_email': self.email or self.login,
            })
            Employee.with_context(skip_medical_sync=True).create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user in users:
            if user.name:
                user._sync_or_create_medical_employee()
        return users

    def write(self, vals):
        res = super().write(vals)
        for user in self:
            if user.name:
                user._sync_or_create_medical_employee()
        return res
