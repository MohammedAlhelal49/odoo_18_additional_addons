"""Show the full branch name in the report header (company details), not the short company name.

Only the 'Company Details' text of the document layout changes; the company name itself is kept.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

HEADER_NAMES = {
    "Bait Al Arab - Khalifa": "Bait Al Arab Automatic Laundry - Khalifa Branch",
    "ALDAHER": "Bait Al Arab Automatic Laundry - Al Daher Branch",
}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
    for company in env["res.company"].search([("name", "in", list(HEADER_NAMES))]):
        details = company.company_details or ""
        if company.name not in details:
            _logger.warning("Report header: company details of %s do not contain its name, not changed.",
                            company.name)
            continue
        company.company_details = details.replace(company.name, HEADER_NAMES[company.name], 1)
