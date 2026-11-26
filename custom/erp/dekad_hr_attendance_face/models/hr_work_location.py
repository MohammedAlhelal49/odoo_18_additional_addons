import math

from odoo import fields, models


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    face_latitude = fields.Float(string="Latitude", digits=(10, 7))
    face_longitude = fields.Float(string="Longitude", digits=(10, 7))
    face_geofence_radius = fields.Integer(
        string="Geofence Radius (m)",
        help="Face check-in from personal devices is only accepted within this distance of the "
             "coordinates above. 0 disables the geofence.")

    def _face_distance(self, latitude, longitude):
        """Haversine distance in meters from this location to the given point."""
        self.ensure_one()
        lat1, lon1 = math.radians(self.face_latitude), math.radians(self.face_longitude)
        lat2, lon2 = math.radians(latitude), math.radians(longitude)
        a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371000 * math.asin(math.sqrt(a))

    def _face_geofence_active(self):
        self.ensure_one()
        return bool(self.face_geofence_radius > 0 and (self.face_latitude or self.face_longitude))
