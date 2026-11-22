# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestMedicalService(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_model = cls.env['medical.service']

    def test_service_creation_and_pricing(self):
        """Test creating a medical service with pricing and discount calculation"""
        service = self.service_model.create({
            'name': 'Dermatology Consultation',
            'code': 'TEST-DERM-01',
            'price': 200.0,
            'discount': 25.0,  # 25% discount
            'duration': 0.75,   # 45 minutes
            'period_between_sessions': 14,
            'active': True,
        })

        self.assertEqual(service.price, 200.0)
        self.assertEqual(service.discount, 25.0)
        # Net price should be 200 * (1 - 0.25) = 150.0
        self.assertAlmostEqual(service.final_price, 150.0)
        self.assertEqual(service.duration_minutes, 45)
        self.assertEqual(service.period_between_sessions, 14)
        self.assertTrue(service.active)

    def test_duration_minutes_inverse(self):
        """Test setting duration via minutes updates hours"""
        service = self.service_model.create({
            'name': 'Physiotherapy',
            'code': 'TEST-PHYS-01',
            'price': 100.0,
            'duration_minutes': 60,
        })
        self.assertAlmostEqual(service.duration, 1.0)

    def test_invalid_price_constraint(self):
        """Negative price should raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.service_model.create({
                'name': 'Invalid Price Service',
                'price': -50.0,
            })

    def test_invalid_discount_constraint(self):
        """Discount outside 0-100 should raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.service_model.create({
                'name': 'Invalid Discount Service',
                'price': 100.0,
                'discount': 120.0,
            })

    def test_invalid_period_between_sessions(self):
        """Negative period between sessions should raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.service_model.create({
                'name': 'Negative Interval Service',
                'price': 100.0,
                'period_between_sessions': -5,
            })
