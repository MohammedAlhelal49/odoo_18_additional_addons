from odoo import _, api, fields, models

YES_NO = [('yes', 'Yes'), ('no', 'No')]


class PhotonServiceReport(models.Model):
    _name = 'photon.service.report'
    _description = 'Customer Service Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
        default='draft', required=True, tracking=True)

    partner_id = fields.Many2one('res.partner', string='Clinic', required=True, tracking=True)
    address = fields.Text(compute='_compute_address', store=True, readonly=False)
    product_id = fields.Many2one('product.product', string='Model', tracking=True)
    model_name = fields.Char(string='Model Description')
    ppm_no = fields.Char(string='PPM No.')
    analytic_account_id = fields.Many2one('account.analytic.account', string='S No', tracking=True)
    report_date = fields.Datetime(
        string='Date & Time', required=True, default=fields.Datetime.now, tracking=True)
    engineer_id = fields.Many2one(
        'res.users', string='Service Engineer', default=lambda self: self.env.user, tracking=True)

    # Visit type
    is_ppm = fields.Boolean(string='PPM')
    is_installation = fields.Boolean(string='Installation')
    is_warranty = fields.Boolean(string='Warranty')
    is_contract = fields.Boolean(string='Contract')
    is_paid_service = fields.Boolean(string='Paid Service')

    # Checklist
    check_cleaning = fields.Boolean(string='Cleaning')
    check_laser_head = fields.Boolean(string='Laser Head Check')
    check_energy = fields.Boolean(string='Energy Check')
    check_fiber = fields.Boolean(string='Fiber Check')
    check_hp = fields.Boolean(string='HP Check')
    check_hose = fields.Boolean(string='Hose Check')
    check_water_refilling = fields.Boolean(string='Water Refilling')
    check_hvps = fields.Boolean(string='HVPS Check')
    check_power = fields.Boolean(string='Power Check')

    error = fields.Text()
    work_report = fields.Text()
    line_ids = fields.One2many('photon.service.report.line', 'report_id', string='Parts', copy=True)

    # Readings (Alexandrite / Nd:YAG)
    alex_lc = fields.Char(string='Alex LC')
    alex_v = fields.Char(string='Alex V')
    alex_tx = fields.Char(string='Alex Tx')
    alex_energy = fields.Char(string='Alex Energy')
    yag_lc = fields.Char(string='Yag LC')
    yag_v = fields.Char(string='Yag V')
    yag_tx = fields.Char(string='Yag Tx')
    yag_energy = fields.Char(string='Yag Energy')

    note = fields.Text()
    work_complete = fields.Selection(YES_NO)
    need_follow_up = fields.Selection(YES_NO, string='Need Follow-up')
    enclosed = fields.Selection(YES_NO)
    engineer_ok = fields.Selection(YES_NO, string='Engineer')
    customer_note = fields.Text(string='Note: Customer')

    @api.depends('partner_id')
    def _compute_address(self):
        for rec in self:
            address = rec.partner_id._display_address(without_company=True) if rec.partner_id else ''
            rec.address = '\n'.join(line for line in address.splitlines() if line.strip()) or False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.model_name = self.product_id.display_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('photon.service.report') or _('New')
        return super().create(vals_list)

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def _report_lines(self, minimum=4):
        """Part lines padded with empty rows so the printed table keeps its shape."""
        lines = list(self.line_ids)
        return lines + [False] * max(0, minimum - len(lines))


class PhotonServiceReportLine(models.Model):
    _name = 'photon.service.report.line'
    _description = 'Customer Service Report Part'
    _order = 'sequence, id'

    report_id = fields.Many2one('photon.service.report', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Part')
    name = fields.Char(string='Part Description', required=True)
    quantity = fields.Float(string='Qty', default=1.0, digits='Product Unit of Measure')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
