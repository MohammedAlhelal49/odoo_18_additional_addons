from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class HrEmployeeMedical(models.Model):
    _inherit = 'hr.employee'

    # Medical Center Employee Classification
    medical_employee_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('sales', 'Sales Employee'),
    ], string='Medical Center Role',
        help='Classify employee by medical center role (separate from job title)')

    is_medical_manager = fields.Boolean(
        string='Department Head / Team Manager',
        default=False,
        tracking=True,
        help='Check if this employee is a Head/Manager of other employees in this medical role '
             '(e.g., Doctor Manager / Head of Doctors, Nurse Manager / Head Nurse, '
             'Receptionist Manager, Sales Manager).'
    )

    medical_specialization = fields.Char(
        string='Medical Specialization',
        help='For doctors: cardiology, dentistry, etc.'
    )

    is_appointment_provider = fields.Boolean(
        string='Can Provide Appointments',
        default=False,
        help='Check if this employee can be assigned as doctor/provider for appointments'
    )

    # Schedule & Availability
    working_hours_per_week = fields.Float(
        string='Working Hours Per Week',
        help='Total expected working hours per week'
    )

    # Group Assignment (for audit/reference)
    group_ids = fields.Many2many(
        'res.groups',
        compute='_compute_medical_groups',
        store=False,
        string='Medical Center Groups',
        help='Security groups assigned based on medical center role'
    )

    # Audit trail
    medical_type_change_date = fields.Datetime(
        string='Medical Role Last Changed',
        readonly=True,
        help='Last date when medical center role was changed'
    )

    medical_type_changed_by_id = fields.Many2one(
        'res.users',
        string='Medical Role Changed By',
        readonly=True,
        help='User who last changed the medical center role'
    )

    @api.depends('medical_employee_type', 'is_medical_manager')
    def _compute_medical_groups(self):
        """Compute security groups based on medical employee type and manager flag"""
        group_mapping = {
            ('doctor', False): 'medical_employee_management.group_medical_doctor',
            ('doctor', True): 'medical_employee_management.group_medical_doctor_manager',
            ('nurse', False): 'medical_employee_management.group_medical_nurse',
            ('nurse', True): 'medical_employee_management.group_medical_nurse_manager',
            ('receptionist', False): 'medical_employee_management.group_medical_receptionist',
            ('receptionist', True): 'medical_employee_management.group_medical_receptionist_manager',
            ('sales', False): 'medical_employee_management.group_medical_sales',
            ('sales', True): 'medical_employee_management.group_medical_sales_manager',
        }

        for employee in self:
            key = (employee.medical_employee_type, bool(employee.is_medical_manager))
            if employee.medical_employee_type and key in group_mapping:
                group_xmlid = group_mapping[key]
                try:
                    group = self.env.ref(group_xmlid)
                    employee.group_ids = [group.id]
                except ValueError:
                    employee.group_ids = []
            else:
                employee.group_ids = []

    def _sync_user_medical_groups(self):
        """Synchronize the employee's medical role into their linked user's security groups"""
        if self.env.context.get('skip_medical_sync'):
            return
        all_medical_group_xmlids = [
            'medical_employee_management.group_medical_doctor',
            'medical_employee_management.group_medical_doctor_manager',
            'medical_employee_management.group_medical_nurse',
            'medical_employee_management.group_medical_nurse_manager',
            'medical_employee_management.group_medical_receptionist',
            'medical_employee_management.group_medical_receptionist_manager',
            'medical_employee_management.group_medical_sales',
            'medical_employee_management.group_medical_sales_manager',
        ]
        all_medical_group_ids = []
        for xmlid in all_medical_group_xmlids:
            g = self.env.ref(xmlid, raise_if_not_found=False)
            if g:
                all_medical_group_ids.append(g.id)

        group_mapping = {
            ('doctor', False): 'medical_employee_management.group_medical_doctor',
            ('doctor', True): 'medical_employee_management.group_medical_doctor_manager',
            ('nurse', False): 'medical_employee_management.group_medical_nurse',
            ('nurse', True): 'medical_employee_management.group_medical_nurse_manager',
            ('receptionist', False): 'medical_employee_management.group_medical_receptionist',
            ('receptionist', True): 'medical_employee_management.group_medical_receptionist_manager',
            ('sales', False): 'medical_employee_management.group_medical_sales',
            ('sales', True): 'medical_employee_management.group_medical_sales_manager',
        }

        for employee in self:
            if not employee.user_id:
                continue
            key = (employee.medical_employee_type, bool(employee.is_medical_manager))
            target_group = None
            if employee.medical_employee_type and key in group_mapping:
                target_group = self.env.ref(group_mapping[key], raise_if_not_found=False)

            user = employee.user_id.sudo()
            current_group_ids = set(user.groups_id.ids)
            to_remove = set(all_medical_group_ids) - ({target_group.id} if target_group else set())
            current_group_ids -= to_remove
            if target_group:
                current_group_ids.add(target_group.id)
            user.with_context(skip_medical_sync=True).write({'groups_id': [(6, 0, list(current_group_ids))]})

    @api.onchange('medical_employee_type')
    def _onchange_medical_employee_type(self):
        """Set appointment provider flag for doctors"""
        if self.medical_employee_type == 'doctor':
            self.is_appointment_provider = True
        elif self.medical_employee_type in ('nurse', 'receptionist', 'sales'):
            self.is_appointment_provider = False

    @api.constrains('is_appointment_provider', 'medical_employee_type')
    def _check_appointment_provider_valid(self):
        """Only doctors can be appointment providers"""
        for employee in self:
            if employee.is_appointment_provider and employee.medical_employee_type != 'doctor':
                raise ValidationError(
                    _('Only employees with "Doctor" role can be appointment providers.')
                )

    @api.constrains('medical_specialization', 'medical_employee_type')
    def _check_specialization_for_doctor(self):
        """Specialization field is meaningful only for doctors"""
        for employee in self:
            if employee.medical_specialization and employee.medical_employee_type != 'doctor':
                raise ValidationError(
                    _('Medical specialization should only be set for doctors.')
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Track medical role assignment on creation and sync security groups"""
        employees = super().create(vals_list)
        for emp in employees:
            if emp.medical_employee_type:
                emp.message_post(
                    body=_("Medical center role assigned: %s") % emp.get_medical_employee_type_display(),
                    message_type='comment'
                )
        employees._sync_user_medical_groups()
        return employees

    def write(self, vals):
        """Track medical role changes and sync security groups"""
        user = self.env.user
        is_admin_or_hr = user.has_group('base.group_system') or user.has_group('medical_employee_management.group_medical_hr_manager')
        if not is_admin_or_hr and not self.env.su:
            # Enforce: only own record can be edited by medical staff
            for emp in self:
                if emp.user_id.id != user.id and emp.id != user.employee_id.id:
                    raise AccessError(_("You are only allowed to edit your own employee profile. All other records are read-only."))
            if 'medical_employee_type' in vals or 'is_medical_manager' in vals:
                raise AccessError(_("Only administrators can change medical role or manager assignment."))

        old_data = {emp.id: (emp.medical_employee_type, emp.active, emp.user_id.id) for emp in self}

        if 'medical_employee_type' in vals and vals.get('medical_employee_type') != 'doctor':
            if 'is_appointment_provider' not in vals:
                vals['is_appointment_provider'] = False
            if 'medical_specialization' not in vals:
                vals['medical_specialization'] = False

        result = super().write(vals)

        for employee in self:
            old_type, old_active, old_user_id = old_data.get(employee.id, (False, employee.active, False))

            # Track medical type change
            if 'medical_employee_type' in vals and vals.get('medical_employee_type') != old_type:
                employee.medical_type_change_date = fields.Datetime.now()
                employee.medical_type_changed_by_id = self.env.user.id
                old_label = dict(self._fields['medical_employee_type'].selection).get(old_type, 'None')
                new_label = dict(self._fields['medical_employee_type'].selection).get(
                    vals.get('medical_employee_type'),
                    'None'
                )
                employee.message_post(
                    body=_("Medical center role changed from %s to %s") % (old_label, new_label),
                    message_type='notification'
                )

            # Track activation/deactivation
            if 'active' in vals and vals.get('active') != old_active:
                status = _("activated") if vals.get('active') else _("deactivated")
                employee.message_post(
                    body=_("Employee %s") % status,
                    message_type='notification'
                )

        if 'medical_employee_type' in vals or 'user_id' in vals or 'is_medical_manager' in vals:
            self._sync_user_medical_groups()

        return result

    def save(self):
        """Helper for test compatibility"""
        self.flush_recordset()
        return self

    def get_medical_employee_type_display(self):
        """Get display name for medical employee type"""
        self.ensure_one()
        return dict(self._fields['medical_employee_type'].selection).get(
            self.medical_employee_type,
            'Unknown'
        )

    def action_make_doctor(self):
        """Quick action to assign doctor role"""
        self.ensure_one()
        self.medical_employee_type = 'doctor'
        self.is_appointment_provider = True

    def action_make_nurse(self):
        """Quick action to assign nurse role"""
        self.ensure_one()
        self.medical_employee_type = 'nurse'
        self.is_appointment_provider = False

    def action_make_receptionist(self):
        """Quick action to assign receptionist role"""
        self.ensure_one()
        self.medical_employee_type = 'receptionist'
        self.is_appointment_provider = False

    def action_make_sales(self):
        """Quick action to assign sales role"""
        self.ensure_one()
        self.medical_employee_type = 'sales'
        self.is_appointment_provider = False

    @api.model
    def action_view_medical_staff_default(self):
        """Return action to view medical staff with default filter based on current user's role"""
        current_user = self.env.user
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', current_user.id)], limit=1
        )

        user_type = current_employee.medical_employee_type if current_employee else False
        if not user_type:
            if getattr(current_user, 'medical_is_doctor', False) or current_user.has_group('medical_employee_management.group_medical_doctor'):
                user_type = 'doctor'
            elif getattr(current_user, 'medical_is_nurse', False) or current_user.has_group('medical_employee_management.group_medical_nurse'):
                user_type = 'nurse'
            elif getattr(current_user, 'medical_is_receptionist', False) or current_user.has_group('medical_employee_management.group_medical_receptionist'):
                user_type = 'receptionist'
            elif getattr(current_user, 'medical_is_sales', False) or current_user.has_group('medical_employee_management.group_medical_sales'):
                user_type = 'sales'

        context = {
            'create': False,
        }

        filter_map = {
            'doctor': 'search_default_filter_doctors',
            'nurse': 'search_default_filter_nurses',
            'receptionist': 'search_default_filter_receptionists',
            'sales': 'search_default_filter_sales',
        }

        if user_type and user_type in filter_map:
            context[filter_map[user_type]] = 1
        else:
            context['search_default_filter_all_medical_staff'] = 1

        kanban_view = self.env.ref('medical_employee_management.view_medical_staff_kanban', raise_if_not_found=False)
        list_view = self.env.ref('medical_employee_management.view_medical_staff_list', raise_if_not_found=False)
        search_view = self.env.ref('medical_employee_management.hr_employee_search_medical', raise_if_not_found=False)

        views = []
        if kanban_view:
            views.append((kanban_view.id, 'kanban'))
        if list_view:
            views.append((list_view.id, 'list'))
        views.append((False, 'form'))

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Medical Staff',
            'res_model': 'hr.employee',
            'view_mode': 'kanban,list,form',
            'views': views,
            'domain': [('medical_employee_type', '!=', False)],
            'context': context,
        }
        if search_view:
            action['search_view_id'] = [search_view.id, 'search']

        return action

    @api.model
    def action_view_my_team(self):
        """Return action to view medical staff filtered by current user's type"""
        current_user = self.env.user
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', current_user.id)], limit=1
        )

        domain = [('medical_employee_type', '!=', False)]
        if current_employee and current_employee.medical_employee_type:
            domain = [('medical_employee_type', '=', current_employee.medical_employee_type)]

        kanban_view = self.env.ref('medical_employee_management.view_medical_staff_kanban', raise_if_not_found=False)
        list_view = self.env.ref('medical_employee_management.view_medical_staff_list', raise_if_not_found=False)
        search_view = self.env.ref('medical_employee_management.hr_employee_search_medical', raise_if_not_found=False)

        views = []
        if kanban_view:
            views.append((kanban_view.id, 'kanban'))
        if list_view:
            views.append((list_view.id, 'list'))
        views.append((False, 'form'))

        action = {
            'type': 'ir.actions.act_window',
            'name': 'My Team',
            'res_model': 'hr.employee',
            'view_mode': 'kanban,list,form',
            'views': views,
            'domain': domain,
            'context': {'create': False},
        }
        if search_view:
            action['search_view_id'] = [search_view.id, 'search']

        return action
