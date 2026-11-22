from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestEmployeeTypes(TransactionCase):
    """Test medical center employee types and classifications"""

    def setUp(self):
        super().setUp()
        self.HrEmployee = self.env['hr.employee']
        self.ResUsers = self.env['res.users']
        self.ResCompany = self.env['res.company']

        self.company = self.env.company

    def test_create_doctor_employee(self):
        """Test creating an employee with Doctor role"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Ahmed Hassan',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
            'medical_specialization': 'Cardiology',
            'is_appointment_provider': True,
            'working_hours_per_week': 40.0,
        })

        self.assertEqual(doctor.medical_employee_type, 'doctor')
        self.assertEqual(doctor.medical_specialization, 'Cardiology')
        self.assertTrue(doctor.is_appointment_provider)

    def test_create_nurse_employee(self):
        """Test creating an employee with Nurse role"""
        nurse = self.HrEmployee.create({
            'name': 'Nurse Fatima',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
            'is_appointment_provider': False,
            'working_hours_per_week': 40.0,
        })

        self.assertEqual(nurse.medical_employee_type, 'nurse')
        self.assertFalse(nurse.is_appointment_provider)

    def test_create_receptionist_employee(self):
        """Test creating an employee with Receptionist role"""
        receptionist = self.HrEmployee.create({
            'name': 'Reception Maryam',
            'company_id': self.company.id,
            'medical_employee_type': 'receptionist',
            'is_appointment_provider': False,
            'working_hours_per_week': 40.0,
        })

        self.assertEqual(receptionist.medical_employee_type, 'receptionist')
        self.assertFalse(receptionist.is_appointment_provider)

    def test_create_sales_employee(self):
        """Test creating an employee with Sales role"""
        sales = self.HrEmployee.create({
            'name': 'Sales Representative Ali',
            'company_id': self.company.id,
            'medical_employee_type': 'sales',
            'is_appointment_provider': False,
            'working_hours_per_week': 40.0,
        })

        self.assertEqual(sales.medical_employee_type, 'sales')
        self.assertFalse(sales.is_appointment_provider)

    def test_appointment_provider_only_for_doctors(self):
        """Test that only doctors can be appointment providers"""
        nurse = self.HrEmployee.create({
            'name': 'Test Nurse',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
        })

        # Try to set is_appointment_provider for non-doctor
        with self.assertRaises(ValidationError):
            nurse.is_appointment_provider = True
            nurse.save()

    def test_specialization_only_for_doctors(self):
        """Test that specialization should only be set for doctors"""
        nurse = self.HrEmployee.create({
            'name': 'Test Nurse',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
        })

        # Try to set specialization for non-doctor
        with self.assertRaises(ValidationError):
            nurse.medical_specialization = 'Pediatrics'
            nurse.save()

    def test_change_employee_type_doctor_to_nurse(self):
        """Test changing employee type from doctor to nurse"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
            'is_appointment_provider': True,
        })

        # Change to nurse
        doctor.medical_employee_type = 'nurse'
        doctor.is_appointment_provider = False
        doctor.save()

        self.assertEqual(doctor.medical_employee_type, 'nurse')
        self.assertFalse(doctor.is_appointment_provider)
        self.assertIsNotNone(doctor.medical_type_change_date)
        self.assertIsNotNone(doctor.medical_type_changed_by_id)

    def test_on_change_medical_employee_type(self):
        """Test onchange handler for medical_employee_type"""
        doctor = self.HrEmployee.new({
            'name': 'Dr. Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        doctor._onchange_medical_employee_type()
        self.assertTrue(doctor.is_appointment_provider)

        # Change to nurse
        nurse = self.HrEmployee.new({
            'name': 'Nurse Test',
            'company_id': self.company.id,
            'medical_employee_type': 'nurse',
        })

        nurse._onchange_medical_employee_type()
        self.assertFalse(nurse.is_appointment_provider)

    def test_employee_without_medical_type(self):
        """Test creating employee without medical type (standard employee)"""
        employee = self.HrEmployee.create({
            'name': 'Regular Employee',
            'company_id': self.company.id,
            'working_hours_per_week': 40.0,
        })

        self.assertFalse(employee.medical_employee_type)
        self.assertFalse(employee.is_appointment_provider)

    def test_get_medical_employee_type_display(self):
        """Test getting display name for medical employee type"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Display Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        display_name = doctor.get_medical_employee_type_display()
        self.assertEqual(display_name, 'Doctor')

    def test_quick_action_make_doctor(self):
        """Test quick action button to make doctor"""
        employee = self.HrEmployee.create({
            'name': 'Employee',
            'company_id': self.company.id,
        })

        employee.action_make_doctor()
        self.assertEqual(employee.medical_employee_type, 'doctor')
        self.assertTrue(employee.is_appointment_provider)

    def test_quick_action_make_nurse(self):
        """Test quick action button to make nurse"""
        employee = self.HrEmployee.create({
            'name': 'Employee',
            'company_id': self.company.id,
        })

        employee.action_make_nurse()
        self.assertEqual(employee.medical_employee_type, 'nurse')
        self.assertFalse(employee.is_appointment_provider)

    def test_quick_action_make_receptionist(self):
        """Test quick action button to make receptionist"""
        employee = self.HrEmployee.create({
            'name': 'Employee',
            'company_id': self.company.id,
        })

        employee.action_make_receptionist()
        self.assertEqual(employee.medical_employee_type, 'receptionist')
        self.assertFalse(employee.is_appointment_provider)

    def test_quick_action_make_sales(self):
        """Test quick action button to make sales employee"""
        employee = self.HrEmployee.create({
            'name': 'Employee',
            'company_id': self.company.id,
        })

        employee.action_make_sales()
        self.assertEqual(employee.medical_employee_type, 'sales')
        self.assertFalse(employee.is_appointment_provider)

    def test_activity_logged_on_creation(self):
        """Test that role assignment is logged as activity"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Activity Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        # Check that a message was posted
        messages = doctor.message_ids.filtered(
            lambda m: 'role assigned' in m.body.lower() or 'Medical center role' in m.body
        )
        self.assertTrue(len(messages) > 0)

    def test_activity_logged_on_type_change(self):
        """Test that role change is logged as activity"""
        doctor = self.HrEmployee.create({
            'name': 'Dr. Change Test',
            'company_id': self.company.id,
            'medical_employee_type': 'doctor',
        })

        # Clear messages
        doctor.message_ids.unlink()

        # Change type
        doctor.medical_employee_type = 'nurse'
        doctor.save()

        # Check for change message
        messages = doctor.message_ids.filtered(
            lambda m: 'role changed' in m.body.lower() or 'Doctor' in m.body
        )
        self.assertTrue(len(messages) > 0)
