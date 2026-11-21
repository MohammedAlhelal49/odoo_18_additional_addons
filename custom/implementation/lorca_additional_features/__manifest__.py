{
    "name": "Lorca additional features",
    "summary": "Extra restrictions and features for the Lorca system",
    "description": """
    *** Lorca Additional Features ***
-- Disable quick create / create on the fly of products in the lines of
   Sales, Accounting, Purchase and Inventory (selection only).
-- Credit Limit Visibility group: the credit limit on the contact is hidden
   from users who are not in this group.
""",
    "author": "Dekad software solutions",
    "version": "18.0",
    "category": "Dekad/Customizations",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "product", "sale", "purchase", "account", "stock"],
    "data": [
        "security/security.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "lorca_additional_features/static/src/**/*",
        ],
    },
}
