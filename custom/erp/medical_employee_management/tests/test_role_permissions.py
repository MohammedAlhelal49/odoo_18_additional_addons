from odoo.tests import TransactionCase
from odoo.exceptions import AccessError


class TestRolePermissions(TransactionCase):
    """Test role-based permission enforcement"""

    def setUp(self):
        super().setUp()
        self.HrEmployee = self.env['hr.employee']
        self.ResUsers = self.env['res.users']
        self.ResGroups = self.env['res.groups']

        self.company = self.env.company

        # Get security groups
        self.group_doctor = self.env.ref('medical_employee_management.group_medical_doctor')
        self.group_nurse = self.env.ref('medical_employee_management.group_medical_nurse')
        self.group_receptionist = self.env.ref('medical_employee_management.group_medical_receptionist')
        self.group_sales = self.env.ref('medical_employee_management.group_medical_sales')
        self.group_hr_manager = self.env.ref('medical_employee_management.group_medical_hr_manager')
        self.group_doctor_manager = self.env.ref('medical_employee_management.group_medical_doctor_manager')
        self.group_nurse_manager = self.env.ref('medical_employee_management.group_medical_nurse_manager')
        self.group_receptionist_manager = self.env.ref('medical_employee_management.group_medical_receptionist_manager')
        self.group_sales_manager = self.env.ref('medical_employee_management.group_medical_sales_manager')

    def test_groups_exist(self):
        """Test that all medical center security groups exist"""
        self.assertIsNotNone(self.group_doctor)
        self.assertIsNotNone(self.group_nurse)
        self.assertIsNotNone(self.group_receptionist)
        self.assertIsNotNone(self.group_sales)
        self.assertIsNotNone(self.group_hr_manager)
        self.assertIsNotNone(self.group_doctor_manager)
        self.assertIsNotNone(self.group_nurse_manager)
        self.assertIsNotNone(self.group_receptionist_manager)
        self.assertIsNotNone(self.group_sales_manager)

    def test_group_names(self):
        """Test that groups have correct names"""
        self.assertIn('Doctor', self.group_doctor.name)
        self.assertIn('Nurse', self.group_nurse.name)
        self.assertIn('Receptionist', self.group_receptionist.name)
        self.assertIn('Sales', self.group_sales.name)

    def test_doctor_employee_creates_with_group(self):
        """Test that doctor employee is associated with doctor group"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Permission Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        # Groups are computed, so they should be in the compute result
        self.assertEqual(len(doctor.group_ids), 1)
        self.assertIn(self.group_doctor, doctor.group_ids)

    def test_nurse_employee_creates_with_group(self):
        """Test that nurse employee is associated with nurse group"""
        nurse = self.HrEmployee.create({
            'name': 'Nurse Permission Test',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
        })

        self.assertEqual(len(nurse.group_ids), 1)
        self.assertIn(self.group_nurse, nurse.group_ids)

    def test_receptionist_employee_creates_with_group(self):
        """Test that receptionist employee is associated with receptionist group"""
        receptionist = self.HrEmployee.create({
            'name': 'Receptionist Permission Test',
            'company_id': self.company.id,
            'medical_employee_type': 'receptionist',
        })

        self.assertEqual(len(receptionist.group_ids), 1)
        self.assertIn(self.group_receptionist, receptionist.group_ids)

    def test_sales_employee_creates_with_group(self):
        """Test that sales employee is associated with sales group"""
        sales = self.HrEmployee.create({
            'name': 'Sales Permission Test',
            'company_id': self.company.id,
            'medical_employee_type': 'sales',
        })

        self.assertEqual(len(sales.group_ids), 1)
        self.assertIn(self.group_sales, sales.group_ids)

    def test_employee_without_type_has_no_medical_group(self):
        """Test that employee without medical type has no medical groups"""
        employee = self.HrEmployee.create({
            'name': 'Regular Employee',
            'company_id': self.company.id,
        })

        self.assertEqual(len(employee.group_ids), 0)

    def test_group_change_on_type_change(self):
        """Test that group changes when employee type changes"""
        employee = self.HrEmployee.create({
            'name': 'Multi-Role Employee',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        self.assertIn(self.group_doctor, employee.group_ids)

        # Change to nurse
        employee.medical_employee_type = 'nurse'
        self.assertIn(self.group_nurse, employee.group_ids)
        self.assertNotIn(self.group_doctor, employee.group_ids)

    def test_acl_exists_for_employees(self):
        """Test that ACL records exist for employee access"""
        # Check that ACL for doctor exists
        acl_doctor = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('group_id', '=', self.group_doctor.id),
        ])
        self.assertTrue(len(acl_doctor) > 0)

        # Check that ACL for nurse exists
        acl_nurse = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('group_id', '=', self.group_nurse.id),
        ])
        self.assertTrue(len(acl_nurse) > 0)

    def test_record_rules_exist(self):
        """Test that record rules exist for employee access"""
        # Check if record rules are defined
        rules = self.env['ir.rule'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('groups', 'in', self.group_doctor.id),
        ])
        # At least one rule should exist for doctor
        self.assertTrue(len(rules) > 0)

    def test_hr_manager_can_edit_employees(self):
        """Test that HR manager group has edit permissions"""
        acl = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('group_id', '=', self.group_hr_manager.id),
        ])

        # HR manager should have write permission
        hr_manager_acl = acl.filtered(lambda a: a.perm_write)
        self.assertTrue(len(hr_manager_acl) > 0)

    def test_doctor_cannot_edit_employees(self):
        """Test that doctor group has read-only permission on employees"""
        acl = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('group_id', '=', self.group_doctor.id),
        ])

        # Doctor should have read but not write permission
        self.assertTrue(any(a.perm_read for a in acl))
        self.assertFalse(any(a.perm_write for a in acl))

    def test_multiple_employees_same_type(self):
        """Test that multiple employees can have the same type"""
        doctor1 = self.HrEmployee.create({
            'name': 'Dr. First',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        doctor2 = self.HrEmployee.create({
            'name': 'Dr. Second',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        self.assertEqual(doctor1.medical_employee_type, doctor2.medical_employee_type)
        self.assertIn(self.group_doctor, doctor1.group_ids)
        self.assertIn(self.group_doctor, doctor2.group_ids)

    def test_medical_manager_assigns_manager_group(self):
        """Test that setting is_medical_manager assigns the corresponding head/manager group"""
        doc_mgr = self.HrEmployee.create({
            'name': 'Dr. Chief of Medicine',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
            'is_medical_manager': True,
        })
        self.assertEqual(len(doc_mgr.group_ids), 1)
        self.assertIn(self.group_doctor_manager, doc_mgr.group_ids)

        nurse_mgr = self.HrEmployee.create({
            'name': 'Head Nurse Florence',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
            'is_medical_manager': True,
        })
        self.assertEqual(len(nurse_mgr.group_ids), 1)
        self.assertIn(self.group_nurse_manager, nurse_mgr.group_ids)

        sales_mgr = self.HrEmployee.create({
            'name': 'Sales Director Bob',
            'company_id': self.company.id,
            'medical_employee_type': 'sales',
            'is_medical_manager': True,
        })
        self.assertEqual(len(sales_mgr.group_ids), 1)
        self.assertIn(self.group_sales_manager, sales_mgr.group_ids)

    def test_medical_manager_group_inheritance(self):
        """Test that manager groups inherit from their respective base staff groups"""
        self.assertIn(self.group_doctor, self.group_doctor_manager.trans_implied_ids)
        self.assertIn(self.group_nurse, self.group_nurse_manager.trans_implied_ids)
        self.assertIn(self.group_receptionist, self.group_receptionist_manager.trans_implied_ids)
        self.assertIn(self.group_sales, self.group_sales_manager.trans_implied_ids)

    def test_admin_inherits_all_manager_groups(self):
        """Test that system administrator inherits all manager and base roles with full override"""
        admin_group = self.env.ref('base.group_system')
        self.assertIn(self.group_doctor_manager, admin_group.trans_implied_ids)
        self.assertIn(self.group_nurse_manager, admin_group.trans_implied_ids)
        self.assertIn(self.group_receptionist_manager, admin_group.trans_implied_ids)
        self.assertIn(self.group_sales_manager, admin_group.trans_implied_ids)
