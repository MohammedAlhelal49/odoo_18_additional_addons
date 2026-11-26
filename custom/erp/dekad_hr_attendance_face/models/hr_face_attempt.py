from odoo import fields, models

REASONS = [
    ('ok', "Recognized"),
    ('invalid_nonce', "Invalid or reused challenge"),
    ('expired_nonce', "Expired challenge"),
    ('nonce_mismatch', "Challenge issued for another kiosk or user"),
    ('locked', "Locked out"),
    ('rate_limited', "Too many challenge requests"),
    ('tampered', "Forbidden parameters sent by the client"),
    ('bad_input', "Invalid images"),
    ('no_face', "No face detected"),
    ('multiple_faces', "Multiple faces detected"),
    ('face_too_small', "Face too small"),
    ('too_fast', "Captured too fast"),
    ('no_frontal', "No frontal face"),
    ('challenge_failed', "Liveness challenge failed"),
    ('identity_changed', "Different faces across frames"),
    ('below_threshold', "Below similarity threshold"),
    ('ambiguous', "Ambiguous match"),
    ('no_gallery', "No enrolled faces"),
    ('no_employee', "User without employee"),
    ('no_location', "Location missing"),
    ('outside_geofence', "Outside the work location"),
    ('engine_unavailable', "Face engine unavailable"),
    ('attendance_error', "Attendance could not be recorded"),
    ('error', "Internal error"),
]


class HrFaceAttempt(models.Model):
    """Audit trail of face check-in attempts. Never contains images or embeddings."""

    _name = 'hr.face.attempt'
    _description = "Face Recognition Attempt"
    _order = 'attempt_date desc, id desc'
    _rec_name = 'attempt_date'

    attempt_date = fields.Datetime(string="Date", required=True, default=fields.Datetime.now, readonly=True, index=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True, index=True, ondelete='cascade')
    channel = fields.Selection([('kiosk', "Kiosk"), ('mobile', "Personal Device")], readonly=True)
    stage = fields.Selection([('challenge', "Challenge"), ('verify', "Verification")], readonly=True)
    result = fields.Selection(
        [('success', "Success"), ('failure', "Failure"), ('locked', "Locked")], readonly=True, index=True)
    reason = fields.Selection(REASONS, readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True, ondelete='set null',
                                  help="Recognized employee (kiosk) or employee of the logged-in user (personal device).")
    user_id = fields.Many2one('res.users', string="User", readonly=True, ondelete='set null')
    score = fields.Float(digits=(3, 3), readonly=True)
    second_score = fields.Float(string="Second Best Score", digits=(3, 3), readonly=True)
    attendance_id = fields.Many2one('hr.attendance', readonly=True, ondelete='set null')
    ip_address = fields.Char(string="IP Address", readonly=True)
    browser = fields.Char(readonly=True)
