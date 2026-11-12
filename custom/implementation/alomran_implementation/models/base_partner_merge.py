from odoo import models, _
from odoo.exceptions import UserError


class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    # Merging deletes the source contacts, which is not allowed.
    def _merge(self, partner_ids, dst_partner=None, extra_checks=True):
        raise UserError(_("Merging contacts is disabled because contacts cannot be deleted."))
