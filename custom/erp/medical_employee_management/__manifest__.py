{
    'name': 'Medical Center Employee Management',
    'version': '18.0.1.0',
    'category': 'Human Resources/Employees',
    'sequence': 26,
    'summary': 'Employee types, roles, and security for medical center',
    'description': """
Medical Center Employee Management
===================================
Implements employee management for medical centers with role-based access control.
Features:
* Four employee types: Doctor, Nurse, Receptionist, Sales Employee
* Standalone app with dedicated menus for Doctors, Nurses, Receptionists, and Sales
* Dedicated section in General Settings
* Role-specific security groups with precise permissions
* Integration with standard Odoo work schedules and calendars
* Appointment availability integrated with employee schedules
    """,
    'author': 'Medical Center',
    'website': 'https://www.medical-center.example.com',
    'images': ['static/description/icon.png'],
    'depends': [
        'hr',
        'resource',
        'calendar',
        'hr_holidays',
        'hr_attendance',
        'crm',
        'medical_crm_lead_extension',
    ],
    'data': [
        # Security - groups must be first
        'security/medical_groups.xml',
        'security/ir.model.access.csv',
        'security/medical_record_rules.xml',

        # Data
        'data/medical_employee_types.xml',

        # Views
        'views/hr_employee_medical_views.xml',
        'views/res_users_medical_views.xml',
        'views/res_groups_views.xml',
        'views/res_config_settings_views.xml',
        'views/medical_employee_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
