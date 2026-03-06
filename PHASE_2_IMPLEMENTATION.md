# Phase 2 Implementation - Complete ✓

## What Was Implemented

Phase 2 extends the core CRM DocTypes (Lead, Deal, Task, Organization) with project fields and enables automatic project assignment based on the user's active project.

---

## Files Modified/Created

### 1. Custom Field Patch

**Created:** `crm/patches/v1_0/add_project_fields_to_core_doctypes.py`

This patch adds the `project` field to all core CRM DocTypes and the `crm_active_project` field to the User doctype.

**Fields Added:**
- **CRM Lead**: `project` field (Link to CRM Project) after `lead_owner`
- **CRM Deal**: `project` field (Link to CRM Project) after `deal_owner`
- **CRM Task**: `project` field (Link to CRM Project) after `assigned_to`
- **CRM Organization**: `project` field (Link to CRM Project) after `territory`
- **User**: `crm_active_project` field (Link to CRM Project, hidden, read-only) after `user_type`

**Properties:**
- All project fields are added to standard filters (`in_standard_filter: 1`)
- Fields are not shown in list view by default (`in_list_view: 0`)
- User's active project field is hidden and read-only (managed programmatically)

**Modified:** `crm/patches.txt`

Added the patch to the `[post_model_sync]` section to ensure it runs after DocTypes are migrated.

---

### 2. CRM Lead Controller

**Modified:** `crm/fcrm/doctype/crm_lead/crm_lead.py`

**Changes:**
1. Added `auto_assign_project()` call in the `validate()` method (line 81)
2. Added new method `auto_assign_project()` (lines 134-143)

**Method Logic:**
```python
def auto_assign_project(self):
    """Auto-assign current user's active project if not set"""
    if not self.project and frappe.db.exists("DocType", "CRM Project"):
        try:
            from crm.fcrm.doctype.crm_project.crm_project import get_active_project
            active_project = get_active_project(frappe.session.user)
            if active_project:
                self.project = active_project
        except Exception:
            # Silently fail if project module not available
            pass
```

**Behavior:**
- Only assigns project if `self.project` is not already set
- Checks if CRM Project DocType exists before attempting assignment
- Gets the current user's active project using `get_active_project()`
- Silently fails if CRM Project module is not available (backward compatible)

---

### 3. CRM Deal Controller

**Modified:** `crm/fcrm/doctype/crm_deal/crm_deal.py`

**Changes:**
1. Added `auto_assign_project()` call in the `validate()` method (line 85)
2. Added new method `auto_assign_project()` (lines 142-151)

**Method Logic:** Same as CRM Lead

---

### 4. CRM Task Controller

**Modified:** `crm/fcrm/doctype/crm_task/crm_task.py`

**Changes:**
1. Added `import frappe` at the top (line 4)
2. Added `auto_assign_project()` call in the `validate()` method (line 35)
3. Added new method `auto_assign_project()` (lines 42-51)

**Method Logic:** Same as CRM Lead

---

### 5. CRM Organization Controller

**Modified:** `crm/fcrm/doctype/crm_organization/crm_organization.py`

**Changes:**
1. Added `auto_assign_project()` call in the `validate()` method (line 32)
2. Added new method `auto_assign_project()` (lines 35-44)

**Method Logic:** Same as CRM Lead

---

## How It Works

### Automatic Project Assignment Flow

1. **User creates a new Lead/Deal/Task/Organization**
2. **Validate method is called**
3. **auto_assign_project() executes:**
   - Checks if `project` field is empty
   - Verifies CRM Project DocType exists
   - Gets user's active project from cache/database
   - Assigns active project to the record
4. **Record is saved with project pre-populated**

### Active Project Resolution

The `get_active_project(user)` function (from Phase 1) follows this resolution order:

1. **Check cache** - `frappe.cache().hget("active_project", user)`
2. **Check User field** - `frappe.db.get_value("User", user, "crm_active_project")`
3. **Get first project** - If user has no active project, get their first project
4. **Set as active** - Automatically set the first project as active

### User Project Assignment

Users are assigned to projects via the `team_members` child table in CRM Project. Only users who are members of a project can set it as their active project.

---

## Database Changes

After running the patch, the following custom fields will be created:

### Custom Field: project (in CRM Lead)
```sql
ALTER TABLE `tabCRM Lead`
ADD COLUMN `project` VARCHAR(140) NULL AFTER `lead_owner`;
```

### Custom Field: project (in CRM Deal)
```sql
ALTER TABLE `tabCRM Deal`
ADD COLUMN `project` VARCHAR(140) NULL AFTER `deal_owner`;
```

### Custom Field: project (in CRM Task)
```sql
ALTER TABLE `tabCRM Task`
ADD COLUMN `project` VARCHAR(140) NULL AFTER `assigned_to`;
```

### Custom Field: project (in CRM Organization)
```sql
ALTER TABLE `tabCRM Organization`
ADD COLUMN `project` VARCHAR(140) NULL AFTER `territory`;
```

### Custom Field: crm_active_project (in User)
```sql
ALTER TABLE `tabUser`
ADD COLUMN `crm_active_project` VARCHAR(140) NULL AFTER `user_type`;
```

---

## Installation & Migration

From your Frappe bench directory:

```bash
cd /path/to/frappe-bench

# Run migrate to apply changes
bench --site [your-site] migrate

# Restart bench to apply code changes
bench restart
```

The migration will:
1. Create CRM Project and CRM Project Member tables (Phase 1)
2. Add `project` custom fields to CRM Lead, Deal, Task, Organization
3. Add `crm_active_project` custom field to User
4. Make fields available in filters and forms

---

## Testing Phase 2

### Test 1: Create a Project and Assign Yourself

```python
import frappe

# Create a project
project = frappe.get_doc({
    "doctype": "CRM Project",
    "project_name": "Test Project Q1",
    "project_code": "TEST-Q1",
    "status": "Active",
    "project_manager": frappe.session.user,
    "team_members": [
        {
            "user": frappe.session.user,
            "role": "Project Manager"
        }
    ]
})
project.insert()

# Set as active project
from crm.fcrm.doctype.crm_project.crm_project import set_active_project
set_active_project("Test Project Q1")

frappe.db.commit()
```

### Test 2: Verify Active Project

```python
from crm.fcrm.doctype.crm_project.crm_project import get_active_project

active_project = get_active_project()
print(f"Your active project: {active_project}")
# Expected: "Test Project Q1"
```

### Test 3: Create a Lead and Verify Auto-Assignment

```python
# Create a lead (project should auto-assign)
lead = frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "status": "Open"
})
lead.insert()

print(f"Lead project: {lead.project}")
# Expected: "Test Project Q1"

frappe.db.commit()
```

### Test 4: Manual Project Override

```python
# Create another project
project2 = frappe.get_doc({
    "doctype": "CRM Project",
    "project_name": "Test Project Q2",
    "project_code": "TEST-Q2",
    "status": "Active",
    "team_members": [
        {
            "user": frappe.session.user,
            "role": "Team Member"
        }
    ]
})
project2.insert()

# Create a lead with explicit project (should NOT auto-assign)
lead = frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "status": "Open",
    "project": "Test Project Q2"  # Explicitly set
})
lead.insert()

print(f"Lead project: {lead.project}")
# Expected: "Test Project Q2" (NOT the active project)

frappe.db.commit()
```

### Test 5: Test Other DocTypes

```python
# Test Deal
deal = frappe.get_doc({
    "doctype": "CRM Deal",
    "organization": "Test Org",
    "status": "Open"
})
deal.insert()
print(f"Deal project: {deal.project}")
# Expected: Active project

# Test Task
task = frappe.get_doc({
    "doctype": "CRM Task",
    "title": "Follow up with lead",
    "status": "Todo",
    "priority": "Medium"
})
task.insert()
print(f"Task project: {task.project}")
# Expected: Active project

# Test Organization
org = frappe.get_doc({
    "doctype": "CRM Organization",
    "organization_name": "Acme Corp"
})
org.insert()
print(f"Organization project: {org.project}")
# Expected: Active project

frappe.db.commit()
```

---

## Filtering by Project

### UI - Standard Filters

All project fields are added to standard filters, so users can:

1. Go to CRM Lead/Deal/Task/Organization list view
2. Click on "Filter" button
3. See "Project" in the filter dropdown
4. Filter by one or more projects

### API - Programmatic Filtering

```python
# Get all leads for a specific project
leads = frappe.get_all(
    "CRM Lead",
    filters={"project": "Test Project Q1"},
    fields=["name", "lead_name", "email", "status"]
)

# Get all deals for the active project
from crm.fcrm.doctype.crm_project.crm_project import get_active_project
active_project = get_active_project()

deals = frappe.get_all(
    "CRM Deal",
    filters={"project": active_project},
    fields=["name", "organization", "deal_value", "status"]
)
```

---

## Key Features

### 1. Automatic Project Assignment
- ✅ New records automatically get the user's active project
- ✅ Existing records without a project can be manually assigned
- ✅ Users can override the default by explicitly setting a project

### 2. Backward Compatibility
- ✅ Silently fails if CRM Project module is not available
- ✅ Existing records without projects continue to work
- ✅ Project field is optional, not required

### 3. Multi-Project Support
- ✅ Users can belong to multiple projects
- ✅ Users can switch their active project
- ✅ Records can be assigned to any project (not just user's projects)

### 4. Standard Filter Integration
- ✅ Project field available in list view filters
- ✅ Users can filter by multiple projects
- ✅ Export filtered data to Excel/CSV

---

## What's Next - Phase 3 (Optional)

Phase 3 would add project-aware data filtering and permissions:

1. **Permission Queries**: Restrict users to only see records from their projects
2. **List View Filters**: Auto-filter list views by active project
3. **Project Dashboard**: Show project-specific statistics
4. **Strict Mode**: Enforce project membership for data access

See `PROJECT_ARCHITECTURE.md` for Phase 3 details.

---

## Summary

Phase 2 is **COMPLETE** and includes:
- ✅ Custom field patch to add `project` to Lead, Deal, Task, Organization
- ✅ Custom field `crm_active_project` in User doctype
- ✅ Auto-assignment of active project on record creation
- ✅ Manual project override capability
- ✅ Backward compatibility with existing code
- ✅ Standard filter integration

**Total Files Modified: 6**
- 1 patch created
- 1 patches.txt updated
- 4 controllers updated (Lead, Deal, Task, Organization)

**Total Files Created: 1**
- Phase 2 implementation patch

Ready for migration and testing!
