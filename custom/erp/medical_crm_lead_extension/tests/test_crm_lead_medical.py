from odoo.tests import TransactionCase


class TestCrmLeadMedical(TransactionCase):
    """Test cases for Medical CRM Lead Extension"""

    def setUp(self):
        super().setUp()
        self.CrmLead = self.env['crm.lead']
        self.Company = self.env['res.company']
        self.Country = self.env['res.country']

    def test_lead_creation_with_medical_fields(self):
        """Test creating a lead with medical fields"""
        lead = self.CrmLead.create({
            'name': 'Test Medical Lead',
            'type': 'lead',
            'medical_service': 'Cardiology Consultation',
            'source_type': 'paid',
            'source_platform': 'facebook',
            'phone': '+1234567890',
        })

        self.assertEqual(lead.medical_service, 'Cardiology Consultation')
        self.assertEqual(lead.source_type, 'paid')
        self.assertEqual(lead.source_platform, 'facebook')
        self.assertIsNotNone(lead.lead_received_date)

    def test_duplicate_phone_detection(self):
        """Test duplicate phone number detection"""
        # Create first lead
        lead1 = self.CrmLead.create({
            'name': 'Lead 1',
            'type': 'lead',
            'phone': '+1-234-567-8900',
        })

        # Create second lead with similar phone number
        lead2 = self.CrmLead.create({
            'name': 'Lead 2',
            'type': 'lead',
            'phone': '+12345678900',  # Same number, different format
        })

        # Check if duplicate warning is triggered
        duplicates = lead2._find_duplicate_leads(lead2)
        self.assertEqual(len(duplicates), 1)
        self.assertIn(lead1, duplicates)

    def test_expected_revenue_validation(self):
        """Test that expected revenue must be non-negative"""
        with self.assertRaises(Exception):
            self.CrmLead.create({
                'name': 'Test Lead',
                'type': 'lead',
                'expected_revenue': -100.0,
            })

    def test_lead_received_date_default(self):
        """Test that lead_received_date is set by default"""
        lead = self.CrmLead.create({
            'name': 'Test Lead',
            'type': 'lead',
        })

        self.assertIsNotNone(lead.lead_received_date)

    def test_date_deadline_consistency(self):
        """Test that deadline cannot be before lead_received_date"""
        from datetime import datetime, timedelta

        received_date = datetime.now()
        deadline_date = received_date - timedelta(days=1)

        with self.assertRaises(Exception):
            self.CrmLead.create({
                'name': 'Test Lead',
                'type': 'lead',
                'lead_received_date': received_date,
                'date_deadline': deadline_date.date(),
            })

    def test_source_type_and_platform_consistency(self):
        """Test source type and platform consistency warnings"""
        # This should log a warning but not fail
        lead = self.CrmLead.create({
            'name': 'Test Lead',
            'type': 'lead',
            'source_type': 'organic',
            'source_platform': 'offline',  # Inconsistent
        })

        self.assertEqual(lead.source_type, 'organic')
        self.assertEqual(lead.source_platform, 'offline')

    def test_lead_partner_relationship(self):
        """Test that leads can be linked to partners"""
        Partner = self.env['res.partner']

        partner = Partner.create({
            'name': 'Test Partner',
            'email': 'partner@example.com',
        })

        lead = self.CrmLead.create({
            'name': 'Test Lead',
            'type': 'lead',
            'partner_id': partner.id,
        })

        self.assertEqual(lead.partner_id, partner)

    def test_medical_consent_fields(self):
        """Test medical consent tracking"""
        lead = self.CrmLead.create({
            'name': 'Test Lead',
            'type': 'lead',
            'contact_consent': True,
            'data_processing_consent': False,
        })

        self.assertTrue(lead.contact_consent)
        self.assertFalse(lead.data_processing_consent)

    def test_nationality_and_country_fields(self):
        """Test nationality and country fields"""
        Country = self.env['res.country']
        usa = Country.search([('code', '=', 'US')], limit=1)

        if usa:
            lead = self.CrmLead.create({
                'name': 'Test Lead',
                'type': 'lead',
                'country_id': usa.id,
                'nationality_id': usa.id,
            })

            self.assertEqual(lead.country_id, usa)
            self.assertEqual(lead.nationality_id, usa)
