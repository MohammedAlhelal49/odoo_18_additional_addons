def migrate(cr, version):
    # allow_price_override ("Allow Price Out of Range") was replaced by its inverse,
    # enforce_price_limits. Keep the behaviour of databases that still have the old
    # field only; databases that already have enforce_price_limits are left as is.
    cr.execute("""
        SELECT column_name FROM information_schema.columns
         WHERE table_name = 'pos_config'
           AND column_name IN ('allow_price_override', 'enforce_price_limits')
    """)
    columns = {row[0] for row in cr.fetchall()}
    if 'allow_price_override' in columns and 'enforce_price_limits' not in columns:
        cr.execute("ALTER TABLE pos_config ADD COLUMN enforce_price_limits boolean")
        cr.execute("UPDATE pos_config SET enforce_price_limits = NOT COALESCE(allow_price_override, false)")
