from odoo import api, fields, models, _


class MedicalAppointmentReport(models.Model):
    _name = 'medical.appointment.report'
    _description = 'Medical Appointment Report'
    _auto = False
    _rec_name = 'appointment_id'

    # Basic Info
    appointment_id = fields.Many2one('medical.appointment', 'Appointment', readonly=True)
    name = fields.Char('Appointment ID', readonly=True)
    appointment_date = fields.Date('Appointment Date', readonly=True)
    appointment_time = fields.Float('Appointment Time', readonly=True)

    # Parties
    patient_id = fields.Many2one('res.partner', 'Patient', readonly=True)
    doctor_id = fields.Many2one('hr.employee', 'Doctor', readonly=True)
    doctor_user_id = fields.Many2one('res.users', 'Doctor User', readonly=True)
    receptionist_id = fields.Many2one('hr.employee', 'Receptionist', readonly=True)
    nurse_id = fields.Many2one('hr.employee', 'Nurse', readonly=True)
    sales_employee_id = fields.Many2one('hr.employee', 'Sales Employee', readonly=True)

    # Service & Status
    service_id = fields.Many2one('medical.service', 'Service', readonly=True)
    status = fields.Selection([
        ('tentative', 'Tentative'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('ready_for_doctor', 'Ready for Doctor'),
        ('in_consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
    ], 'Status', readonly=True)

    # Financial
    appointment_total = fields.Monetary('Total', currency_field='company_currency_id', readonly=True)
    commission_rate = fields.Float('Commission Rate (%)', readonly=True)
    commission_amount = fields.Monetary('Commission Amount', currency_field='company_currency_id', readonly=True)

    # Doctor Earning (5% of appointment total)
    doctor_commission = fields.Monetary('Doctor Earning', currency_field='company_currency_id', readonly=True)

    # Sales Commission
    sales_commission = fields.Monetary('Sales Commission', currency_field='company_currency_id', readonly=True)

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    created_date = fields.Date('Created Date', readonly=True)

    # Timestamps
    consultation_started_date = fields.Datetime('Consultation Started', readonly=True)
    consultation_completed_date = fields.Datetime('Consultation Completed', readonly=True)
    checked_in_date = fields.Datetime('Checked In', readonly=True)

    def init(self):
        tools = __import__('odoo.tools', fromlist=['drop_view_if_exists'])
        tools.drop_view_if_exists(self.env.cr, self._table)

        query = """
            CREATE or REPLACE VIEW medical_appointment_report AS (
                SELECT
                    apt.id,
                    apt.id as appointment_id,
                    apt.name,
                    apt.appointment_date,
                    apt.appointment_time,
                    apt.patient_id,
                    apt.doctor_id,
                    apt.doctor_user_id,
                    apt.receptionist_id,
                    apt.nurse_id,
                    apt.sales_employee_id,
                    apt.service_id,
                    apt.status,
                    apt.appointment_total,
                    apt.commission_rate,
                    apt.commission_amount,
                    (apt.appointment_total * 0.05) as doctor_commission,
                    (apt.appointment_total * (apt.commission_rate / 100.0)) as sales_commission,
                    apt.company_id,
                    apt.created_date,
                    apt.consultation_started_date,
                    apt.consultation_completed_date,
                    apt.checked_in_date
                FROM medical_appointment apt
            )
        """
        self.env.cr.execute(query)
