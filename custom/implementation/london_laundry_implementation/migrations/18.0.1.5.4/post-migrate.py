import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """التحصيلات بالجلسات المسكّرة اللي ما انطابقت مع فواتيرها عند الإغلاق: منطابقها هلق."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    sessions = env['pos.session'].search([('state', '=', 'closed')])
    done = sessions._laundry_reconcile_pending_collections()
    _logger.info("London Laundry: %s pending collections matched with their invoices", done)
