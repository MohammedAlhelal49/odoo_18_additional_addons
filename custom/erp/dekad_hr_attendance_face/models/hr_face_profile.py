import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Command
from odoo.tools import SQL

from ..lib import engine, liveness, matching

_logger = logging.getLogger(__name__)

MANAGER_GROUP = 'hr_attendance.group_hr_attendance_manager'

ENROLL_MIN_SAMPLES = 3
ENROLL_MAX_SAMPLES = 10
ENROLL_MIN_SCORE = 0.85
ENROLL_MIN_FACE_SIDE = 80
ENROLL_FRONTAL_MAX = 0.2
ENROLL_CONSISTENCY_MIN = 0.45

# Per-process cache of company galleries: (dbname, company_id) -> (signature, ids, matrix)
_GALLERY_CACHE = {}


class HrFaceProfile(models.Model):
    _name = 'hr.face.profile'
    _description = "Employee Face Profile"
    _rec_name = 'employee_id'
    _order = 'employee_id'

    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade', index=True, readonly=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, index=True)
    consent_given = fields.Boolean(string="Consent Given", readonly=True)
    consent_date = fields.Datetime(string="Consent Date", readonly=True)
    consent_user_id = fields.Many2one('res.users', string="Consent Recorded By", readonly=True)
    sample_ids = fields.One2many('hr.face.sample', 'profile_id', string="Samples", readonly=True)
    sample_count = fields.Integer(compute='_compute_sample_count', string="Number of Samples")

    _sql_constraints = [
        ('employee_uniq', 'unique(employee_id)', "An employee can only have one face profile."),
    ]

    @api.depends('sample_ids')
    def _compute_sample_count(self):
        for profile in self:
            profile.sample_count = len(profile.sample_ids)

    @api.model
    def _enroll_reason_message(self, code):
        return {
            'bad_input': _("invalid or unsupported image"),
            'no_face': _("no face detected"),
            'multiple_faces': _("more than one face"),
            'face_too_small': _("face too small"),
            'low_quality': _("face not clear or not looking at the camera"),
        }.get(code, code)

    @api.model
    def enroll_samples(self, employee_id, images, consent):
        """Compute and store face templates for an employee.

        Only Attendance administrators may enroll. Images are processed in
        memory and never stored; existing samples are replaced.
        """
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError(_("Only Attendance administrators can enroll faces."))
        if not consent:
            raise UserError(_("The employee's consent is required before enrolling their face."))
        if not isinstance(images, list) or not images:
            raise UserError(_("Capture or upload at least %s photos.", ENROLL_MIN_SAMPLES))
        if len(images) > ENROLL_MAX_SAMPLES:
            raise UserError(_("At most %s photos can be enrolled.", ENROLL_MAX_SAMPLES))
        face_engine = engine.get_engine()
        if not face_engine:
            raise UserError(_("The face recognition engine is not available on this server."))
        employee = self.env['hr.employee'].browse(int(employee_id)).exists()
        if not employee or not employee.active:
            raise UserError(_("Faces can only be enrolled for active employees."))
        employee.check_access('read')

        vectors, scores, rejected = [], [], []
        for index, value in enumerate(images, 1):
            try:
                if not isinstance(value, str):
                    raise engine.FaceInputError('bad_input')
                image = face_engine.decode(value, max_bytes=engine.ENROLL_MAX_BYTES, max_side=engine.ENROLL_MAX_SIDE)
                face = liveness.pick_face(face_engine.detect(image))
                if (face[14] < ENROLL_MIN_SCORE or min(face[2], face[3]) < ENROLL_MIN_FACE_SIDE
                        or not abs(liveness.yaw_ratio(face)) <= ENROLL_FRONTAL_MAX):
                    raise engine.FaceInputError('low_quality')
                vectors.append(face_engine.embed(image, face))
                scores.append(float(face[14]))
            except engine.FaceInputError as e:
                rejected.append(_("photo %(index)s: %(reason)s", index=index, reason=self._enroll_reason_message(e.code)))
        if len(vectors) < ENROLL_MIN_SAMPLES:
            raise UserError(_(
                "Only %(count)s usable photos (minimum %(minimum)s). Rejected: %(rejected)s",
                count=len(vectors), minimum=ENROLL_MIN_SAMPLES, rejected="; ".join(rejected) or "-"))

        np = engine.np
        stacked = np.stack(vectors)
        centroid = stacked.mean(axis=0)
        centroid /= np.linalg.norm(centroid)
        if float((stacked @ centroid).min()) < ENROLL_CONSISTENCY_MIN:
            raise UserError(_("The photos do not seem to show the same person. Please capture them again."))

        # Refuse templates that would make identification ambiguous.
        company = employee.company_id
        other_ids, other_matrix = self.env['hr.face.sample']._face_gallery(company.id, exclude_employee_id=employee.id)
        if other_matrix is not None:
            unique, best = matching.best_scores(centroid, other_ids, other_matrix)
            if len(best) and float(best.max()) >= company.face_match_threshold:
                other = self.env['hr.employee'].sudo().browse(int(unique[best.argmax()]))
                raise UserError(_(
                    "This face is too similar to the enrolled face of %s. Enrollment refused to avoid "
                    "ambiguous matches.", other.name))

        profile = self.search([('employee_id', '=', employee.id)])
        values = {
            'consent_given': True,
            'consent_date': fields.Datetime.now(),
            'consent_user_id': self.env.uid,
            'sample_ids': [Command.clear()] + [
                Command.create({
                    'embedding': engine.embedding_to_bytes(vector),
                    'detection_score': score,
                    'model_version': engine.MODEL_VERSION,
                })
                for vector, score in zip(vectors, scores)
            ],
        }
        if profile:
            profile.write(values)
        else:
            profile = self.create({'employee_id': employee.id, **values})
        _logger.info("Face profile enrolled for employee %s by user %s (%s samples)",
                     employee.id, self.env.uid, len(vectors))
        return {'accepted': len(vectors), 'rejected': rejected}

    @api.model
    def _cron_purge_inactive(self):
        """Safety net: archiving can happen on resource.resource without hr.employee.write."""
        profiles = self.sudo().with_context(active_test=False).search([('employee_id.active', '=', False)])
        if profiles:
            _logger.info("Purging %s face profiles of archived employees", len(profiles))
            profiles.unlink()


class HrFaceSample(models.Model):
    _name = 'hr.face.sample'
    _description = "Employee Face Sample"
    _order = 'id'

    profile_id = fields.Many2one('hr.face.profile', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(related='profile_id.employee_id', store=True, index=True)
    company_id = fields.Many2one(related='profile_id.company_id', store=True, index=True)
    embedding = fields.Binary(
        attachment=False, prefetch=False, copy=False, groups=MANAGER_GROUP,
        help="Biometric template (128 float32). Never displayed.")
    detection_score = fields.Float(digits=(3, 3), readonly=True)
    model_version = fields.Char(readonly=True)

    @api.model
    def _face_gallery(self, company_id, employee_id=None, exclude_employee_id=None):
        """Return (employee_ids, matrix) of consented samples of active employees
        of ``company_id``. Reads through SQL; callers are responsible for access:
        the kiosk controller (sudo) or an Attendance administrator.
        """
        np = engine.np
        conditions = [
            SQL("e.company_id = %s", company_id),
            SQL("e.active"),
            SQL("p.consent_given"),
            SQL("s.model_version = %s", engine.MODEL_VERSION),
        ]
        if employee_id:
            conditions.append(SQL("e.id = %s", employee_id))
        if exclude_employee_id:
            conditions.append(SQL("e.id != %s", exclude_employee_id))
        where = SQL(" AND ").join(conditions)
        joins = SQL("""
            FROM hr_face_sample s
            JOIN hr_face_profile p ON p.id = s.profile_id
            JOIN hr_employee e ON e.id = p.employee_id
        """)
        cache_key = None
        if not employee_id and not exclude_employee_id:
            self.env.cr.execute(SQL(
                "SELECT md5(string_agg(s.id::text || ':' || e.id::text, ',' ORDER BY s.id)) %s WHERE %s",
                joins, where))
            signature = self.env.cr.fetchone()[0]
            cache_key = (self.env.cr.dbname, company_id)
            cached = _GALLERY_CACHE.get(cache_key)
            if cached and cached[0] == signature:
                return cached[1], cached[2]
        self.env.cr.execute(SQL("SELECT e.id, s.embedding %s WHERE %s ORDER BY s.id", joins, where))
        ids, vectors = [], []
        for emp_id, value in self.env.cr.fetchall():
            vector = engine.embedding_from_bytes(value) if value else None
            if vector is not None:
                ids.append(emp_id)
                vectors.append(vector)
        result = (np.array(ids, dtype=np.int64), np.stack(vectors) if vectors else None)
        if cache_key:
            _GALLERY_CACHE[cache_key] = (signature, *result)
        return result
