from odoo.tests import tagged

from .common import FaceHttpCase


@tagged('post_install', '-at_install', 'dekad_face')
class TestFaceMobile(FaceHttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a1 = cls.env['res.users'].create({
            'name': 'Face A1 User', 'login': 'face_a1', 'password': 'face_a1_pass1234',
            'company_id': cls.company_a.id, 'company_ids': [(6, 0, cls.company_a.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.emp_a1.user_id = cls.user_a1
        cls.location = cls.env['hr.work.location'].create({
            'name': 'Face HQ', 'address_id': cls.company_a.partner_id.id,
            'face_latitude': 25.2048, 'face_longitude': 55.2708, 'face_geofence_radius': 200,
        })

    def setUp(self):
        super().setUp()
        self.authenticate('face_a1', 'face_a1_pass1234')

    def my(self, route, **params):
        return self.make_jsonrpc_request(f'/dekad_face/my/{route}', params)

    def my_attempt(self, person=1, **extra):
        challenge = self.my('challenge')
        self.assertTrue(challenge.get('nonce'), challenge)
        frames = self.fake.frames_for(person, challenge['challenge'], challenge['frames'])
        return self.my('verify', nonce=challenge['nonce'], frames=frames, **extra)

    def test_config(self):
        self.assertEqual(self.my('config'), {'enabled': True, 'require_location': False, 'face_only': False})
        self.company_a.face_mobile_enabled = False
        self.assertEqual(self.my('config'), {'enabled': False})

    def test_one_to_one_success(self):
        result = self.my_attempt(person=1)
        self.assertEqual(result['id'], self.emp_a1.id)
        self.assertEqual(self.emp_a1.last_attendance_id.in_mode, 'face_mobile')
        self.assertEqual(self.attempts(result='success').user_id, self.user_a1)

    def test_other_person_rejected(self):
        # A2's face is enrolled in the same company but this is a 1:1 check against A1.
        self.assertEqual(self.my_attempt(person=2), {'error': 'not_recognized'})
        self.assertFalse(self.emp_a1.attendance_ids | self.emp_a2.attendance_ids)

    def test_client_cannot_choose_employee(self):
        self.assertEqual(self.my_attempt(person=2, employee_id=self.emp_a2.id), {'error': 'error'})
        self.assertFalse(self.emp_a2.attendance_ids)

    def test_not_enrolled(self):
        self.env['hr.face.profile'].sudo().search([('employee_id', '=', self.emp_a1.id)]).unlink()
        self.assertEqual(self.my_attempt(person=1), {'error': 'not_enrolled'})

    def test_kiosk_nonce_not_usable_on_mobile(self):
        challenge = self.make_jsonrpc_request('/dekad_face/kiosk/challenge', {'token': self.token_a})
        frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
        self.assertEqual(self.my('verify', nonce=challenge['nonce'], frames=frames), {'error': 'expired'})

    def test_geolocation_required(self):
        self.company_a.face_require_geolocation = True
        self.assertEqual(self.my_attempt(person=1), {'error': 'no_location'})
        self.assertEqual(self.my_attempt(person=1, latitude='abc', longitude=1), {'error': 'no_location'})
        self.assertTrue(self.my_attempt(person=1, latitude=25.2, longitude=55.27).get('id'))

    def test_geofence(self):
        self.emp_a1.work_location_id = self.location
        # Geofence applies even when geolocation is not globally required.
        self.assertEqual(self.my_attempt(person=1), {'error': 'no_location'})
        self.assertEqual(self.my_attempt(person=1, latitude=25.25, longitude=55.30), {'error': 'outside_geofence'})
        result = self.my_attempt(person=1, latitude=25.2050, longitude=55.2710)
        self.assertEqual(result['id'], self.emp_a1.id)
        self.assertAlmostEqual(self.emp_a1.last_attendance_id.in_latitude, 25.2050, places=4)

    def test_user_lockout(self):
        self.company_a.face_max_failures_user = 2
        for _i in range(2):
            self.my_attempt(person=2)
        self.assertEqual(self.my('challenge'), {'error': 'locked'})

    def test_face_only_blocks_systray(self):
        self.company_a.face_only = True
        self.assertEqual(self.make_jsonrpc_request('/hr_attendance/systray_check_in_out', {}), {})
        self.assertFalse(self.emp_a1.attendance_ids)
        self.company_a.face_only = False
        self.assertTrue(self.make_jsonrpc_request('/hr_attendance/systray_check_in_out', {}).get('id'))

    def test_public_cannot_use_mobile_routes(self):
        self.logout()
        with self.assertRaises(Exception):
            self.my('challenge')
