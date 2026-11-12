{
    'name': 'Al Omran CRM Enhancements',
    'version': '1.3',
    'category': 'Sales/CRM',
    'summary': 'Enhances CRM by preventing duplicates and automating opportunity reassignment',
    'depends': ['crm','base','sale','web' , 'contacts','dekad_sale_enhancement','utm'],
    'data': [
        'security/ir.model.access.csv',
        'security/alomran_security.xml',
        'data/crm_cron.xml',
        'data/schedule_day_data.xml',
        'data/course_duration_units_data.xml',
        'data/utm_sources.xml',
        'views/sale_report_inherit.xml',
        'views/crm_settings_view.xml',
        'views/res_partner_views.xml',
        'views/sale_order_view.xml',
        'views/sale_report_view.xml',
        "views/res_users_views.xml",
        "wizard/transfer_company_wizard_views.xml",
        "wizard/customer_lookup_views.xml",
        "views/takeover_log_views.xml",
        "views/crm_lead_alomran_views.xml",
        "views/res_partner_no_delete_views.xml",
        "views/daily_activity_report_views.xml",
        "report/daily_activity_report_pdf.xml",
        "views/mail_activity_views.xml",
        "views/sales_dashboard_views.xml",
        "views/sales_report_views.xml",
        "report/sales_report_pdf.xml",

    ],
    'assets': {
        'web.assets_frontend': [
            'alomran_implementation/static/src/js/patch_signature.js',
            'alomran_implementation/static/src/css/hide_auto_button.css',

        ],
        "web.assets_backend": [
            "alomran_implementation/static/src/js/list_confirmation_dialog_patch.js",
            "alomran_implementation/static/src/js/takeover_button.js",
            "alomran_implementation/static/xml/takeover_button.xml",
            "alomran_implementation/static/src/js/open_in_new_tab.js",
            "alomran_implementation/static/src/js/calendar_open_new_tab.js",
            "alomran_implementation/static/src/xml/open_in_new_tab.xml",
            "alomran_implementation/static/src/daily_activity_report/daily_activity_report.js",
            "alomran_implementation/static/src/daily_activity_report/daily_activity_report.xml",
            "alomran_implementation/static/src/daily_activity_report/daily_activity_report.scss",
            "alomran_implementation/static/src/daily_activity_report/daily_activity_dashboard.js",
            "alomran_implementation/static/src/daily_activity_report/daily_activity_dashboard.xml",
            "alomran_implementation/static/src/sales_dashboard/sales_dashboard.js",
            "alomran_implementation/static/src/sales_dashboard/sales_dashboard.xml",
            "alomran_implementation/static/src/sales_dashboard/sales_dashboard.scss",
            "alomran_implementation/static/src/sales_report/sales_report.js",
            "alomran_implementation/static/src/sales_report/sales_report.xml",
            "alomran_implementation/static/src/sales_report/sales_report.scss",
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'description': '''
- Prevents duplicate CRM opportunities for the same customer with the same title.
- Supports configurable duplicate contact handling (Warning Only or Prevent Duplicates) from Settings.
- Blocks creation or modification of contacts with duplicate names or phone/mobile numbers when duplicate prevention is enabled.
- Displays duplicate contact warnings (Name and Phone/Mobile) on both the Contacts form and the CRM Opportunity form.
- Synchronizes the CRM Opportunity mobile number with the linked Contact (res.partner) when edited.
- Extends the Contacts form by adding personal information fields and a read-only contract date set to the creation date.
- Adds custom course and enrollment fields to Sales Orders, and a read-only contract date set to the order creation date.
- Shows the mobile number in the partner display name instead of the address.
- Hides the Auto Signature button in the Sign interface.
- Transfers salesperson leads and contacts to another company.
- Customer Lookup: search a phone/mobile across all branches and see the branch, salesperson, last update, remaining validity days and Active/Expired status, with manual take over.
- Lead validity / manual transfer after N full days (default 30) without any employee update
  (log note, message, completed activity or stage change). Active / Expired filters on opportunities.
  The random auto-transfer cron is disabled.
- Contacts can never be deleted or merged; only Sales Managers can archive them.
- New opportunities require a Source and Notes/Details of at least 50 characters
  (existing opportunities are only checked when their notes change).
- Daily Activity Report per employee / branch / day (interactive screen with filters, drill-down, PDF and Excel export).
- Activity Dashboard: KPI cards, daily trend, tasks status, pipeline by stage, leads validity and
  employees comparison charts, overdue tasks and leads expiring soon.
- Sales managers / "All Documents" salespeople see every employee; "Own Documents" salespeople
  only see and track their own activity (enforced server side and by record rules).
- Sales Dashboard (same layout as the Bait Al Arab reports): period presets with comparison to the
  previous period, branch / salesperson filters, contracts KPIs, sales trend, payment methods,
  customer sources, new vs re-enrollment, best-selling courses, salespeople, branches and
  amounts remaining to invoice. "Own Documents" salespeople only see their own sales.
- Sales Reports (same layout as the Bait Al Arab reports, PDF and Excel export): Daily Sales,
  Sales by Course, Salesperson Performance, Sales by Branch, Sales by Payment Method,
  Sales by Customer Source and Remaining to Invoice, with period comparison and filters.
- "Open in New Tab" button on tasks (activities) and CRM lists; right / middle click on an
  opportunity in the CRM calendar opens it in a new browser tab.
''',

}



