from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase

class TestFcmDevice(TransactionCase):

    def setUp(self):
        super(TestFcmDevice, self).setUp()
        self.Partner = self.env['res.partner']
        self.FcmDevice = self.env['fcm.device']
        self.FcmNotification = self.env['fcm.notification']

    def test_fcm_device_creation(self):
        """Test creating an FCM device record."""
        partner = self.Partner.create({'name': 'Test Partner'})
        device = self.FcmDevice.create({
            'partner_id': partner.id,
            'token': 'test_token_123',
            'device_type': 'android'
        })
        self.assertEqual(device.token, 'test_token_123')
        self.assertEqual(device.partner_id, partner)

    def test_fcm_token_uniqueness(self):
        """Test that FCM tokens must be unique per server URL."""
        partner = self.Partner.create({'name': 'Test Partner'})
        self.FcmDevice.create({
            'partner_id': partner.id,
            'token': 'duplicate_token',
            'server_url': 'https://example.com'
        })
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.FcmDevice.create({
                    'partner_id': partner.id,
                    'token': 'duplicate_token',
                    'server_url': 'https://example.com'
                })

    def test_notification_is_read_and_expiration(self):
        """Test default is_read ('notread') and automatic expiration_date calculation (30 days default)."""
        partner = self.Partner.create({'name': 'Notification User'})
        notification = self.FcmNotification.create({
            'partner_id': partner.id,
            'title': 'Test Title',
            'body': 'Test Body',
        })
        self.assertEqual(notification.is_read, 'notread', "Default is_read must be 'notread'")
        self.assertIsNotNone(notification.expiration_date, "expiration_date should be automatically calculated")
        
        # Verify default store duration is 30 days
        expected_expiry = notification.create_date + timedelta(days=30)
        delta_seconds = abs((notification.expiration_date - expected_expiry).total_seconds())
        self.assertLess(delta_seconds, 5, "Default retention date should be create_date + 30 days")

        # Test mark as read / not read actions
        notification.action_mark_as_read()
        self.assertEqual(notification.is_read, 'read')
        notification.action_mark_as_not_read()
        self.assertEqual(notification.is_read, 'notread')

    def test_notification_garbage_collection(self):
        """Test deletion of expired notifications."""
        partner = self.Partner.create({'name': 'GC User'})
        now = fields.Datetime.now()

        # Expired notification (expiration date in the past)
        expired_notif = self.FcmNotification.create({
            'partner_id': partner.id,
            'title': 'Expired Notif',
            'expiration_date': now - timedelta(days=1),
        })

        # Valid notification (expiration date in the future)
        valid_notif = self.FcmNotification.create({
            'partner_id': partner.id,
            'title': 'Valid Notif',
            'expiration_date': now + timedelta(days=10),
        })

        # Run GC
        self.FcmNotification._gc_expired_notifications()

        self.assertFalse(expired_notif.exists(), "Expired notification should be deleted")
        self.assertTrue(valid_notif.exists(), "Valid notification should still exist")

    def test_retention_days_setting(self):
        """Test changing fcm_retention_days setting in res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'fcm_retention_days': 15,
        })
        settings.set_values()

        partner = self.Partner.create({'name': 'Retention User'})
        notification = self.FcmNotification.create({
            'partner_id': partner.id,
            'title': 'Custom Retention Notif',
        })

        expected_expiry = notification.create_date + timedelta(days=15)
        delta_seconds = abs((notification.expiration_date - expected_expiry).total_seconds())
        self.assertLess(delta_seconds, 5, "Retention date should follow configured retention days (15 days)")

    def test_get_notifications_date_filtering(self):
        """Test get_notifications_by_user_id with start_date and end_date filters."""
        user = self.env['res.users'].create({
            'name': 'Filter User',
            'login': 'filteruser',
            'email': 'filteruser@example.com',
        })
        
        self.FcmNotification.create({
            'partner_id': user.partner_id.id,
            'title': 'Notif 1',
            'create_date': '2026-01-10 10:00:00',
        })
        self.FcmNotification.create({
            'partner_id': user.partner_id.id,
            'title': 'Notif 2',
            'create_date': '2026-02-15 10:00:00',
        })
        self.FcmNotification.create({
            'partner_id': user.partner_id.id,
            'title': 'Notif 3',
            'create_date': '2026-03-20 10:00:00',
        })

        # 1. Null start_date and end_date -> return all
        all_notifs = self.FcmNotification.get_notifications_by_user_id(user.id, start_date=None, end_date=None)
        self.assertEqual(len(all_notifs), 3, "When date filters are null, should return all notifications")

        # 2. Filter with start_date and end_date covering February only
        feb_notifs = self.FcmNotification.get_notifications_by_user_id(user.id, start_date='2026-02-01', end_date='2026-02-28')
        self.assertEqual(len(feb_notifs), 1)
        self.assertEqual(feb_notifs[0]['title'], 'Notif 2')

        # 3. Filter with start_date only
        from_feb = self.FcmNotification.get_notifications_by_user_id(user.id, start_date='2026-02-01')
        self.assertEqual(len(from_feb), 2)
        titles = [n['title'] for n in from_feb]
        self.assertIn('Notif 2', titles)
        self.assertIn('Notif 3', titles)

    def test_skip_nested_fcm_notifications(self):
        """Test that skip_fcm_notification context flag suppresses nested notifications."""
        partner = self.Partner.create({'name': 'Nested Test Partner'})
        self.FcmDevice.create({
            'partner_id': partner.id,
            'token': 'nested_token_123',
        })
        
        initial_count = self.FcmNotification.search_count([('partner_id', '=', partner.id)])
        
        # Calling _send_fcm_common with skip_fcm_notification=True should not create any notification log
        self.env['mail.thread'].with_context(skip_fcm_notification=True)._send_fcm_common(
            partner, "Nested Title", "Nested Body", {"model": "sale.order", "res_id": "1"}
        )
        
        new_count = self.FcmNotification.search_count([('partner_id', '=', partner.id)])
        self.assertEqual(initial_count, new_count, "No notification log should be created when skip_fcm_notification context is set")

    def test_get_preferences_module_filtering(self):
        """Test that device preference initialization only targets sale, attendance, and crm modules."""
        device = self.FcmDevice.create({
            'token': 'pref_filter_token',
            'server_url': 'https://example.com'
        })
        device.action_initialize_fcm_preferences()
        pref_modules = device.fcm_addon_preference_ids.mapped('module_id.name')
        allowed_modules = {'sale', 'sale_management', 'crm', 'hr_attendance', 'attendance'}
        for mod_name in pref_modules:
            self.assertIn(mod_name, allowed_modules, f"Module {mod_name} should be in allowed preference modules")

    def test_app_version_and_config_settings(self):
        """Test reading and writing app version and mobile configuration settings."""
        settings = self.env['res.config.settings'].create({
            'fcm_app_version': '2.1.0',
            'fcm_min_app_version': '2.0.0',
            'fcm_force_update': True,
            'fcm_app_url_android': 'https://play.google.com/store/apps/details?id=com.example.app',
            'fcm_app_url_ios': 'https://apps.apple.com/app/id123456789',
            'fcm_app_config': '{"feature_flag_x": true}'
        })
        settings.set_values()

        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(params.get_param('firebaseOdooFlutter.app_version'), '2.1.0')
        self.assertEqual(params.get_param('firebaseOdooFlutter.min_app_version'), '2.0.0')
        self.assertEqual(params.get_param('firebaseOdooFlutter.force_update'), 'True')
        self.assertEqual(params.get_param('firebaseOdooFlutter.app_config'), '{"feature_flag_x": true}')

