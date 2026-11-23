import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.london_laundry_implementation.models.res_partner import parse_laundry_number

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """أرقام قديمة محفوظة بصيغة دولية مع فراغات (+971 56 …): بنفس صيغة باقي الأرقام (056…)،
    حتى البحث برقم الهاتف بشاشة الطلبات يلاقيها."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    partners = env['res.partner'].with_context(active_test=False).search(['|', ('mobile', '!=', False), ('phone', '!=', False)])
    for partner in partners:
        vals = {}
        for field in ('mobile', 'phone'):
            value = partner[field]
            normalized = parse_laundry_number(value) if value else None
            if normalized and normalized != value:
                vals[field] = normalized
        if not vals:
            continue
        try:
            with cr.savepoint():
                partner.write(vals)
            _logger.info("London Laundry: %s numbers normalized: %s", partner.display_name, vals)
        except Exception as error:  # noqa: BLE001 - a duplicate number must not block the upgrade
            _logger.warning("London Laundry: %s numbers kept as they are (%s)", partner.display_name, error)
