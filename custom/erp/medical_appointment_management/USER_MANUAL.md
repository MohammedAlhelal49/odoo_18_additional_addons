# Dekad Medical Center
## Appointment Management System
### Complete User Manual

---

## Table of Contents
1. [System Overview](#system-overview)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Getting Started](#getting-started)
4. [Dashboard](#dashboard)
5. [Appointments](#appointments)
6. [Documents](#documents)
7. [Reports](#reports)
8. [Commission Tracking](#commission-tracking)
9. [Workflow Scenarios](#workflow-scenarios)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

### What is This System?

The Medical Center Appointment Management System is an Odoo-based solution designed to manage:
- **Medical appointments** from booking to completion
- **Patient records** and medical history
- **Staff roles** with role-based access control
- **Commission tracking** for all staff members
- **Document management** (prescriptions, lab reports, certificates)
- **Performance reporting** with analytics and KPIs

### Key Features

✅ **Flexible Appointment Workflow** - Multi-stage appointment lifecycle
✅ **Role-Based Access** - Different views for each staff type
✅ **Time-Window Actions** - Smart actions during critical time periods
✅ **Commission Management** - Automatic tracking by staff type
✅ **Document Management** - Attach files to appointments
✅ **Performance Dashboard** - Real-time KPI metrics
✅ **Audit Trail** - Track all actions and changes

---

## User Roles & Permissions

### 1. **Administrator** (System Admin)
**Access:** Everything - full system control

**Capabilities:**
- View all appointments, staff, and commissions
- Access staff commission reports
- View all performance metrics
- Configure system settings
- Manage user accounts and roles

**Key Actions:**
- Staff Commission Report - see all staff earnings by type
- System Configuration
- User Management

---

### 2. **Doctor** (Medical Professional)
**Access:** Own appointments only

**Capabilities:**
- View personal appointments
- Start consultation (within 5 min of appointment time)
- Complete consultation
- Add clinical findings, diagnosis, prescriptions
- Record patient vitals
- View personal earnings dashboard

**Key Actions:**
1. ⏱️ **Start Consultation** - Within 5 minutes of appointment time
2. 📝 **Add Clinical Notes** - Diagnosis, prescription, treatment plan
3. ✅ **Complete Consultation** - Finalize and close appointment
4. 💰 **View Earnings** - Personal performance & commission

**Time Window:** ±5 minutes of scheduled appointment time

---

### 3. **Nurse** (Triage/Clinical)
**Access:** Patients ready for triage

**Capabilities:**
- Check patient vitals
- Record vital signs (BP, temp, heart rate, O2, etc.)
- Mark patient ready for doctor
- View patient history
- Add nurse notes

**Key Actions:**
1. 📋 **Record Vitals** - Blood pressure, temperature, heart rate
2. ✓ **Mark Ready for Doctor** - When vitals complete
3. 📝 **Add Notes** - Clinical observations

**Time Window:** ±5 minutes of scheduled appointment time

---

### 4. **Receptionist** (Front Desk)
**Access:** All appointments for check-in

**Capabilities:**
- Confirm appointments (day before)
- Check in patients
- Manage patient arrival
- Mark no-shows
- Generate invoices
- View appointment schedule

**Key Actions:**
1. 📞 **Confirm Appointment** - Day before appointment
2. ✅ **Check In Patient** - 15 minutes before appointment
3. ❌ **Mark No-Show** - If patient doesn't arrive
4. 💳 **Generate Invoice** - Auto-generated on completion

**Time Window:** 15 minutes before appointment

---

### 5. **Sales Representative**
**Access:** Own leads and appointments

**Capabilities:**
- Track leads and conversions
- Book appointments
- View commission earnings
- Track lead follow-ups
- View sales performance

**Key Actions:**
1. 📊 **Book Appointment** - From qualified lead
2. 💰 **Track Commission** - View earned commission
3. 📈 **Sales Performance** - View personal stats

---

## Getting Started

### 1. Login to System
```
URL: http://localhost:8069
Username: Your username
Password: Your password
```

### 2. Navigate to Medical Module
```
Menu → Medical Appointments (or Medical Staff for employees)
```

### 3. Access Your Dashboard
```
Appointments → Dashboard
```

---

## Dashboard

### What is the Dashboard?

The Dashboard provides **real-time KPI metrics** for your medical center operations.

### Dashboard Features

**📊 Summary Cards:**
- Total Appointments
- Completed Appointments
- Upcoming Appointments
- Cancelled & No-Show Count
- Total Revenue
- Total Commission
- Completion Rate

**📈 Performance Trends:**
- Current vs Previous Period
- Percentage changes
- Visual indicators (↑ ↑)

**⏰ Date Range Filtering:**
- Select custom date range
- Auto-calculate previous period
- Real-time updates

### How to Use the Dashboard

**Step 1:** Click "Appointments → Dashboard"
**Step 2:** View summary cards
**Step 3:** Change date range (From Date / To Date)
**Step 4:** Dashboard auto-updates with new period

### What You'll See

**For Admins:**
- All staff appointments
- Total revenue from all sources
- Total commission paid

**For Doctors:**
- Only your appointments
- Your earnings
- Your completion rate

**For Sales:**
- Your leads booked
- Your commission earned
- Your conversion rate

---

## Appointments

### Appointment Lifecycle

```
Tentative → Confirmed → Checked-In → Ready for Doctor → 
In Consultation → Completed
```

### Creating an Appointment

**For Sales (Book Appointment):**
1. Go to CRM → Leads
2. Open a qualified lead
3. Click "Book Appointment"
4. Fill in:
   - Patient
   - Doctor
   - Date/Time
   - Service
   - Price
5. Click "Save"

**For Receptionist (Confirm):**
1. Go to Appointments
2. Find appointment
3. Click "Confirm" (day before)
4. System records confirmation time

### Managing Appointments

#### Receptionist: Check-In

**When:** 15 minutes before appointment
**How:**
1. Open appointment record
2. Click "Check In Patient"
3. System records:
   - Check-in time
   - Who checked in
   - Patient arrival status

**If Too Early:** "Too early to check in. Check in available in X minutes"
**If Past Time:** Can still check in (system flexible after time window)

#### Nurse: Mark Ready

**When:** Within ±5 minutes of appointment time
**How:**
1. Open appointment
2. Click "Mark Ready for Doctor"
3. Record patient vitals:
   - Blood pressure
   - Temperature
   - Heart rate
   - O2 saturation
   - Height/Weight
4. Add clinical notes
5. Click "Mark Ready for Doctor"

#### Doctor: Start Consultation

**When:** Within ±5 minutes of appointment time
**How:**
1. Open appointment
2. Click "Start Consultation"
3. System:
   - Sets status to "In Consultation"
   - Auto-generates MRN (Medical Record Number)
   - Records start time
4. Patient record now editable

#### Doctor: Complete Consultation

**When:** After appointment time
**How:**
1. While in "In Consultation" status:
2. Add clinical information:
   - Diagnosis
   - Prescriptions
   - Treatment plan
   - Doctor notes
3. Click "Complete Consultation"
4. System:
   - Calculates commission
   - Closes appointment
   - Generates invoice
   - Records completion time

### Appointment Status Meanings

| Status | Meaning | Who Acts | Next Step |
|--------|---------|----------|-----------|
| **Tentative** | Initial booking | Sales | Receptionist confirms |
| **Confirmed** | Confirmed by receptionist | Receptionist | Patient checks in |
| **Checked-In** | Patient arrived | Receptionist | Nurse takes vitals |
| **Ready for Doctor** | Vitals done, ready | Nurse | Doctor starts |
| **In Consultation** | Doctor is consulting | Doctor | Doctor completes |
| **Completed** | Finished and billed | Doctor | Payment/Follow-up |
| **Cancelled** | Cancelled | Any | Closed |
| **No-Show** | Patient didn't come | Receptionist | Closed |

---

## Documents

### What Are Documents?

Documents attached to appointments for:
- **Prescriptions** - Medication list
- **Lab Reports** - Test results
- **Medical Reports** - Clinical findings
- **Certificates** - Medical certificates
- **Forms** - Patient forms
- **Other** - Any relevant files

### How to Add a Document

**Step 1:** Open appointment
**Step 2:** Go to "Documents" tab
**Step 3:** Click "Add" (or "+" button)
**Step 4:** Fill in:
- **Document Name** - Brief description
- **Document Type** - Prescription, Lab Report, etc.
- **Description** - Additional details (optional)
- **Document File** - Upload file
**Step 5:** Click "Save"

### How to View Documents

**Step 1:** Open appointment
**Step 2:** Go to "Documents" tab
**Step 3:** See all attached documents with:
- Name
- Type (badge)
- Who uploaded it
- Upload date

### Document Types

| Type | Used For | Who Uses |
|------|----------|----------|
| **Prescription** | Medications | Doctor |
| **Lab Report** | Test results | Doctor/Nurse |
| **Medical Report** | Clinical report | Doctor |
| **Certificate** | Medical certificate | Receptionist |
| **Form** | Patient forms | Any |
| **Other** | Other files | Any |

---

## Reports

### Available Reports

#### 1. Staff Commission Report (Admin Only)
**Purpose:** View all staff commission by type

**How to Access:**
- Reporting → Staff Commission Report

**What You See:**
- Doctor commissions
- Nurse commissions
- Receptionist earnings
- Sales commissions
- Grouped by staff type
- With charts and comparisons

**Data Shown:**
- Total appointments
- Completed appointments
- Total revenue
- Commission earned
- Average per appointment

#### 2. Doctor Performance (Doctor Only)
**Purpose:** View your personal performance

**How to Access:**
- Reporting → My Appointments & Earnings

**What You See:**
- Your appointment timeline
- Your earnings trend
- Completion rate
- Service breakdown
- Commission details

**Time Period:** Filter by date range

#### 3. Sales Performance (Sales Only)
**Purpose:** Track your sales conversion

**How to Access:**
- Reporting → My Sales Performance

**What You See:**
- Leads booked
- Conversion rates
- Revenue generated
- Commission earned
- Monthly trends

### How to Use Reports

**Step 1:** Go to Reporting menu
**Step 2:** Select report type
**Step 3:** View chart or table
**Step 4:** Click row to drill down
**Step 5:** Export if needed (CSV/Excel)

---

## Commission Tracking

### How Commission Works

**Commission Calculation:**

```
Appointment Amount × Commission Rate = Commission Earned
```

**Example:**
- Appointment: 500 AED
- Commission Rate: 5%
- Commission Earned: 25 AED

### Commission by Staff Type

| Staff Type | When Earned | How Much | Based On |
|-----------|------------|----------|----------|
| **Doctor** | On completion | 5% of appointment fee | Completed appointments |
| **Nurse** | On ready | Fixed rate | Vitals recording |
| **Receptionist** | On check-in | Fixed rate | Patient arrival |
| **Sales** | On completion | Commission rate | Lead conversion |

### Viewing Your Commission

**For Doctors:**
1. Go to Reporting → My Appointments & Earnings
2. See total commission earned
3. See commission per appointment
4. View trends over time

**For All Staff:**
1. Go to Dashboard
2. Check "Total Commission" card
3. See percentage change vs previous period

### Commission Details

**What's Tracked:**
- ✅ Earned commission (amount calculated)
- ✅ Pending commission (not yet approved)
- ✅ Paid commission (already paid)
- ✅ Commission source (which appointment)
- ✅ Commission date (when earned)

---

## Workflow Scenarios

### Scenario 1: Complete Patient Appointment (Happy Path)

**Timeline:**

```
Day Before (Receptionist):
1. Open appointment
2. Click "Confirm"
3. Patient confirms by phone ✓

Appointment Day:
1. (15 min before) Receptionist: Check in patient
2. (5 min before) Nurse: Record vitals, mark ready
3. (At time) Doctor: Start consultation
4. (During) Doctor: Add diagnosis, prescription
5. (After time) Doctor: Complete consultation
6. (Auto) System: Generate invoice, calculate commission
```

**Step-by-Step:**

**Day Before - Receptionist:**
```
Appointments → Select appointment
Click "Confirm Appointment" button
System confirms, records confirmation time
```

**Appointment Day - 15 min before - Receptionist:**
```
Appointments → Find appointment
Click "Check In Patient" button
System records check-in time and user
Patient status: Checked-In
```

**Appointment Day - 5 min before - Nurse:**
```
Appointments → Find appointment
Go to "Vitals" section
Fill in:
  - Blood Pressure
  - Temperature
  - Heart Rate
  - O2 Saturation
  - Height/Weight
Add notes if needed
Click "Mark Ready for Doctor"
Status changes: Ready for Doctor
```

**Appointment Day - At time - Doctor:**
```
Appointments → Find appointment
Click "Start Consultation"
System sets status: In Consultation
Auto-generates MRN
Add clinical information:
  - Diagnosis
  - Prescriptions
  - Treatment plan
  - Doctor notes
Click "Complete Consultation"
System:
  - Closes appointment
  - Records end time
  - Generates invoice
  - Calculates commission (25 AED)
  - Updates Dashboard
```

### Scenario 2: Nurse Skips Action (Flexible Workflow)

**What happens if Nurse doesn't mark ready?**

**Timeline:**

```
(5 min before) Nurse is busy, can't record vitals

(At time) Doctor:
1. Clicks "Start Consultation"
2. System accepts (time window passed, allows flexibility)
3. Doctor starts consultation
4. Vitals recording is marked as "skipped"
```

**Result:**
- ✅ Appointment continues smoothly
- ✅ Doctor can still start
- ⚠️ Vitals field shows as "null" (skipped action)
- ✅ Nurses can catch up later if needed

### Scenario 3: Check-In Window Passed

**What happens if receptionist checks in too late?**

**Before Fix Time Window:**
```
Patient arrives early (30 min before)
Receptionist tries to check in
Error: "Too early to check in. Available in 30 minutes"
```

**After Time Window:**
```
Patient arrives 2 hours late
Receptionist still can check in
System: "Check-in window has passed but allowing for flexibility"
Check-in succeeds
Appointment continues
```

### Scenario 4: Admin Views All Staff Commission

**Step-by-Step:**

```
Admin Login:
1. Go to Reporting → Staff Commission Report
2. See chart grouped by:
   - Doctors: 5,000 AED total
   - Nurses: 2,000 AED total
   - Receptionists: 1,500 AED total
   - Sales: 8,000 AED total
3. Click on "Doctor" group to expand
4. See individual doctor commissions:
   - Dr. Ahmed: 2,500 AED (50 appointments × 50 AED avg)
   - Dr. Fatima: 2,500 AED (48 appointments × 52 AED avg)
5. Click on doctor name to view detail
6. See:
   - All their completed appointments
   - Each appointment's revenue
   - Total commission earned
   - Pending vs paid
```

---

## User Actions Quick Reference

### Receptionist Actions

| Action | When | Steps | Time |
|--------|------|-------|------|
| **Confirm** | Day before | Appt → "Confirm" button | Flexible |
| **Check In** | Before appt | Appt → "Check In" button | 15 min before |
| **No-Show** | No patient | Appt → "Mark No-Show" | After time |
| **Cancel** | If needed | Appt → "Cancel" | Any time |

### Nurse Actions

| Action | When | Steps | Time |
|--------|------|-------|------|
| **Record Vitals** | At appointment | Appt → Vitals section | ±5 min of time |
| **Mark Ready** | Vitals done | Appt → "Mark Ready" button | ±5 min of time |
| **Add Notes** | During | Appt → Nurse Notes field | Anytime |

### Doctor Actions

| Action | When | Steps | Time |
|--------|------|-------|------|
| **Start** | At appointment | Appt → "Start Consultation" | ±5 min of time |
| **Add Clinical** | During | Appt → Clinical section | During/after |
| **Complete** | After appointment | Appt → "Complete" button | After time |
| **View Earnings** | Anytime | Reporting → My Earnings | Anytime |

### Sales Actions

| Action | When | Steps | Result |
|--------|------|-------|--------|
| **Book Appt** | Lead qualified | Lead → "Book Appt" | Appointment created |
| **View Commiss** | Anytime | Dashboard / Reports | See earnings |
| **Track Conversion** | Ongoing | Reporting → Sales | Monitor leads |

---

## Troubleshooting

### Issue: "Can't check in - too early"

**Problem:** Getting error "Too early to check in"
**Solution:**
1. Check current time
2. Appointment time is more than 15 minutes away
3. Wait until 15 minutes before appointment
4. If appointment passed: Check in still works (system flexible)

### Issue: "Appointment is locked"

**Problem:** Can't edit appointment booking details
**Reason:** Appointment has started
**Solution:**
- You CAN still:
  - Add clinical notes
  - Record vitals
  - Update status
- You CANNOT change:
  - Appointment date/time
  - Patient
  - Doctor
  - Service

**Why:** Prevents accidental booking changes after appointment starts

### Issue: "Action not available"

**Problem:** Button is greyed out
**Possible Reasons:**
1. Wrong status (e.g., appointment not confirmed)
2. Outside time window
3. Wrong user role
4. Appointment already completed

**Solution:**
1. Check appointment status
2. Check current time vs appointment time
3. Check your user role
4. If time passed, system may be flexible - try anyway

### Issue: "Not enough permissions"

**Problem:** Can't see appointment or action
**Solution:**
- Doctors can only see their own appointments
- Admins can see everything
- Sales can only see their own leads
- Ask admin if you need higher access

### Issue: Commission not showing

**Problem:** Can't find commission in reports
**Solution:**
1. Appointment must be **Completed** status
2. Check Dashboard → Total Commission
3. For detailed: Reporting → Your role's report
4. Commission calculated when completed, may take few seconds

### Issue: Document won't upload

**Problem:** Can't add document to appointment
**Reasons:**
1. File too large
2. Wrong file type
3. Appointment locked

**Solution:**
1. Try smaller file
2. Use common formats (PDF, JPG, PNG)
3. Ask receptionist if needed

---

## Best Practices

### ✅ Do's

✅ Confirm appointments day before (Receptionist)
✅ Check in patients on time (Receptionist)
✅ Record vitals accurately (Nurse)
✅ Complete consultations same day (Doctor)
✅ Review Dashboard weekly (Admin)
✅ Attach relevant documents (All)
✅ Use correct appointment statuses

### ❌ Don'ts

❌ Don't change appointment date/time after starting
❌ Don't create multiple appointments for same patient same day
❌ Don't mark appointment complete before finishing
❌ Don't forget to record vitals (affects patient care)
❌ Don't ignore confirmation reminders
❌ Don't share patient information beyond your role

---

## Support & Help

### If You Need Help:

1. **Check Dashboard** - View KPI metrics
2. **Review Appointment Status** - Understand current state
3. **Check Time Windows** - Verify you're in correct timeframe
4. **Verify User Role** - Confirm you have permissions
5. **Contact Administrator** - For access/permission issues

### Key Contacts:

- **System Admin:** [Admin Email/Phone]
- **Help Desk:** [Support Email/Phone]
- **Training:** [Training Contact]

---

## System Architecture Overview

### Core Components:

1. **Appointments** - Central record
2. **Medical Staff** - Roles & permissions
3. **Patients** - Contact + medical history
4. **Documents** - File storage
5. **Commission** - Automatic tracking
6. **Reports** - Analytics & KPIs
7. **Dashboard** - Real-time metrics

### Data Flow:

```
Lead → Appointment → Confirmation → Check-In → 
Vitals → Consultation → Completion → Commission → Report
```

### Security:

- ✅ Role-based access (what you see)
- ✅ Record-level rules (who can edit)
- ✅ Audit trail (what changed)
- ✅ Time windows (when allowed)
- ✅ Status locks (after starting)

---

## Conclusion

This Medical Appointment Management System is designed to:
1. **Streamline** patient care workflow
2. **Automate** commission tracking
3. **Ensure** data integrity
4. **Provide** real-time analytics
5. **Support** role-based teamwork

**For Questions:** Consult this manual or contact your system administrator.

**Version:** 1.0 - October 2026
**Last Updated:** 2026-10-19

---

*End of User Manual*
