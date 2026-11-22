# Robust Reschedule Wizard Time Pre-filling - Implementation Guide

## Overview
This guide documents how to implement a robust reschedule wizard with intelligent time pre-filling, real-time conflict checking, and proper HH:MM format display. This can be replicated in any Odoo 18 project.

## Feature Summary
- **Transient Model Wizard** for rescheduling appointments/records with time fields
- **Automatic Pre-filling** of current values when wizard opens
- **HH:MM Format Display** for all time fields (converts Float to readable format)
- **Real-time Conflict Checking** (optional, for scheduling applications)
- **Smooth User Experience** - no manual data entry needed

---

## 1. Create the Wizard Model

**File:** `wizard/reschedule_wizard.py`

```python
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class RescheduleWizard(models.TransientModel):
    _name = 'reschedule.wizard'
    _description = 'Reschedule Record'

    # Link to the record being rescheduled
    record_id = fields.Many2one(
        'base.model',  # Change to your target model
        string='Record',
        required=True,
        readonly=True
    )

    # Current values (pre-filled, read-only)
    current_date = fields.Date(
        string='Current Date',
        readonly=True,
        help='Current scheduled date'
    )
    current_time = fields.Float(
        string='Current Time',
        readonly=True,
        help='Current scheduled time (Float format)'
    )
    current_time_display = fields.Char(
        string='Current Time (HH:MM)',
        compute='_compute_current_time_display',
        readonly=True
    )

    # New values (editable)
    new_date = fields.Date(
        string='New Date',
        required=True,
        help='Select new scheduled date'
    )
    new_time = fields.Float(
        string='New Time',
        required=True,
        help='Select new time (9.0 = 09:00, 14.5 = 14:30)'
    )

    # Optional: Conflict checking
    has_conflict = fields.Boolean(
        string='Schedule Conflict Detected',
        compute='_compute_conflict'
    )
    conflict_details = fields.Text(
        string='Conflict Details',
        compute='_compute_conflict'
    )

    # Reschedule reason
    reason = fields.Text(
        string='Reschedule Reason',
        required=True,
        placeholder='Explain why this reschedule is necessary'
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with current record values"""
        res = super().default_get(fields_list)
        
        record_id = self.env.context.get('active_id')
        if record_id:
            record = self.env[self.env.context.get('active_model', 'base.model')].browse(record_id)
            
            if record.exists():
                # Pre-fill with current values
                if 'current_date' in fields_list and hasattr(record, 'scheduled_date'):
                    res['current_date'] = record.scheduled_date
                if 'current_time' in fields_list and hasattr(record, 'scheduled_time'):
                    res['current_time'] = record.scheduled_time
                if 'new_date' in fields_list:
                    res['new_date'] = record.scheduled_date if hasattr(record, 'scheduled_date') else fields.Date.today()
                if 'new_time' in fields_list:
                    res['new_time'] = record.scheduled_time if hasattr(record, 'scheduled_time') else 9.0
                if 'record_id' in fields_list:
                    res['record_id'] = record_id
        
        return res

    @api.depends('current_time')
    def _compute_current_time_display(self):
        """Convert Float time (9.0) to HH:MM format (09:00)"""
        for wizard in self:
            wizard.current_time_display = self._float_to_time_string(wizard.current_time)

    @api.depends('new_date', 'new_time')
    def _compute_conflict(self):
        """Check for scheduling conflicts with existing records"""
        for wizard in self:
            if not wizard.new_date or not wizard.new_time:
                wizard.has_conflict = False
                wizard.conflict_details = ""
                continue
            
            # Query for conflicts (customize based on your model)
            conflicts = self.env['base.model'].search([
                ('id', '!=', wizard.record_id.id),
                ('scheduled_date', '=', wizard.new_date),
                ('status', 'not in', ['cancelled', 'no_show']),
            ])
            
            conflict_list = []
            for conflict in conflicts:
                time_str = self._float_to_time_string(conflict.scheduled_time)
                conflict_list.append(f"• {conflict.name} at {time_str}")
            
            if conflict_list:
                wizard.has_conflict = True
                wizard.conflict_details = "Already scheduled:\n" + "\n".join(conflict_list)
            else:
                wizard.has_conflict = False
                wizard.conflict_details = ""

    def _float_to_time_string(self, float_time):
        """
        Convert Float time (9.0, 14.5) to HH:MM format (09:00, 14:30)
        
        Args:
            float_time: Float value (e.g., 9.0, 14.5, 9.75)
        
        Returns:
            String in HH:MM format (e.g., "09:00", "14:30", "09:45")
        """
        if not float_time:
            return ""
        
        try:
            # Round to avoid floating point issues
            float_time = round(float(float_time), 2)
            
            # Extract hours and minutes
            hours = int(float_time)
            minutes = round((float_time - hours) * 60)
            
            # Handle minute overflow
            if minutes >= 60:
                hours += 1
                minutes = 0
            
            # Format as HH:MM
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            _logger.warning(f"Could not convert time: {float_time}")
            return ""

    def _convert_time_string_to_float(self, time_string):
        """
        Convert HH:MM format back to Float for database storage
        
        Args:
            time_string: String in HH:MM format (e.g., "09:30")
        
        Returns:
            Float value (e.g., 9.5)
        """
        if not time_string:
            return 0.0
        
        try:
            parts = time_string.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours + (minutes / 60.0)
        except (ValueError, IndexError):
            _logger.warning(f"Could not convert time string: {time_string}")
            return 0.0

    def action_reschedule(self):
        """Execute the reschedule operation"""
        self.ensure_one()
        
        if self.has_conflict:
            raise ValidationError(
                _("Schedule conflict detected:\n%s\n\n"
                  "Please choose a different time or contact your supervisor.") 
                % self.conflict_details
            )
        
        # Update the record
        self.record_id.write({
            'scheduled_date': self.new_date,
            'scheduled_time': self.new_time,
            'reschedule_reason': self.reason,
            'reschedule_date': fields.Datetime.now(),
        })
        
        # Log the change (optional audit trail)
        _logger.info(
            f"Record {self.record_id.name} rescheduled from "
            f"{self.current_date} {self._float_to_time_string(self.current_time)} to "
            f"{self.new_date} {self._float_to_time_string(self.new_time)} - "
            f"Reason: {self.reason}"
        )
        
        # Return success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Record rescheduled successfully'),
                'type': 'success',
            }
        }
```

---

## 2. Create the Wizard View

**File:** `wizard/reschedule_wizard_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_reschedule_wizard_form" model="ir.ui.view">
        <field name="name">reschedule.wizard.form</field>
        <field name="model">reschedule.wizard</field>
        <field name="arch" type="xml">
            <form string="Reschedule Record">
                <sheet>
                    <!-- Conflict Alert -->
                    <field name="has_conflict" invisible="1"/>
                    <div class="alert alert-danger" role="alert" 
                         invisible="not has_conflict">
                        <strong>⚠️ Schedule Conflict:</strong>
                        <field name="conflict_details" readonly="1" nolabel="1"/>
                    </div>

                    <!-- Current Schedule (Read-only) -->
                    <group string="Current Schedule">
                        <field name="current_date" readonly="1"/>
                        <field name="current_time_display" readonly="1"/>
                    </group>

                    <!-- New Schedule (Editable) -->
                    <group string="New Schedule">
                        <field name="new_date" required="1"/>
                        <field name="new_time" widget="float_time" required="1"
                               help="Format: 9.0 = 09:00, 14.5 = 14:30"/>
                    </group>

                    <!-- Reason -->
                    <group string="Reschedule Reason">
                        <field name="reason" required="1" nolabel="1"/>
                    </group>
                </sheet>

                <footer>
                    <button name="action_reschedule" string="Confirm Reschedule" 
                            type="object" class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

---

## 3. Add Fields to Your Main Model

Add these fields to your model that will be rescheduled:

```python
scheduled_date = fields.Date(string='Scheduled Date', required=True)
scheduled_time = fields.Float(string='Scheduled Time', required=True)
reschedule_reason = fields.Text(string='Last Reschedule Reason')
reschedule_date = fields.Datetime(string='Last Rescheduled', readonly=True)
```

---

## 4. Add Action Button to Main Model View

```xml
<button name="action_open_reschedule_wizard" string="Reschedule" type="object"
        class="btn-info" icon="fa-calendar"/>
```

And in the model:

```python
def action_open_reschedule_wizard(self):
    return {
        'name': _('Reschedule'),
        'type': 'ir.actions.act_window',
        'res_model': 'reschedule.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'active_id': self.id,
            'active_model': self._name,
        }
    }
```

---

## 5. Update Manifest

Add to your `__manifest__.py`:

```python
'data': [
    # ... other files ...
    'wizard/reschedule_wizard_views.xml',
],
```

---

## 6. Key Implementation Points

### Time Format Conversion
- **Database**: Store as Float (9.0 = 9 AM, 14.5 = 2:30 PM)
- **Display**: Show as HH:MM (09:00, 14:30)
- **Widget**: Use `widget="float_time"` in views
- **Conversion**: `_float_to_time_string()` and `_convert_time_string_to_float()`

### Pre-filling Strategy
- Use `default_get()` to populate wizard fields on open
- Read-only display of current values
- Automatic format conversion to HH:MM for display
- Preserve original Float values for computation

### Conflict Checking
- Compute field `_compute_conflict()` runs automatically
- Show alert in wizard if conflict detected
- Can make override available for supervisors
- Prevents saving if conflict (unless overridden)

### Audit Trail
- Log reschedule operations with reason
- Store reschedule_date and reschedule_reason
- Optional: Create activity entries for tracking

---

## 7. Customization Points

When implementing in another project, customize:

1. **Model Name**: Replace `base.model` with your actual model (e.g., `appointment.record`)
2. **Date/Time Fields**: Update field names to match your model (`scheduled_date`, `scheduled_time`, etc.)
3. **Status Field**: For conflict checking, adjust status values to your model's workflow
4. **Conflict Logic**: Modify `_compute_conflict()` based on your scheduling rules
5. **Success Message**: Update the notification message and redirect action

---

## 8. Testing Checklist

- [ ] Wizard opens with current values pre-filled
- [ ] Time displays as HH:MM (not 9.0 or 14.5)
- [ ] Can select new date and time
- [ ] Conflict detection works correctly
- [ ] Reschedule saves correctly to database
- [ ] Audit trail records the change
- [ ] User receives success notification
- [ ] Cancel button closes without saving

---

## 9. Prompt for AI Agent Implementation

Use this prompt with an AI agent to implement in another project:

> "Implement a robust reschedule wizard for [MODEL_NAME] records. Follow the implementation guide at [PATH_TO_THIS_FILE]. The wizard should:
> 1. Pre-fill with current [DATE_FIELD] and [TIME_FIELD] values
> 2. Convert Float times (9.0) to HH:MM format (09:00) for display
> 3. Allow users to select new date/time and provide a reschedule reason
> 4. Check for schedule conflicts before allowing reschedule
> 5. Save changes with audit trail (reschedule_reason, reschedule_date)
> 6. Show HH:MM format in all views, not Float decimals
> 
> Use the medical_appointment_management/wizard/medical_appointment_reschedule_wizard.py as reference for:
> - _float_to_time_string() method for time conversion
> - default_get() pattern for pre-filling
> - @api.onchange handlers for real-time updates
> - try-except error handling for robustness
> - ir.actions.act_window_close for proper wizard closing"

---

## Reference Implementation

Full working implementation in Odoo 18 Medical Center project:
- **Model**: `medical_appointment_management/models/medical_appointment.py`
- **Wizard**: `medical_appointment_management/wizard/medical_appointment_reschedule_wizard.py`
- **Views**: `medical_appointment_management/wizard/medical_appointment_reschedule_wizard_views.xml`

Key methods to reference:
- `_float_to_time_string()` - Float to HH:MM conversion
- `_convert_time_string_to_float()` - HH:MM to Float conversion  
- `default_get()` - Wizard pre-filling with context
- `action_reschedule()` - Reschedule operation with validation
