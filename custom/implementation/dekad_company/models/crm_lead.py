from odoo import models, fields, api
from datetime import timedelta


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    dekad_request_type = fields.Char(string='Request Type')
    dekad_industry = fields.Char(string='Company Field / Industry')
    dekad_employees = fields.Integer(string='Number of Employees')
    dekad_demo_date = fields.Datetime(string='Preferred Demo Date & Time')

    inactive_days = fields.Integer(
        string="Inactive (Days)",
        search='_search_inactive_days',
        store=False,
        help="Search for leads untouched for a specific number of days."
    )

    def _search_inactive_days(self, operator, value):
        # Gracefully handle invalid inputs from the search bar
        try:
            days = int(value)
        except ValueError:
            return []

        # Prevent SQL injection on the operator
        valid_operators = ['=', '!=', '>', '>=', '<', '<=']
        if operator not in valid_operators:
            return []

        # Calculate the days since the latest activity, message, or creation date
        query = f"""
                SELECT cl.id
                FROM crm_lead cl
                LEFT JOIN (
                    SELECT res_id, MAX(date) as max_msg_date
                    FROM mail_message
                    WHERE model = 'crm.lead'
                    GROUP BY res_id
                ) msg ON msg.res_id = cl.id
                LEFT JOIN (
                    SELECT res_id, MAX(create_date) as max_act_date
                    FROM mail_activity
                    WHERE res_model = 'crm.lead'
                    GROUP BY res_id
                ) act ON act.res_id = cl.id
                WHERE EXTRACT(DAY FROM (NOW() AT TIME ZONE 'UTC' - GREATEST(
                    cl.create_date,
                    COALESCE(msg.max_msg_date, '1970-01-01'::timestamp),
                    COALESCE(act.max_act_date, '1970-01-01'::timestamp)
                ))) {operator} %s
            """

        self.env.cr.execute(query, (days,))
        result = self.env.cr.fetchall()
        lead_ids = [r[0] for r in result]

        # Return standard Odoo domain syntax
        return [('id', 'in', lead_ids)]

    @api.model
    def _cron_check_inactive_leads(self):
        # Find companies that have configured users AND a valid inactivity period
        companies = self.env['res.company'].search([
            ('crm_reminder_user_ids', '!=', False),
            ('crm_inactivity_days', '>', 0)
        ])
        if not companies:
            return

        for company in companies:
            users_to_notify = company.crm_reminder_user_ids
            inactivity_days = company.crm_inactivity_days

            # Dynamically calculate the date threshold per company
            threshold_date = fields.Datetime.now() - timedelta(days=inactivity_days)

            # Fetch open leads for this company
            leads = self.search([
                ('company_id', 'in', [company.id, False]),
                ('active', '=', True),
                ('probability', '<', 100),
                ('type', '=', 'lead')
            ])

            if not leads:
                continue

            leads_tuple = tuple(leads.ids)

            # Optimized SQL fetch for latest message dates
            self.env.cr.execute("""
                        SELECT res_id, MAX(date) 
                        FROM mail_message 
                        WHERE model = 'crm.lead' AND res_id IN %s 
                        GROUP BY res_id
                    """, (leads_tuple,))
            msg_dates = dict(self.env.cr.fetchall())

            # Optimized SQL fetch for latest activity dates
            self.env.cr.execute("""
                        SELECT res_id, MAX(create_date) 
                        FROM mail_activity 
                        WHERE res_model = 'crm.lead' AND res_id IN %s 
                        GROUP BY res_id
                    """, (leads_tuple,))
            act_dates = dict(self.env.cr.fetchall())

            for lead in leads:
                last_msg_date = msg_dates.get(lead.id, lead.create_date)
                last_act_date = act_dates.get(lead.id, lead.create_date)

                last_attention = max(last_msg_date, last_act_date, lead.create_date)

                if last_attention < threshold_date:
                    # Verify an open reminder doesn't already exist
                    existing_reminder = self.env['mail.activity'].search_count([
                        ('res_model', '=', 'crm.lead'),
                        ('res_id', '=', lead.id),
                        ('summary', '=', 'Inactivity Reminder')
                    ])

                    if existing_reminder == 0:
                        # Dynamic message based on configured days
                        note_text = f'This lead has not received attention (messages, notes, or activities) in over {inactivity_days} days.'

                        for user in users_to_notify:
                            lead.activity_schedule(
                                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                                summary='Inactivity Reminder',
                                note=note_text,
                                user_id=user.id
                            )
