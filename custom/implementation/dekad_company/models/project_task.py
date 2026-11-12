from odoo import models, fields, api, _
from datetime import timedelta


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Contact fields to hold data before CRM conversion
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

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Ensure tasks aren't "Private" if they come from your website
        for vals in vals_list:
            if not vals.get('project_id') and vals.get('dekad_request_type'):
                # Force assign to a project to avoid "Private" status
                # You can find the ID in Project > Configuration > Projects
                vals['project_id'] = self.env['project.project'].search([('name', '=', 'Website Inquiries')],
                                                                        limit=1).id

        # 2. Create the task records
        tasks = super(ProjectTask, self).create(vals_list)

        # 3. Handle Helpdesk Ticket creation
        for task in tasks:
            if task.dekad_request_type:
                # Map ALL fields from Task to Ticket
                self.env['helpdesk.ticket'].sudo().create({
                    'name': f"{task.dekad_request_type}: {task.dekad_contact_name or task.name}",
                    'description': task.description,
                    'dekad_contact_name': task.dekad_contact_name,
                    'dekad_company_name': task.dekad_company_name,
                    'dekad_email': task.dekad_email,
                    'dekad_phone': task.dekad_phone,
                    'dekad_request_type': task.dekad_request_type,
                    'dekad_industry': task.dekad_industry,
                    'dekad_employees': task.dekad_employees,
                    'dekad_demo_date': task.dekad_demo_date,
                })

        return tasks

    @api.model
    def _cron_notify_task_deadlines(self):
        companies = self.env['res.company'].search([
            ('enable_deadline_notifications', '=', True),
            ('deadline_notify_days', '>', 0)
        ])
        if not companies:
            return

        today = fields.Date.today()
        todo_activity_type = self.env.ref('mail.mail_activity_data_todo')

        for company in companies:
            target_date = today + timedelta(days=company.deadline_notify_days)

            # Search open tasks due on target_date
            tasks = self.search([
                ('company_id', 'in', [company.id, False]),
                ('date_deadline', '=', target_date),
                ('is_closed', '=', False),
                ('active', '=', True)
            ])

            for task in tasks:
                # Avoid duplicate activity scheduling for the same task
                existing_activities = self.env['mail.activity'].search_count([
                    ('res_model', '=', 'project.task'),
                    ('res_id', '=', task.id),
                    ('summary', 'in', ['Task Deadline Approaching', 'Team Task Deadline Approaching'])
                ])
                if existing_activities > 0:
                    continue

                programmers = task.user_ids
                team_leader = task.project_id.user_id
                programmer_names = ", ".join(programmers.mapped('name')) if programmers else "Unassigned"

                # 1. Notify Programmer(s) / Assignees
                for programmer in programmers:
                    prog_body = (
                        f"<p><strong>Deadline Reminder:</strong> The task "
                        f"<strong>{task.name}</strong> is due on "
                        f"<strong>{task.date_deadline}</strong>. Please ensure your work is submitted on time.</p>"
                    )
                    task.message_post(
                        body=prog_body,
                        partner_ids=programmer.partner_id.ids,
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )
                    task.activity_schedule(
                        activity_type_id=todo_activity_type.id,
                        summary='Task Deadline Approaching',
                        note=f"Task '{task.name}' is due on {task.date_deadline}.",
                        user_id=programmer.id
                    )

                # 2. Notify Team Leader
                if team_leader:
                    tl_body = (
                        f"<p><strong>Team Leader Alert:</strong> Task <strong>{task.name}</strong> "
                        f"assigned to programmer(s) <strong>{programmer_names}</strong> is due in "
                        f"<strong>{company.deadline_notify_days} day(s)</strong> (Deadline: {task.date_deadline}).</p>"
                    )
                    task.message_post(
                        body=tl_body,
                        partner_ids=team_leader.partner_id.ids,
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )

                    # Schedule activity for TL if they are not also assigned as the programmer
                    if team_leader not in programmers:
                        task.activity_schedule(
                            activity_type_id=todo_activity_type.id,
                            summary='Team Task Deadline Approaching',
                            note=f"Task '{task.name}' assigned to programmer(s): {programmer_names} is due on {task.date_deadline}.",
                            user_id=team_leader.id
                        )
