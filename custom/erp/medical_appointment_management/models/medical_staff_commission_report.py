from odoo import api, fields, models, _
from datetime import datetime, timedelta


class MedicalStaffCommissionReport(models.Model):
    _name = 'medical.staff.commission.report'
    _description = 'Staff Commission Report'
    _auto = False
    _rec_name = 'employee_id'

    # Employee Info
    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    user_id = fields.Many2one('res.users', 'User', readonly=True)
    employee_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('sales', 'Sales'),
    ], 'Employee Type', readonly=True)

    # Appointment Counts
    total_appointments = fields.Integer('Total Appointments', readonly=True)
    completed_appointments = fields.Integer('Completed Appointments', readonly=True)
    cancelled_appointments = fields.Integer('Cancelled Appointments', readonly=True)

    # Financial Data
    total_revenue = fields.Monetary('Total Revenue', currency_field='company_currency_id', readonly=True)
    total_commission = fields.Monetary('Total Commission', currency_field='company_currency_id', readonly=True)
    average_commission = fields.Monetary('Avg Commission', currency_field='company_currency_id', readonly=True)

    # Time Period
    date_from = fields.Date('From Date', readonly=True)
    date_to = fields.Date('To Date', readonly=True)

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    def init(self):
        tools = __import__('odoo.tools', fromlist=['drop_view_if_exists'])
        tools.drop_view_if_exists(self.env.cr, self._table)

        query = """
            CREATE or REPLACE VIEW medical_staff_commission_report AS (
                SELECT
                    ROW_NUMBER() OVER () as id,
                    he.id as employee_id,
                    he.user_id,
                    he.medical_employee_type as employee_type,
                    COUNT(DISTINCT apt.id) as total_appointments,
                    COUNT(DISTINCT CASE WHEN apt.status = 'completed' THEN apt.id END) as completed_appointments,
                    COUNT(DISTINCT CASE WHEN apt.status = 'cancelled' THEN apt.id END) as cancelled_appointments,
                    COALESCE(SUM(CASE WHEN apt.status = 'completed' THEN apt.appointment_total ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN apt.status = 'completed' THEN apt.commission_amount ELSE 0 END), 0) as total_commission,
                    CASE
                        WHEN COUNT(DISTINCT CASE WHEN apt.status = 'completed' THEN apt.id END) > 0
                        THEN COALESCE(SUM(CASE WHEN apt.status = 'completed' THEN apt.commission_amount ELSE 0 END), 0) /
                             COUNT(DISTINCT CASE WHEN apt.status = 'completed' THEN apt.id END)
                        ELSE 0
                    END as average_commission,
                    MIN(apt.appointment_date) as date_from,
                    MAX(apt.appointment_date) as date_to,
                    he.company_id,
                    he.company_id as company_currency_id
                FROM hr_employee he
                LEFT JOIN medical_appointment apt ON (
                    (he.medical_employee_type = 'doctor' AND apt.doctor_id = he.id) OR
                    (he.medical_employee_type = 'nurse' AND apt.nurse_id = he.id) OR
                    (he.medical_employee_type = 'receptionist' AND apt.receptionist_id = he.id) OR
                    (he.medical_employee_type = 'sales' AND apt.sales_employee_id = he.id)
                )
                WHERE he.medical_employee_type IN ('doctor', 'nurse', 'receptionist', 'sales')
                GROUP BY he.id, he.user_id, he.medical_employee_type, he.company_id
            )
        """
        self.env.cr.execute(query)
