from odoo import _, api, fields, models

from ..lib import engine


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    face_kiosk_enabled = fields.Boolean(related='company_id.face_kiosk_enabled', readonly=False)
    face_mobile_enabled = fields.Boolean(related='company_id.face_mobile_enabled', readonly=False)
    face_only = fields.Boolean(related='company_id.face_only', readonly=False)
    face_match_threshold = fields.Float(related='company_id.face_match_threshold', readonly=False)
    face_match_margin = fields.Float(related='company_id.face_match_margin', readonly=False)
    face_liveness_method = fields.Selection(related='company_id.face_liveness_method', readonly=False)
    face_frame_count = fields.Integer(related='company_id.face_frame_count', readonly=False)
    face_nonce_ttl = fields.Integer(related='company_id.face_nonce_ttl', readonly=False)
    face_max_challenges = fields.Integer(related='company_id.face_max_challenges', readonly=False)
    face_max_failures_ip = fields.Integer(related='company_id.face_max_failures_ip', readonly=False)
    face_max_failures_kiosk = fields.Integer(related='company_id.face_max_failures_kiosk', readonly=False)
    face_max_failures_user = fields.Integer(related='company_id.face_max_failures_user', readonly=False)
    face_rate_window = fields.Integer(related='company_id.face_rate_window', readonly=False)
    face_lockout_minutes = fields.Integer(related='company_id.face_lockout_minutes', readonly=False)
    face_store_photo = fields.Boolean(related='company_id.face_store_photo', readonly=False)
    face_photo_retention_days = fields.Integer(related='company_id.face_photo_retention_days', readonly=False)
    face_require_geolocation = fields.Boolean(related='company_id.face_require_geolocation', readonly=False)

    face_engine_ok = fields.Boolean(compute='_compute_face_engine')
    face_engine_message = fields.Char(compute='_compute_face_engine')

    @api.depends('company_id')
    def _compute_face_engine(self):
        status = engine.status()
        messages = {
            engine.STATUS_OK: _("The face recognition engine is ready."),
            engine.STATUS_MISSING_LIBS: _(
                "Face recognition is unavailable: the Python packages opencv-python-headless and numpy "
                "are not installed on the server. See the module README."),
            engine.STATUS_MISSING_MODEL: _(
                "Face recognition is unavailable: the model files are missing from the module's "
                "face_models folder."),
            engine.STATUS_CHECKSUM: _(
                "Face recognition is unavailable: a model file does not match its expected checksum."),
            engine.STATUS_LOAD_ERROR: _(
                "Face recognition is unavailable: the models could not be loaded. Check the server log."),
        }
        for settings in self:
            settings.face_engine_ok = status == engine.STATUS_OK
            settings.face_engine_message = messages.get(status, status)
