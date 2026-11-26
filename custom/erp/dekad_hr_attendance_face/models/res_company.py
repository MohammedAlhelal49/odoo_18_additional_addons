from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..lib import engine, liveness


class ResCompany(models.Model):
    _inherit = 'res.company'

    face_kiosk_enabled = fields.Boolean(string="Face Recognition in Kiosk")
    face_mobile_enabled = fields.Boolean(string="Face Recognition on Personal Devices")
    face_only = fields.Boolean(
        string="Face Only",
        help="When face recognition is enabled for a channel, the server rejects the other "
             "check-in methods of that channel (badge and manual selection in the kiosk, "
             "the systray button for personal devices).")
    face_match_threshold = fields.Float(string="Similarity Threshold", default=0.40, digits=(3, 3))
    face_match_margin = fields.Float(string="Minimum Margin", default=0.06, digits=(3, 3))
    # Additional checkers register in lib/liveness.py and extend this field with selection_add.
    face_liveness_method = fields.Selection(
        [(liveness.HeadTurnLiveness.code, "Head turn challenge")],
        string="Liveness Check", default='head_turn', required=True)
    face_frame_count = fields.Integer(string="Frames per Attempt", default=5)
    face_nonce_ttl = fields.Integer(string="Challenge Validity (seconds)", default=60)
    face_max_challenges = fields.Integer(string="Max Challenges per IP", default=30)
    face_max_failures_ip = fields.Integer(string="Max Failures per IP", default=20)
    face_max_failures_kiosk = fields.Integer(string="Max Failures per Kiosk", default=60)
    face_max_failures_user = fields.Integer(string="Max Failures per User", default=5)
    face_rate_window = fields.Integer(string="Rate Limit Window (minutes)", default=15)
    face_lockout_minutes = fields.Integer(string="Lockout Duration (minutes)", default=15)
    face_store_photo = fields.Boolean(string="Store Check-in Photo")
    face_photo_retention_days = fields.Integer(string="Photo Retention (days)", default=30)
    face_require_geolocation = fields.Boolean(string="Require Geolocation on Personal Devices", default=True)

    @api.constrains('face_kiosk_enabled', 'face_mobile_enabled')
    def _check_face_engine_available(self):
        if any(c.face_kiosk_enabled or c.face_mobile_enabled for c in self) and engine.status() != engine.STATUS_OK:
            raise ValidationError(_(
                "Face recognition cannot be enabled: the face engine is not available on this server (%s).",
                engine.status()))

    @api.constrains(
        'face_match_threshold', 'face_match_margin', 'face_frame_count', 'face_nonce_ttl',
        'face_max_challenges', 'face_max_failures_ip', 'face_max_failures_kiosk', 'face_max_failures_user',
        'face_rate_window', 'face_lockout_minutes', 'face_photo_retention_days')
    def _check_face_parameters(self):
        for company in self:
            if not 0.2 <= company.face_match_threshold <= 0.95:
                raise ValidationError(_("The similarity threshold must be between 0.20 and 0.95."))
            if not 0.0 <= company.face_match_margin <= 0.5:
                raise ValidationError(_("The minimum margin must be between 0 and 0.5."))
            if not 3 <= company.face_frame_count <= 8:
                raise ValidationError(_("The number of frames per attempt must be between 3 and 8."))
            if not 15 <= company.face_nonce_ttl <= 300:
                raise ValidationError(_("The challenge validity must be between 15 and 300 seconds."))
            if min(company.face_max_challenges, company.face_max_failures_ip, company.face_max_failures_kiosk,
                   company.face_max_failures_user, company.face_rate_window, company.face_lockout_minutes,
                   company.face_photo_retention_days) < 1:
                raise ValidationError(_("Rate limits, durations and the photo retention must be positive."))
