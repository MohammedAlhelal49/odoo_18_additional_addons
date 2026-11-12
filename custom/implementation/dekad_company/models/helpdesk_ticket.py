from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Contact fields
    dekad_contact_name = fields.Char(string='Contact Name')
    dekad_company_name = fields.Char(string='Company Name')
    dekad_email = fields.Char(string='Email')
    dekad_phone = fields.Char(string='Phone')

    # Custom request fields
    dekad_request_type = fields.Char(string='Request Type')
    dekad_industry = fields.Char(string='Company Field / Industry')
    dekad_employees = fields.Integer(string='Number of Employees')
    dekad_demo_date = fields.Datetime(string='Preferred Date & Time')

    # Link to the generated lead
    dekad_lead_id = fields.Many2one('crm.lead', string='Generated Lead', readonly=True, copy=False)

    # Dummy field for the search UI
    inactive_days = fields.Integer(
        string="Inactive (Days)",
        search='_search_inactive_days',
        store=False,
        help="Search for tickets untouched for a specific number of days."
    )

    def _search_inactive_days(self, operator, value):
        try:
            days = int(value)
        except ValueError:
            return []

        valid_operators = ['=', '!=', '>', '>=', '<', '<=']
        if operator not in valid_operators:
            return []

        query = f"""
            SELECT ht.id
            FROM helpdesk_ticket ht
            LEFT JOIN (
                SELECT res_id, MAX(date) as max_msg_date
                FROM mail_message
                WHERE model = 'helpdesk.ticket'
                GROUP BY res_id
            ) msg ON msg.res_id = ht.id
            LEFT JOIN (
                SELECT res_id, MAX(create_date) as max_act_date
                FROM mail_activity
                WHERE res_model = 'helpdesk.ticket'
                GROUP BY res_id
            ) act ON act.res_id = ht.id
            WHERE EXTRACT(DAY FROM (NOW() AT TIME ZONE 'UTC' - GREATEST(
                ht.create_date,
                COALESCE(msg.max_msg_date, '1970-01-01'::timestamp),
                COALESCE(act.max_act_date, '1970-01-01'::timestamp)
            ))) {operator} %s
        """

        self.env.cr.execute(query, (days,))
        result = self.env.cr.fetchall()
        ticket_ids = [r[0] for r in result]

        return [('id', 'in', ticket_ids)]

    @api.model
    def _cron_check_inactive_tickets(self):
        companies = self.env['res.company'].search([
            ('helpdesk_reminder_user_ids', '!=', False),
            ('helpdesk_inactivity_days', '>', 0)
        ])
        if not companies:
            return

        for company in companies:
            users_to_notify = company.helpdesk_reminder_user_ids
            inactivity_days = company.helpdesk_inactivity_days
            threshold_date = fields.Datetime.now() - timedelta(days=inactivity_days)

            # Fetch open tickets (ignoring closed stages) for this company
            tickets = self.search([
                ('company_id', 'in', [company.id, False]),
                ('stage_id.is_close', '=', False)
            ])

            if not tickets:
                continue

            tickets_tuple = tuple(tickets.ids)

            self.env.cr.execute("""
                SELECT res_id, MAX(date) 
                FROM mail_message 
                WHERE model = 'helpdesk.ticket' AND res_id IN %s 
                GROUP BY res_id
            """, (tickets_tuple,))
            msg_dates = dict(self.env.cr.fetchall())

            self.env.cr.execute("""
                SELECT res_id, MAX(create_date) 
                FROM mail_activity 
                WHERE res_model = 'helpdesk.ticket' AND res_id IN %s 
                GROUP BY res_id
            """, (tickets_tuple,))
            act_dates = dict(self.env.cr.fetchall())

            for ticket in tickets:
                last_msg_date = msg_dates.get(ticket.id, ticket.create_date)
                last_act_date = act_dates.get(ticket.id, ticket.create_date)

                last_attention = max(last_msg_date, last_act_date, ticket.create_date)

                if last_attention < threshold_date:
                    existing_reminder = self.env['mail.activity'].search_count([
                        ('res_model', '=', 'helpdesk.ticket'),
                        ('res_id', '=', ticket.id),
                        ('summary', '=', 'Ticket Inactivity Reminder')
                    ])

                    if existing_reminder == 0:
                        note_text = f'This ticket has not received attention in over {inactivity_days} days.'

                        for user in users_to_notify:
                            ticket.activity_schedule(
                                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                                summary='Ticket Inactivity Reminder',
                                note=note_text,
                                user_id=user.id
                            )

    def action_convert_ticket_to_lead_or_opportunity(self):
        """Creates a CRM Lead from the Ticket data."""
        self.ensure_one()

        if self.dekad_lead_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': self.dekad_lead_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        lead_vals = {
            'name': self.name,
            'contact_name': self.dekad_contact_name,
            'partner_name': self.dekad_company_name,
            'email_from': self.dekad_email,
            'phone': self.dekad_phone,
            'type': 'lead',
            'description': self.description,
            'dekad_request_type': self.dekad_request_type,
            'dekad_industry': self.dekad_industry,
            'dekad_employees': self.dekad_employees,
            'dekad_demo_date': self.dekad_demo_date,
        }

        new_lead = self.env['crm.lead'].sudo().create(lead_vals)
        self.dekad_lead_id = new_lead.id

        self.message_post(
            body=f"Converted to Lead: <a href='#' data-oe-model='crm.lead' data-oe-id='{new_lead.id}'>{new_lead.name}</a>")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': new_lead.id,
            'view_mode': 'form',
            'target': 'current',
        }
