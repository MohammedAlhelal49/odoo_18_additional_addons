import re

from odoo import http
from odoo.http import request

PRODUCTS_PER_PAGE = 12

# Product families shown as filters. The database has a single product
# category, so the family is guessed from the product name / internal code.
FAMILIES = [
    ("hematology", "Hematology", "fa-tint",
     r"hemat|haemat|hemolynac|isotonac|cleanac|clean protein|^mek|^mk-"),
    ("controls", "Calibrators & Controls", "fa-sliders",
     r"calibrat|control|\bqc\b|trol\b|\b[se]cal\b|\bacc\b|\baqc\b"),
    ("consumables", "Lab Consumables", "fa-cubes",
     r"cup|cuvette|wash|tubing|maintenance|solution|fluid"),
    ("chemistry", "Clinical Chemistry", "fa-flask", None),  # everything else
]
FAMILY_INFO = {key: {"key": key, "label": label, "icon": icon} for key, label, icon, _re in FAMILIES}


def _family(product):
    text = " ".join(filter(None, [product.name, product.default_code])).lower()
    for key, _label, _icon, pattern in FAMILIES:
        if pattern is None or re.search(pattern, text):
            return key
    return FAMILIES[-1][0]


class HealthcareWebsite(http.Controller):

    @http.route(["/products", "/products/page/<int:page>"], type="http", auth="public", website=True, sitemap=True)
    def products(self, page=1, search="", family="", **kw):
        search = (search or "").strip()
        domain = [("sale_ok", "=", True)]
        if search:
            domain += ["|", ("name", "ilike", search), ("default_code", "ilike", search)]
        products = request.env["product.template"].sudo().search(domain, order="name, id")

        families = {product.id: _family(product) for product in products}
        counts = {key: 0 for key in FAMILY_INFO}
        for key in families.values():
            counts[key] += 1
        if family in FAMILY_INFO:
            products = products.filtered(lambda p: families[p.id] == family)
        else:
            family = ""

        url_args = {key: value for key, value in (("search", search), ("family", family)) if value}
        pager = request.website.pager(
            url="/products", total=len(products), page=page, step=PRODUCTS_PER_PAGE, url_args=url_args)
        offset = pager["offset"]
        return request.render("healthcare_website.products_page", {
            "products": products[offset:offset + PRODUCTS_PER_PAGE],
            "product_family": {pid: FAMILY_INFO[key] for pid, key in families.items()},
            "families": [dict(FAMILY_INFO[key], count=counts[key]) for key, *_rest in FAMILIES],
            "total_count": sum(counts.values()),
            "found": len(products),
            "pager": pager,
            "search": search,
            "family": family,
            "currency": request.env.company.currency_id,
        })
