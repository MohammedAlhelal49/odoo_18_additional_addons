# -*- coding: utf-8 -*-
import json

from odoo import _, fields, http
from odoo.http import content_disposition, request


class DailyActivityReportController(http.Controller):

    @http.route('/alomran/daily_activity_report/xlsx', type='http', auth='user', methods=['POST'])
    def export_xlsx(self, options='{}', **kw):
        try:
            options = json.loads(options or '{}')
        except ValueError:
            options = {}
        Report = request.env['alomran.daily.activity.report']
        # access is checked inside (sales managers only)
        content = Report._get_xlsx_content(options)
        today = fields.Date.to_string(fields.Date.context_today(Report))
        filename = _("Daily Activity Report") + f" {today}.xlsx"
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename)),
        ])


class SalesReportController(http.Controller):

    @http.route('/alomran/sales_report/xlsx', type='http', auth='user', methods=['POST'])
    def export_xlsx(self, report_key, options='{}', **kw):
        try:
            options = json.loads(options or '{}')
        except ValueError:
            options = {}
        # access is checked inside get_report (salespeople, own scope enforced)
        content, filename = request.env['alomran.sales.report'].get_xlsx(report_key, options)
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename)),
        ])
