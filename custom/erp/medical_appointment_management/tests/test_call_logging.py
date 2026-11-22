# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestCallLogging(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Test Lead for Call Logging',
            'contact_name': 'Sarah Jenkins',
            'phone': '+971501234567',
            'source_type': 'paid',
            'source_platform': 'facebook',
            'campaign_name': 'Ramadan Health Campaign',
        })

    def test_log_call_no_answer_creates_activity(self):
        """No Answer outcome requires next_followup_date and auto-creates a call activity"""
        followup_date = date.today() + timedelta(days=2)

        # Missing followup date should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['crm.lead.call_log'].create({
                'lead_id': self.lead.id,
                'outcome': 'no_answer',
                'notes': 'Customer did not pick up phone',
            })

        # With followup date, should succeed and create activity
        call_log = self.env['crm.lead.call_log'].create({
            'lead_id': self.lead.id,
            'outcome': 'no_answer',
            'next_followup_date': followup_date,
            'notes': 'Customer did not answer, will call back in 2 days',
        })

        self.assertEqual(call_log.outcome, 'no_answer')
        self.assertTrue(call_log.activity_id, "Activity should be auto-created on lead")
        self.assertEqual(call_log.activity_id.date_deadline, followup_date)
        self.assertEqual(self.lead.next_followup_date, followup_date)
        self.assertIn(call_log, self.lead.call_log_ids)
        self.assertEqual(self.lead.call_log_count, 1)

    def test_log_call_contacted_no_mandatory_followup(self):
        """Contacted outcome should save without requiring next_followup_date"""
        call_log = self.env['crm.lead.call_log'].create({
            'lead_id': self.lead.id,
            'outcome': 'contacted',
            'notes': 'Spoke with Sarah, interested in consultation',
        })

        self.assertEqual(call_log.outcome, 'contacted')
        self.assertFalse(call_log.activity_id)

    def test_log_call_wizard(self):
        """Test wizard for logging call"""
        followup_date = date.today() + timedelta(days=3)
        wizard = self.env['crm.lead.log.call.wizard'].create({
            'lead_id': self.lead.id,
            'outcome': 'followup_required',
            'next_followup_date': followup_date,
            'notes': 'Customer requested to call back next Tuesday',
        })
        wizard.action_save_call_log()

        latest_log = self.env['crm.lead.call_log'].search([('lead_id', '=', self.lead.id)], order='id desc', limit=1)
        self.assertEqual(latest_log.outcome, 'followup_required')
        self.assertEqual(latest_log.next_followup_date, followup_date)
