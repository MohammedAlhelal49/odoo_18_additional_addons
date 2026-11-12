
from odoo import models
import requests
import logging
import time

_logger = logging.getLogger(__name__)
class OrchidaARAPI:

    def __init__(self, company):
        self.base_url = company.orchida_base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {company.api_token}',
            "Company-id":company.companyid
        }





    def get_ar_invs_status(self, from_date, to_date, page, page_size=50, retries=3):
        url = f"{self.base_url}/GetInvStatus"

        params = {
            'dateFrom': from_date,
            'dateTo': to_date,
            'pageNumber': page,
            'pageSize': page_size
        }

        for attempt in range(retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=(10, 120)
                )

                # check HTTP status
                if response.status_code != 200:
                    _logger.warning(
                        "API returned status %s | Page %s",
                        response.status_code,
                        page
                    )
                    time.sleep(1)
                    continue

                # safe json parsing
                try:
                    return response.json()
                except ValueError:
                    _logger.error("Invalid JSON response from API | Page %s", page)
                    return {}

            except requests.exceptions.Timeout:
                _logger.warning("Timeout calling API | Page %s | Attempt %s",
                                page, attempt + 1)
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                _logger.error("Request error | Page %s | %s", page, str(e))
                time.sleep(1)

        _logger.error("API failed after %s retries | Page %s", retries, page)
        return {}
