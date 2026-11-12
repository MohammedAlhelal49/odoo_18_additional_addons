from odoo import http, api, SUPERUSER_ID
from odoo.http import request
from odoo.modules.registry import Registry
import odoo
import logging

_logger = logging.getLogger(__name__)

class FcmController(http.Controller):
    def __init__(self):
        super().__init__()
        _logger.info("FCM Controller Initialized")

    @http.route('/firebaseOdooFlutter/select_db', type='json', auth='none', methods=['POST'], csrf=False)
    def select_db(self, db=None, **kwargs):
        """Endpoint to select a database and bind it to the session."""
        if not db:
            return {'status': 'error', 'message': 'Database name (db) is required'}
        
        try:
            # Set the database for the session
            request.session.db = db
            # Force session to be saved
            request.session.rotate()
            _logger.info("Database %s selected for session %s", db, request.session.sid)
            return {'status': 'success', 'message': f'Database {db} selected for session'}
        except Exception as e:
            _logger.error("Error selecting database %s: %s", db, str(e))
            return {'status': 'error', 'message': str(e)}

    @http.route('/firebaseOdooFlutter/register_device', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def register_device(self, token, db=None, device_type='android', device_name=False, user_id=None, server_url=None, **kwargs):
        """Endpoint to register or update an FCM token. Supports multi-database environments."""
        if not token:
            return {'status': 'error', 'message': 'Token is required'}
        
        # Determine which database to use
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        # Determine server URL if not provided
        if not server_url:
            server_url = request.httprequest.host_url.rstrip('/')

        try:
            # Bind the DB to session if not already set
            if not request.session.db:
                request.session.db = db

            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                
                partner_id = False
                if user_id:
                    user = env['res.users'].sudo().browse(int(user_id))
                    if user.exists():
                        partner_id = user.partner_id.id

                # Search by token AND server_url to allow same token on different servers
                device = env['fcm.device'].sudo().search([
                    ('token', '=', token),
                    ('server_url', '=', server_url)
                ], limit=1)
                
                vals = {
                    'partner_id': partner_id,
                    'device_type': device_type,
                    'dbname': db,
                    'server_url': server_url,
                }
                if device_name:
                    vals['name'] = device_name
                    
                if device:
                    device.write(vals)
                else:
                    vals['token'] = token
                    env['fcm.device'].create(vals)
                    
                return {'status': 'success', 'message': f'Device registered successfully in {db}'}
        except Exception as e:
            _logger.error("FCM Registration error in %s: %s", db, str(e))
            return {'status': 'error', 'message': f'Database {db} error: {str(e)}'}

    @http.route('/firebaseOdooFlutter/unregister_device', type='json', auth='none', methods=['POST'], csrf=False)
    def unregister_device(self, token, db=None, server_url=None, **kwargs):
        """Endpoint to unregister an FCM token."""
        if not token:
             return {'status': 'error', 'message': 'Token is required'}
        
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        if not server_url:
            server_url = request.httprequest.host_url.rstrip('/')

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                device = env['fcm.device'].sudo().search([
                    ('token', '=', token),
                    ('server_url', '=', server_url)
                ], limit=1)
                if device:
                    device.unlink()
                return {'status': 'success', 'message': f'Device unregistered successfully from {db}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Database {db} error: {str(e)}'}

    @http.route('/firebaseOdooFlutter/notifications', type='json', auth='none', methods=['POST'], csrf=False)
    def get_notifications(self, user_id, start_date=None, end_date=None, date_from=None, date_to=None, limit=None, db=None, **kwargs):
        """Endpoint to get notifications for a user with optional date filtering (start_date/end_date)."""
        db = db or kwargs.get('db') or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}
        
        start = start_date or date_from or kwargs.get('start_date') or kwargs.get('date_from')
        end = end_date or date_to or kwargs.get('end_date') or kwargs.get('date_to')

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                notifications = env['fcm.notification'].sudo().get_notifications_by_user_id(
                    user_id=user_id,
                    start_date=start,
                    end_date=end,
                    limit=limit if limit is not None else 50
                )
                return {'status': 'success', 'data': notifications}
        except Exception as e:
            return {'status': 'error', 'message': f'Database {db} error: {str(e)}'}

    @http.route('/firebaseOdooFlutter/mark_as_read', type='json', auth='none', methods=['POST'], csrf=False)
    def mark_as_read(self, notification_id=None, notification_ids=None, is_read='read', db=None, **kwargs):
        """Endpoint to update read status ('read' or 'notread') of notification log(s)."""
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        if not notification_id and not notification_ids:
            return {'status': 'error', 'message': 'notification_id or notification_ids is required'}

        ids_to_update = []
        if notification_id:
            ids_to_update.append(int(notification_id))
        if notification_ids:
            if isinstance(notification_ids, list):
                ids_to_update.extend([int(i) for i in notification_ids])
            else:
                ids_to_update.append(int(notification_ids))

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                notifications = env['fcm.notification'].sudo().browse(ids_to_update)
                if not notifications.exists():
                    return {'status': 'error', 'message': 'Notification(s) not found'}
                
                status_val = 'read' if is_read in ['read', True, 'true', 1] else 'notread'
                notifications.write({'is_read': status_val})
                return {'status': 'success', 'message': f'Updated notification(s) is_read to {status_val}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/firebaseOdooFlutter/get_preferences', type='json', auth='none', methods=['POST'], csrf=False)
    def get_preferences(self, token, db=None, server_url=None, **kwargs):
        """Endpoint to get notification preferences for a specific device, including granular actions."""
        if not token:
            return {'status': 'error', 'message': 'Token is required'}
        
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        if not server_url:
            server_url = request.httprequest.host_url.rstrip('/')

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                device = env['fcm.device'].sudo().search([
                    ('token', '=', token),
                    ('server_url', '=', server_url)
                ], limit=1)
                
                if not device:
                    return {'status': 'error', 'message': 'Device not found'}

                # Get installed modules filtered for sale, attendance, and crm
                target_modules = ['sale', 'sale_management', 'crm', 'hr_attendance', 'attendance']
                installed_modules = env['ir.module.module'].sudo().search([
                    ('state', '=', 'installed'),
                    ('name', 'in', target_modules)
                ])
                
                # Get existing preferences for this device
                existing_prefs = {p.module_id.id: p for p in device.fcm_addon_preference_ids}

                prefs = []
                for module in installed_modules:
                    pref = existing_prefs.get(module.id)
                    
                    # Get available actions for this module
                    available_actions = env['fcm.addon.preference'].get_available_actions(module.name)
                    
                    actions_data = []
                    if available_actions:
                        # Map existing action preferences
                        existing_actions = {a.action_type: a.is_enabled for a in pref.action_ids} if pref else {}
                        
                        for action_type, action_label in available_actions:
                            actions_data.append({
                                'action_type': action_type,
                                'action_label': action_label,
                                'is_enabled': existing_actions.get(action_type, True) # Default to True
                            })

                    prefs.append({
                        'module_id': module.id,
                        'preference_id': pref.id if pref else False,
                        'module_name': module.name,
                        'module_shortdesc': module.shortdesc,
                        'is_enabled': pref.is_enabled if pref else True, # Default to True if not set
                        'actions': actions_data
                    })
                return {'status': 'success', 'preferences': prefs}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/firebaseOdooFlutter/update_preference', type='json', auth='none', methods=['POST'], csrf=False)
    def update_preference(self, is_enabled, preference_id=None, module_id=None, action_type=None, token=None, db=None, server_url=None, **kwargs):
        """Endpoint to update a specific notification preference or action preference."""
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        if not preference_id and not (module_id and token):
            return {'status': 'error', 'message': 'Either preference_id OR (module_id AND token) is required'}

        if not server_url:
            server_url = request.httprequest.host_url.rstrip('/')

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                pref = False
                
                if preference_id:
                    pref = env['fcm.addon.preference'].sudo().browse(int(preference_id))
                elif module_id and token:
                    device = env['fcm.device'].sudo().search([
                        ('token', '=', token),
                        ('server_url', '=', server_url)
                    ], limit=1)
                    if not device:
                        return {'status': 'error', 'message': 'Device not found'}
                    
                    pref = env['fcm.addon.preference'].sudo().search([
                        ('device_id', '=', device.id),
                        ('module_id', '=', int(module_id))
                    ], limit=1)
                    
                    if not pref:
                        # Create new preference record if it doesn't exist
                        pref = env['fcm.addon.preference'].sudo().create({
                            'device_id': device.id,
                            'module_id': int(module_id),
                            'is_enabled': True if action_type else bool(is_enabled)
                        })

                if not pref or not pref.exists():
                    return {'status': 'error', 'message': 'Preference not found'}
                
                if action_type:
                    # Update or create action preference
                    action_pref = env['fcm.addon.preference.action'].sudo().search([
                        ('preference_id', '=', pref.id),
                        ('action_type', '=', action_type)
                    ], limit=1)
                    if action_pref:
                        action_pref.write({'is_enabled': bool(is_enabled)})
                    else:
                        env['fcm.addon.preference.action'].sudo().create({
                            'preference_id': pref.id,
                            'action_type': action_type,
                            'is_enabled': bool(is_enabled)
                        })
                    return {'status': 'success', 'message': f'Action preference {action_type} updated'}
                else:
                    # Update main module preference
                    pref.write({'is_enabled': bool(is_enabled)})
                    return {'status': 'success', 'message': 'Module preference updated'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/firebaseOdooFlutter/initialize_preferences', type='json', auth='none', methods=['POST'], csrf=False)
    def initialize_preferences(self, token, db=None, server_url=None, **kwargs):
        """Endpoint to initialize preferences for all installed addons on a device."""
        if not token:
            return {'status': 'error', 'message': 'Token is required'}
        
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        if not server_url:
            server_url = request.httprequest.host_url.rstrip('/')

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                device = env['fcm.device'].sudo().search([
                    ('token', '=', token),
                    ('server_url', '=', server_url)
                ], limit=1)
                
                if not device:
                    return {'status': 'error', 'message': 'Device not found'}

                device.action_initialize_fcm_preferences()
                return {'status': 'success', 'message': 'Preferences initialized'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/firebaseOdooFlutter/check_app_config', '/firebaseOdooFlutter/get_app_config'], type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def check_app_config(self, db=None, app_version=None, **kwargs):
        """Endpoint to check mobile app configuration, version requirements, and force update status."""
        db = db or request.params.get('db') or request.httprequest.args.get('db') or request.session.db
        if not db:
            return {'status': 'error', 'message': 'Database (db) is required'}

        try:
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                params = env['ir.config_parameter'].sudo()

                latest_version = params.get_param('firebaseOdooFlutter.app_version', default='1.0.0')
                min_version = params.get_param('firebaseOdooFlutter.min_app_version', default='1.0.0')
                force_update_param = params.get_param('firebaseOdooFlutter.force_update', default='False')
                force_update_flag = str(force_update_param).lower() in ['true', '1', 'yes']
                
                app_url_android = params.get_param('firebaseOdooFlutter.app_url_android', default='')
                app_url_ios = params.get_param('firebaseOdooFlutter.app_url_ios', default='')
                
                raw_app_config = params.get_param('firebaseOdooFlutter.app_config', default='')
                app_config_data = {}
                if raw_app_config:
                    try:
                        import json
                        app_config_data = json.loads(raw_app_config)
                    except Exception:
                        app_config_data = {'raw': raw_app_config}

                def parse_ver(v_str):
                    if not v_str:
                        return (0,)
                    parts = []
                    for p in str(v_str).strip().split('.'):
                        cleaned = ''.join(c for c in p if c.isdigit())
                        parts.append(int(cleaned) if cleaned else 0)
                    return tuple(parts)

                update_required = False
                must_force_update = force_update_flag

                if app_version:
                    client_ver = parse_ver(app_version)
                    latest_ver = parse_ver(latest_version)
                    min_ver = parse_ver(min_version)

                    if client_ver < latest_ver:
                        update_required = True
                    if client_ver < min_ver:
                        must_force_update = True

                return {
                    'status': 'success',
                    'latest_app_version': latest_version,
                    'min_app_version': min_version,
                    'update_required': update_required,
                    'force_update': must_force_update,
                    'app_url_android': app_url_android,
                    'app_url_ios': app_url_ios,
                    'app_config': app_config_data
                }
        except Exception as e:
            _logger.error("Error checking app configuration in %s: %s", db, str(e))
            return {'status': 'error', 'message': str(e)}



