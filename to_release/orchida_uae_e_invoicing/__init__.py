from . import models
from . import services


def post_init_hook(env):
    """Migrate legacy Selection status values to new Char fields."""
    cr = env.cr

    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'api_sent_invoice'
          AND column_name IN ('taxAuthStatus', 'receiverStatus')
    """)
    legacy_cols = {row[0] for row in cr.fetchall()}

    # Legacy columns may not exist on fresh installs; migrate only when present.
    if legacy_cols:
        tax_expr = '"taxAuthStatus"' if 'taxAuthStatus' in legacy_cols else "'pending'"
        recv_expr = '"receiverStatus"' if 'receiverStatus' in legacy_cols else "'pending'"
        cr.execute(f"""
            UPDATE api_sent_invoice
            SET orchida_tax_status = COALESCE({tax_expr}, 'pending'),
                orchida_receiver_status = COALESCE({recv_expr}, 'pending')
            WHERE orchida_tax_status IS NULL
               OR orchida_receiver_status IS NULL
               OR orchida_tax_status = ''
               OR orchida_receiver_status = '';
        """)

    # Rename old service products that still carry the "Orchida" prefix
    Product = env['product.product'].sudo()
    for old_name, new_name in [
        ('Orchida Document Allowance', 'Document Allowance'),
        ('Orchida Document Charge', 'Document Charge'),
    ]:
        products = Product.search([('name', '=', old_name), ('type', '=', 'service')])
        if products:
            products.write({'name': new_name})

    # Map official UAE localization taxes to default Orchida categories.
    env['account.tax'].sudo().seed_default_tax_categories()