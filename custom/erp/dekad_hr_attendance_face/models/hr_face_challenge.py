import hashlib
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import SQL

from ..lib import liveness


def _hash_nonce(nonce):
    return hashlib.sha256(nonce.encode()).hexdigest()


class HrFaceChallenge(models.Model):
    """Single-use liveness challenge. Only the SHA-256 of the nonce is stored."""

    _name = 'hr.face.challenge'
    _description = "Face Recognition Challenge"
    _order = 'id desc'

    nonce_hash = fields.Char(required=True, index=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    channel = fields.Selection([('kiosk', "Kiosk"), ('mobile', "Personal Device")], required=True)
    user_id = fields.Many2one('res.users', ondelete='cascade')
    challenge = fields.Char(required=True)
    liveness_method = fields.Char(required=True)
    ip_address = fields.Char()
    issued_at = fields.Datetime(required=True)
    expires_at = fields.Datetime(required=True, index=True)
    state = fields.Selection([('issued', "Issued"), ('used', "Used")], default='issued', required=True)

    _sql_constraints = [
        ('nonce_hash_uniq', 'unique(nonce_hash)', "Nonce collision."),
    ]

    @api.model
    def _issue(self, company, channel, ip_address, user=None):
        """Create a challenge and return (nonce, challenge) for the client."""
        checker = liveness.get_checker(company.face_liveness_method)
        nonce = secrets.token_urlsafe(32)
        now = fields.Datetime.now()
        record = self.create({
            'nonce_hash': _hash_nonce(nonce),
            'company_id': company.id,
            'channel': channel,
            'user_id': user.id if user else False,
            'challenge': checker.new_challenge(),
            'liveness_method': checker.code,
            'ip_address': ip_address,
            'issued_at': now,
            'expires_at': now + timedelta(seconds=company.face_nonce_ttl),
        })
        return nonce, record.challenge

    @api.model
    def _consume(self, nonce, company, channel, user=None):
        """Atomically burn a nonce. Returns (values, reason); reason is None on success.

        The UPDATE ... WHERE state = 'issued' is atomic across workers: only one
        request can ever consume a given nonce, whatever the outcome.
        """
        if not isinstance(nonce, str) or not 20 <= len(nonce) <= 100:
            return None, 'invalid_nonce'
        self.env.cr.execute(SQL("""
            UPDATE hr_face_challenge
               SET state = 'used', write_date = (now() at time zone 'UTC')
             WHERE nonce_hash = %s AND state = 'issued'
         RETURNING company_id, channel, user_id, challenge, liveness_method, issued_at, expires_at
        """, _hash_nonce(nonce)))
        row = self.env.cr.dictfetchone()
        if not row:
            return None, 'invalid_nonce'
        if row['company_id'] != company.id or row['channel'] != channel \
                or (row['user_id'] or None) != (user.id if user else None):
            return None, 'nonce_mismatch'
        now = fields.Datetime.now()
        if row['expires_at'] < now:
            return None, 'expired_nonce'
        row['elapsed'] = (now - row['issued_at']).total_seconds()
        return row, None

    @api.model
    def _cron_face_gc(self):
        """Remove old challenges and stale rate-limit counters."""
        cutoff = fields.Datetime.now() - timedelta(hours=1)
        self.env.cr.execute(SQL("DELETE FROM hr_face_challenge WHERE expires_at < %s", cutoff))
        self.env['hr.face.throttle']._gc()
