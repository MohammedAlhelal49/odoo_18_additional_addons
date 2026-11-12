import logging

_logger = logging.getLogger(__name__)

OLD_MODULE = "london_laundry_dashboard"
NEW_MODULE = "london_laundry_implementation"


def migrate(cr, version):
    """The dashboard, reports and daily e-mail moved from london_laundry_dashboard into this module.

    Hand its records (security group and its users, menus, actions, cron, settings fields...) over
    to this module so they are updated in place instead of deleted, then mark the old module as
    uninstalled. Does nothing on databases where london_laundry_dashboard was never installed.
    """
    cr.execute("SELECT id FROM ir_module_module WHERE name = %s AND state IN ('installed', 'to upgrade', 'to install')",
               (OLD_MODULE,))
    row = cr.fetchone()
    if not row:
        return
    cr.execute("""
        UPDATE ir_model_data old SET module = %s
         WHERE old.module = %s
           AND NOT EXISTS (SELECT 1 FROM ir_model_data new WHERE new.module = %s AND new.name = old.name)
    """, (NEW_MODULE, OLD_MODULE, NEW_MODULE))
    _logger.info("Moved %s records from %s to %s", cr.rowcount, OLD_MODULE, NEW_MODULE)
    cr.execute("DELETE FROM ir_model_data WHERE module = %s", (OLD_MODULE,))
    cr.execute("UPDATE ir_module_module SET state = 'uninstalled', latest_version = NULL WHERE id = %s", (row[0],))
    cr.execute("DELETE FROM ir_module_module_dependency WHERE module_id = %s", (row[0],))
