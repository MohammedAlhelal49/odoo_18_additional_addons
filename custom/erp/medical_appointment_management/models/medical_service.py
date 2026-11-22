from odoo import api, fields, models


class MedicalService(models.Model):
    _name = 'medical.service'
    _description = 'Medical Service / Specialization'
    _order = 'name'

    name = fields.Char(string='Service Name', required=True, index=True)
    code = fields.Char(string='Service Code', index=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('consultation', 'Consultation'),
        ('surgery', 'Surgery'),
        ('diagnosis', 'Diagnosis'),
        ('therapy', 'Therapy'),
        ('other', 'Other'),
    ], string='Category', default='consultation')
    
    default_duration = fields.Float(
        string='Default Duration (hours)',
        default=1.0,
        help='Default appointment duration for this service'
    )
    duration = fields.Float(
        string='Duration (hours)',
        default=1.0,
        help='Duration of the medical service in hours'
    )
    duration_minutes = fields.Integer(
        string='Duration (minutes)',
        compute='_compute_duration_minutes',
        store=True
    )
    period_between_sessions = fields.Integer(
        string='Wait Days Between Sessions',
        default=0,
        help='Recommended minimum interval in days between consecutive treatments'
    )
    
    price = fields.Monetary(
        string='Service Price',
        currency_field='company_currency_id'
    )
    discount = fields.Float(string='Discount (%)', default=0.0)
    final_price = fields.Monetary(
        string='Net Price',
        compute='_compute_final_price',
        store=True,
        currency_field='company_currency_id'
    )

    doctor_ids = fields.Many2many(
        'hr.employee',
        string='Authorized Doctors',
        domain=[('medical_employee_type', '=', 'doctor')]
    )
    product_id = fields.Many2one(
        'product.product',
        string='Linked Invoicing Product'
    )
    color = fields.Integer(string='Color Index')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )

    active = fields.Boolean(default=True)

    @api.depends('price', 'discount')
    def _compute_final_price(self):
        for rec in self:
            if rec.price and rec.discount:
                rec.final_price = rec.price * (1.0 - (rec.discount / 100.0))
            else:
                rec.final_price = rec.price or 0.0

    @api.depends('duration', 'default_duration')
    def _compute_duration_minutes(self):
        for rec in self:
            d = rec.duration or rec.default_duration or 1.0
            rec.duration_minutes = int(d * 60)

    _rec_name = 'name'
    _rec_names_search = ['name', 'code']

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for service in self:
            if service.code:
                service.display_name = f"[{service.code}] {service.name}"
            else:
                service.display_name = service.name or ''

    def name_get(self):
        result = []
        for service in self:
            name = service.name
            if service.code:
                name = f"[{service.code}] {name}"
            result.append((service.id, name))
        return result

