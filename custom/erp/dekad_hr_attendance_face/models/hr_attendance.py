import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MANAGER_GROUP = 'hr_attendance.group_hr_attendance_manager'
FACE_MODES = [('face_kiosk', "Face (Kiosk)"), ('face_mobile', "Face (Personal Device)")]
PHOTO_FIELDS = ('face_photo_in', 'face_photo_out')


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Extends the selections defined in hr_attendance/models/hr_attendance.py
    in_mode = fields.Selection(selection_add=FACE_MODES, ondelete={code: 'set default' for code, _l in FACE_MODES})
    out_mode = fields.Selection(selection_add=FACE_MODES, ondelete={code: 'set default' for code, _l in FACE_MODES})
    face_photo_in = fields.Image(string="Check-in Photo", max_width=320, max_height=320,
                                 attachment=True, copy=False, readonly=True, groups=MANAGER_GROUP)
    face_photo_out = fields.Image(string="Check-out Photo", max_width=320, max_height=320,
                                  attachment=True, copy=False, readonly=True, groups=MANAGER_GROUP)

    @api.model
    def _cron_face_purge_photos(self):
        """Delete check-in photos older than each company's retention period."""
        Attachment = self.env['ir.attachment'].sudo()
        for company in self.env['res.company'].sudo().search([]):
            cutoff = fields.Datetime.now() - timedelta(days=company.face_photo_retention_days or 30)
            attachments = Attachment.search([
                ('res_model', '=', 'hr.attendance'),
                ('res_field', 'in', PHOTO_FIELDS),
                ('create_date', '<', cutoff),
            ])
            if not attachments:
                continue
            attendances = self.sudo().browse(set(attachments.mapped('res_id'))).exists()
            in_company = set(attendances.filtered(lambda a: a.employee_id.company_id == company).ids)
            to_delete = attachments.filtered(lambda a: a.res_id in in_company)
            if to_delete:
                _logger.info("Purging %s face photos of company %s", len(to_delete), company.id)
                to_delete.unlink()
