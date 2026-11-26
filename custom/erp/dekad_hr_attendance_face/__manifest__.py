{
    'name': 'Attendance Face Recognition',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Secure face-recognition check-in/out for the attendance kiosk and personal devices',
    'description': """
Face recognition for hr_attendance
==================================
* Server-side detection (YuNet) and recognition (SFace) on CPU through OpenCV.
* Single-use nonce + head-turn liveness challenge, DB-based rate limiting.
* Biometric templates stored in a dedicated, administrator-only model.
* Kiosk (1:N, company kiosk token) and personal devices (1:1, logged-in user, geofence).

Python dependencies (opencv-python-headless, numpy) are optional: the module
installs without them and the feature stays disabled. See README.md.
    """,
    'author': 'Dekad',
    'depends': ['hr_attendance'],
    # Face libraries are intentionally NOT declared in external_dependencies:
    # declaring them would block installation when they are missing.
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/hr_face_profile_views.xml',
        'views/hr_face_attempt_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_work_location_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dekad_hr_attendance_face/static/src/face_capture/**/*',
            'dekad_hr_attendance_face/static/src/systray/**/*',
            'dekad_hr_attendance_face/static/src/enrollment/**/*',
        ],
        'hr_attendance.assets_public_attendance': [
            'dekad_hr_attendance_face/static/src/face_capture/**/*',
            'dekad_hr_attendance_face/static/src/kiosk/**/*',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
