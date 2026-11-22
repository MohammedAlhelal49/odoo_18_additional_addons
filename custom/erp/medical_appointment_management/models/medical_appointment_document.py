from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalAppointmentDocument(models.Model):
    _name = 'medical.appointment.document'
    _description = 'Appointment Document'
    _order = 'create_date DESC'

    DOCUMENT_TYPES = [
        ('prescription', 'Prescription'),
        ('lab_report', 'Lab Report'),
        ('medical_report', 'Medical Report'),
        ('certificate', 'Medical Certificate'),
        ('form', 'Medical Form'),
        ('other', 'Other'),
    ]

    # Core Fields
    appointment_id = fields.Many2one(
        'medical.appointment',
        string='Appointment',
        required=True,
        ondelete='cascade',
        tracking=True,
    )

    name = fields.Char(
        string='Document Name',
        required=True,
        tracking=True,
    )

    document_type = fields.Selection(
        DOCUMENT_TYPES,
        string='Document Type',
        required=True,
        tracking=True,
    )

    description = fields.Text(
        string='Description',
        help='Additional notes about the document',
    )

    document = fields.Binary(
        string='Document File',
        required=True,
        help='Upload the document file',
    )

    filename = fields.Char(
        string='Filename',
        help='Name of the uploaded file',
    )

    # Tracking
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
    )

    create_date = fields.Datetime(
        string='Created Date',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        # Auto-set created_by
        if 'created_by' not in vals:
            vals['created_by'] = self.env.user.id
        return super().create(vals)
