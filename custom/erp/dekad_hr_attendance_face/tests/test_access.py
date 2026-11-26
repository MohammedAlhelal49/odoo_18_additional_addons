from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import FaceHttpCase


@tagged('post_install', '-at_install', 'dekad_face')
class TestFaceAccessRights(FaceHttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.new_user_cls('face_manager', 'base.group_user,hr_attendance.group_hr_attendance_manager')
        cls.officer = cls.new_user_cls('face_officer', 'base.group_user,hr_attendance.group_hr_attendance_officer')
        cls.hr_user = cls.new_user_cls('face_hr', 'base.group_user,hr.group_hr_manager')
        cls.employee_user = cls.new_user_cls('face_employee', 'base.group_user')
        cls.portal = cls.new_user_cls('face_portal', 'base.group_portal')

    @classmethod
    def new_user_cls(cls, login, groups):
        from odoo.tests import new_test_user
        return new_test_user(cls.env, login=login, groups=groups, company_id=cls.company_a.id)

    def test_manager_can_read_templates(self):
        samples = self.env['hr.face.sample'].with_user(self.manager).search([])
        self.assertTrue(samples)
        self.assertTrue(samples[0].embedding)
        # Multi-company rule: company B samples are not visible from company A only.
        self.assertNotIn(self.emp_b1, samples.employee_id)
        self.assertTrue(self.emp_a1.with_user(self.manager).face_enrolled)

    def test_non_managers_cannot_access_templates(self):
        for user in (self.officer, self.hr_user, self.employee_user, self.portal):
            for model in ('hr.face.sample', 'hr.face.profile'):
                with self.assertRaises(AccessError, msg=f"{user.login} on {model}"):
                    self.env[model].with_user(user).search([])
            with self.assertRaises(AccessError):
                self.env['hr.face.sample'].with_user(user).browse(
                    self.env['hr.face.sample'].sudo().search([], limit=1).id).read(['embedding'])

    def test_non_managers_cannot_read_audit_or_internal_models(self):
        for user in (self.officer, self.hr_user, self.employee_user, self.portal):
            for model in ('hr.face.attempt', 'hr.face.challenge', 'hr.face.throttle'):
                with self.assertRaises(AccessError, msg=f"{user.login} on {model}"):
                    self.env[model].with_user(user).search([])

    def test_face_enrolled_field_restricted(self):
        with self.assertRaises(AccessError):
            self.emp_a1.with_user(self.hr_user).read(['face_enrolled'])

    def test_photo_fields_restricted(self):
        with self.assertRaises(AccessError):
            self.env['hr.attendance'].with_user(self.officer).search([], limit=1).read(['face_photo_in'])

    def test_only_manager_enrolls(self):
        for user in (self.officer, self.hr_user, self.employee_user):
            with self.assertRaises(AccessError):
                self.env['hr.face.profile'].with_user(user).enroll_samples(self.emp_a2.id, ['x'] * 3, True)
            with self.assertRaises(AccessError):
                self.emp_a2.with_user(user).action_open_face_enrollment()

    def test_enrollment_requires_consent(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self.env['hr.face.profile'].with_user(self.manager).enroll_samples(self.emp_a2.id, ['x'] * 3, False)

    def test_templates_not_exposed_through_employee(self):
        fields = self.env['hr.employee'].with_user(self.employee_user).fields_get()
        self.assertNotIn('face_enrolled', fields)
        self.assertFalse([name for name in fields if 'embedding' in name])

    def test_archive_and_delete_purge_data(self):
        Profile = self.env['hr.face.profile'].sudo()
        # An HR officer without face access can still archive: data is purged.
        self.emp_a2.with_user(self.hr_user).action_archive()
        self.assertFalse(Profile.search([('employee_id', '=', self.emp_a2.id)]))
        # Deleting the employee cascades.
        sample_ids = Profile.search([('employee_id', '=', self.emp_b1.id)]).sample_ids.ids
        self.emp_b1.unlink()
        self.assertFalse(self.env['hr.face.sample'].sudo().browse(sample_ids).exists())

    def test_cron_purges_archived_resources(self):
        # Archiving through resource.resource bypasses hr.employee.write.
        self.emp_a1.resource_id.active = False
        self.assertFalse(self.emp_a1.active)
        Profile = self.env['hr.face.profile'].sudo()
        self.assertTrue(Profile.search([('employee_id', '=', self.emp_a1.id)]))
        Profile._cron_purge_inactive()
        self.assertFalse(Profile.search([('employee_id', '=', self.emp_a1.id)]))
