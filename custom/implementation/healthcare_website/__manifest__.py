{
    "name": "Health Protection Website",
    "summary": "Public website for Health Protection: one-page home and a products listing (no e-commerce)",
    "version": "18.0.1.0.0",
    "category": "Website",
    "author": "Dekad (Mohammed alhelal)",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "data/website_data.xml",
        "views/layout_templates.xml",
        "views/home_templates.xml",
        "views/products_templates.xml",
        "views/partners_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "healthcare_website/static/src/scss/healthcare_website.scss",
        ],
    },
    "installable": True,
    "application": True,
}
