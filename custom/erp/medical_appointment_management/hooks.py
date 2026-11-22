# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Fix sequence after module installation"""
    logger.warning("MEDICAL APPOINTMENT: post_init_hook starting...")

    try:
        # Delete old invalid sequence
        old_seq = env['ir.sequence'].search([('code', '=', 'medical.appointment')])
        if old_seq:
            logger.warning(f"MEDICAL APPOINTMENT: Deleting old sequence with prefix: {old_seq.prefix}")
            old_seq.unlink()

        # Create new valid sequence
        seq = env['ir.sequence'].create({
            'name': 'Medical Appointment',
            'code': 'medical.appointment',
            'prefix': 'APT/',
            'suffix': '',
            'number_next': 1,
            'number_increment': 1,
            'padding': 6,
            'company_id': env.ref('base.main_company').id,
        })
        logger.warning(f"MEDICAL APPOINTMENT: Created new sequence with ID: {seq.id}")

    except Exception as e:
        logger.error(f"MEDICAL APPOINTMENT: Error in post_init_hook: {str(e)}", exc_info=True)
        raise
