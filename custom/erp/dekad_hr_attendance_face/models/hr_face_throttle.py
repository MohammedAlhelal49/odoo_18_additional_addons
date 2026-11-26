from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import SQL


class HrFaceThrottle(models.Model):
    """Fixed-window counters shared by all workers through PostgreSQL.

    Updates use INSERT ... ON CONFLICT DO UPDATE, which takes a row lock, so
    concurrent requests on several workers count correctly without Redis.
    """

    _name = 'hr.face.throttle'
    _description = "Face Recognition Rate Limit"

    key = fields.Char(required=True)
    window_start = fields.Datetime(required=True)
    hits = fields.Integer(required=True, default=0)
    locked_until = fields.Datetime()

    _sql_constraints = [
        ('key_uniq', 'unique(key)', "Duplicate rate-limit key."),
    ]

    @api.model
    def _is_locked(self, keys):
        self.env.cr.execute(SQL(
            "SELECT 1 FROM hr_face_throttle WHERE key IN %s AND locked_until > %s LIMIT 1",
            tuple(keys), fields.Datetime.now()))
        return bool(self.env.cr.fetchone())

    @api.model
    def _hit(self, key, limit, window_minutes, lockout_minutes):
        """Count one event for ``key``; lock the key once ``limit`` is reached.

        :return: True if the key is now locked.
        """
        now = fields.Datetime.now()
        self.env.cr.execute(SQL("""
            INSERT INTO hr_face_throttle AS t (key, window_start, hits, create_date, write_date)
                 VALUES (%(key)s, %(now)s, 1, %(now)s, %(now)s)
            ON CONFLICT (key) DO UPDATE SET
                hits = CASE WHEN t.window_start <= %(window)s THEN 1 ELSE t.hits + 1 END,
                window_start = CASE WHEN t.window_start <= %(window)s THEN %(now)s ELSE t.window_start END,
                write_date = %(now)s
            RETURNING t.hits
        """, key=key, now=now, window=now - timedelta(minutes=window_minutes)))
        hits = self.env.cr.fetchone()[0]
        if hits < limit:
            return False
        self.env.cr.execute(SQL(
            "UPDATE hr_face_throttle SET locked_until = %s, hits = 0, window_start = %s WHERE key = %s",
            now + timedelta(minutes=lockout_minutes), now, key))
        return True

    @api.model
    def _gc(self):
        now = fields.Datetime.now()
        self.env.cr.execute(SQL("""
            DELETE FROM hr_face_throttle
             WHERE window_start < %s AND (locked_until IS NULL OR locked_until < %s)
        """, now - timedelta(days=1), now))
