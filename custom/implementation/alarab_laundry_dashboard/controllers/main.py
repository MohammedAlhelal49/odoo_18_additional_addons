import json


from odoo import fields, http
from odoo.http import content_disposition, request


class LaundryReportController(http.Controller):

    @http.route("/alarab_laundry_dashboard/report/xlsx", type="http", auth="user", methods=["POST"])
    def report_xlsx(self, report_key, options="{}", **kwargs):
        # access is checked inside get_report (dashboard group); CSRF is checked by Odoo for POST
        content, filename = request.env["alarab.laundry.report"].get_xlsx(report_key, json.loads(options or "{}"))
        return request.make_response(content, headers=[
            ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("Content-Disposition", content_disposition(filename)),
        ])

    @http.route("/alarab_laundry_dashboard/statement/<int:partner_id>", type="http", auth="public", methods=["GET"])
    def customer_statement(self, partner_id, date_from=None, date_to=None, companies="", token=None, **kwargs):
        """Customer statement PDF, opened by the customer from the WhatsApp link (no login).

        The link is signed (customer, period, companies) with the database secret, so it cannot be
        changed to read another customer or period.
        """
        try:
            start, stop = fields.Date.to_date(date_from), fields.Date.to_date(date_to)
            company_ids = [int(c) for c in (companies or "").split(",") if c]
        except (TypeError, ValueError):
            raise request.not_found()
        report_model = request.env["alarab.laundry.report"].sudo()
        if not (start and stop and company_ids
                and report_model._check_statement_token(partner_id, start, stop, company_ids, token)):
            raise request.not_found()
        partner = request.env["res.partner"].sudo().browse(partner_id).exists()
        if not partner:
            raise request.not_found()
        pdf, _report_type = request.env["ir.actions.report"].sudo().with_context(
            allowed_company_ids=company_ids, lang=partner.lang or "en_US",
            # the public user usually has no timezone: print the time like the shop sees it
            ld_browser_tz=partner.tz or request.env.ref("base.user_admin").sudo().tz,
        )._render_qweb_pdf(
            "alarab_laundry_dashboard.action_report_customer_statement", [partner.id],
            data={"date_from": fields.Date.to_string(start), "date_to": fields.Date.to_string(stop)})
        filename = "Statement - %s - %s - %s.pdf" % (partner.name, date_from, date_to)
        return request.make_response(pdf, headers=[
            ("Content-Type", "application/pdf"),
            ("Content-Disposition", content_disposition(filename, disposition_type="inline")),
        ])
