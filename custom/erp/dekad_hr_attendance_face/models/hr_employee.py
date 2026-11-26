from odoo import _, fields, models
from odoo.exceptions import AccessError

MANAGER_GROUP = 'hr_attendance.group_hr_attendance_manager'


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    face_enrolled = fields.Boolean(
        string="Face Enrolled", compute='_compute_face_enrolled', groups=MANAGER_GROUP)

    def _compute_face_enrolled(self):
        enrolled = set(self.env['hr.face.profile'].search(
            [('employee_id', 'in', self.ids), ('sample_ids', '!=', False)]).employee_id.ids)
        for employee in self:
            employee.face_enrolled = employee.id in enrolled

    def write(self, vals):
        res = super().write(vals)
        if 'active' in vals and not vals['active']:
            self._face_purge()
        return res

    def _face_purge(self):
        # sudo: biometric data must be removed even when the user archiving the
        # employee (e.g. an HR officer) has no access to the face models.
        self.env['hr.face.profile'].sudo().search([('employee_id', 'in', self.ids)]).unlink()

    def action_open_face_enrollment(self):
        self.ensure_one()
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError(_("Only Attendance administrators can enroll faces."))
        return {
            'type': 'ir.actions.client',
            'tag': 'dekad_face_enrollment',
            'name': _("Face Enrollment"),
            'params': {'employee_id': self.id, 'employee_name': self.name},
            'target': 'current',
        }

    def action_face_delete_data(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError(_("Only Attendance administrators can delete face data."))
        self.env['hr.face.profile'].search([('employee_id', 'in', self.ids)]).unlink()
        return True
