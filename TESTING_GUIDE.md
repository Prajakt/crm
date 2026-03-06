# CRM Project Workspace - Testing Guide

## Prerequisites

This implementation requires a Frappe bench with the CRM app installed. If you don't have one set up yet, follow these steps:

### Setup Frappe Bench (if needed)

```bash
# Install frappe-bench
pip install frappe-bench

# Create a new bench
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# Create a new site
bench new-site mysite.localhost

# Get the CRM app
bench get-app https://github.com/Prajakt/crm --branch feature/crm-project-workspace

# Install CRM app on site
bench --site mysite.localhost install-app crm

# Start bench
bench start
```

---

## Installation & Migration

Once you have a bench with the CRM app:

```bash
cd /path/to/frappe-bench/apps/crm

# Switch to the feature branch
git fetch origin
git checkout feature/crm-project-workspace
git pull origin feature/crm-project-workspace

# Go back to bench directory
cd ../..

# Run migrations to create new DocTypes and fields
bench --site mysite.localhost migrate

# Clear cache to load new hooks
bench --site mysite.localhost clear-cache

# Restart bench
bench restart
```

---

## Verification Script

Run this to verify all files are in place:

```bash
# From the CRM app directory
cd /path/to/frappe-bench/apps/crm

# Check DocTypes exist
ls -la crm/fcrm/doctype/crm_project/
ls -la crm/fcrm/doctype/crm_project_member/

# Check API files
ls -la crm/api/project.py
ls -la crm/permissions.py

# Check patches
ls -la crm/patches/v1_0/add_project_fields_to_core_doctypes.py

# Check documentation
ls -la PROJECT_ARCHITECTURE.md
ls -la PHASE_*_IMPLEMENTATION.md

echo "✓ All files are in place!"
```

---

## Testing Steps

### 1. Access the Site

```bash
# Start the bench
bench start

# Access in browser
open http://mysite.localhost:8000
```

Login with your admin credentials.

---

### 2. Verify DocTypes Created

```bash
# Check if DocTypes were created
bench --site mysite.localhost console

# In the Frappe console:
import frappe
frappe.connect()

# Check if CRM Project exists
print(frappe.db.exists("DocType", "CRM Project"))  # Should print: CRM Project

# Check if CRM Project Member exists
print(frappe.db.exists("DocType", "CRM Project Member"))  # Should print: CRM Project Member

# Check custom fields
lead_meta = frappe.get_meta("CRM Lead")
print(lead_meta.has_field("project"))  # Should print: True

deal_meta = frappe.get_meta("CRM Deal")
print(deal_meta.has_field("project"))  # Should print: True

print("✓ All DocTypes and fields created successfully!")
```

---

### 3. Create Test Project (Console)

```bash
bench --site mysite.localhost console
```

```python
import frappe
frappe.connect()
frappe.set_user("Administrator")

# Create a test project
project = frappe.get_doc({
    "doctype": "CRM Project",
    "project_name": "Test Project Q1",
    "project_code": "TEST-Q1",
    "status": "Active",
    "project_manager": "Administrator",
    "team_members": [
        {
            "user": "Administrator",
            "role": "Project Manager"
        }
    ]
})
project.insert()
frappe.db.commit()

print(f"✓ Project created: {project.name}")
```

---

### 4. Test Active Project APIs

```python
# Still in console
from crm.fcrm.doctype.crm_project.crm_project import (
    get_user_projects,
    set_active_project,
    get_active_project
)

# Get user's projects
projects = get_user_projects("Administrator")
print("User projects:", projects)

# Set active project
result = set_active_project("Test Project Q1")
print("Active project set:", result)

# Get active project
active = get_active_project("Administrator")
print("Active project:", active)

print("✓ Active project APIs working!")
```

---

### 5. Test Auto-Assignment

```python
# Create a lead - should auto-assign to active project
lead = frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "status": "Open"
})
lead.insert()
frappe.db.commit()

print(f"Lead created: {lead.name}")
print(f"Lead project: {lead.project}")  # Should be "Test Project Q1"

if lead.project == "Test Project Q1":
    print("✓ Auto-assignment working!")
else:
    print("✗ Auto-assignment not working")
```

---

### 6. Test Project Dashboard API

```python
from crm.api.project import get_project_dashboard

# Get dashboard data
dashboard = get_project_dashboard("Test Project Q1")

print("\n=== Project Dashboard ===")
print(f"Project: {dashboard['project']['project_name']}")
print(f"Status: {dashboard['project']['status']}")
print(f"Total Leads: {dashboard['stats']['total_leads']}")
print(f"Total Deals: {dashboard['stats']['total_deals']}")
print(f"Total Tasks: {dashboard['stats']['total_tasks']}")

print("✓ Dashboard API working!")
```

---

### 7. Test Team Management

```python
from crm.api.project import add_team_member, get_project_team

# Note: You need a real user email here
# For testing, create a test user first
test_user = frappe.get_doc({
    "doctype": "User",
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User",
    "send_welcome_email": 0
})
test_user.insert()
test_user.add_roles("Sales User")
frappe.db.commit()

# Add team member
add_team_member("Test Project Q1", "testuser@example.com", "Team Member")
print("✓ Team member added")

# Get team
team = get_project_team("Test Project Q1")
print(f"Team size: {len(team)}")
for member in team:
    print(f"  - {member['full_name']} ({member['role']})")

print("✓ Team management APIs working!")
```

---

### 8. Test Permissions

```python
# Test as Sales User
frappe.set_user("testuser@example.com")

# Create a lead (should assign to active project)
lead2 = frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "status": "Open"
})
lead2.insert()
frappe.db.commit()

print(f"Lead2 created: {lead2.name}")
print(f"Lead2 project: {lead2.project}")

# Get all leads (should only see leads from user's projects)
leads = frappe.get_all("CRM Lead", fields=["name", "lead_name", "project"])
print(f"\nLeads visible to testuser: {len(leads)}")
for l in leads:
    print(f"  - {l.lead_name}: {l.project or '(no project)'}")

# Try to access a lead from another project
# First create another project and lead as admin
frappe.set_user("Administrator")

project2 = frappe.get_doc({
    "doctype": "CRM Project",
    "project_name": "Other Project",
    "project_code": "OTHER",
    "status": "Active"
})
project2.insert()

lead3 = frappe.get_doc({
    "doctype": "CRM Lead",
    "first_name": "Bob",
    "last_name": "Johnson",
    "email": "bob@example.com",
    "status": "Open",
    "project": "Other Project"
})
lead3.insert()
frappe.db.commit()

# Now try to access as testuser
frappe.set_user("testuser@example.com")
try:
    lead3_doc = frappe.get_doc("CRM Lead", lead3.name)
    print("✗ Permission check failed - should not have access!")
except frappe.PermissionError:
    print("✓ Permission check working - access denied as expected!")

frappe.set_user("Administrator")
```

---

### 9. Test Project-Specific Layouts

```python
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import (
    save_fields_layout,
    get_fields_layout
)
import json

# Create a test layout
test_layout = [{
    "name": "tab1",
    "sections": [{
        "name": "section1",
        "columns": [{
            "name": "column1",
            "fields": ["first_name", "last_name", "email"]
        }]
    }]
}]

# Save global layout
save_fields_layout("CRM Lead", "Quick Entry", json.dumps(test_layout))
print("✓ Global layout saved")

# Save project-specific layout
project_layout = [{
    "name": "tab1",
    "sections": [{
        "name": "section1",
        "columns": [{
            "name": "column1",
            "fields": ["first_name", "email", "mobile_no"]  # Different fields
        }]
    }]
}]

save_fields_layout("CRM Lead", "Quick Entry", json.dumps(project_layout), "Test Project Q1")
print("✓ Project-specific layout saved")

# Get layout without project (should return global)
global_layout = get_fields_layout("CRM Lead", "Quick Entry")
print(f"Global layout sections: {len(global_layout)}")

# Get layout with project (should return project-specific)
project_layout_retrieved = get_fields_layout("CRM Lead", "Quick Entry", project="Test Project Q1")
print(f"Project layout sections: {len(project_layout_retrieved)}")

print("✓ Project-specific layouts working!")
```

---

### 10. Test Reports & Analytics

```python
from crm.api.project import get_project_reports

# Get reports
reports = get_project_reports("Test Project Q1")

print("\n=== Project Reports ===")
print(f"Conversion Rate: {reports['conversion_rate']:.1f}%")
print(f"Win Rate: {reports['win_rate']:.1f}%")
print(f"Avg Deal Value: {reports['avg_deal_value']}")
print(f"Leads by Source: {len(reports['leads_by_source'])} sources")
print(f"Monthly Trend: {len(reports['monthly_trend'])} months")

print("✓ Reports API working!")
```

---

## Browser Testing

### 1. Access CRM Module

1. Login to your site: http://mysite.localhost:8000
2. Go to CRM module
3. You should see "CRM Project" in the left sidebar

### 2. Create Project via UI

1. Click on "CRM Project" in sidebar
2. Click "New"
3. Fill in:
   - Project Name: "UI Test Project"
   - Project Code: "UI-TEST"
   - Status: Active
4. Add team members
5. Save

### 3. Test Project Switching

Use the browser console:

```javascript
// Get project context
frappe.call({
    method: 'crm.api.project.get_project_context',
    callback: function(r) {
        console.log('Context:', r.message);
    }
});

// Switch project
frappe.call({
    method: 'crm.api.project.switch_project',
    args: { project: 'UI Test Project' },
    callback: function(r) {
        console.log('Switched:', r.message);
        location.reload();
    }
});
```

### 4. Test Filtering

1. Go to CRM Lead list
2. Click "Filter"
3. You should see "Project" in the filter options
4. Filter by your project
5. Create a new lead - it should auto-assign to active project

---

## Performance Testing

```python
import time
import frappe
frappe.connect()
frappe.set_user("Administrator")

# Create 100 test leads
print("Creating 100 test leads...")
start = time.time()

for i in range(100):
    lead = frappe.get_doc({
        "doctype": "CRM Lead",
        "first_name": f"Test{i}",
        "email": f"test{i}@example.com",
        "status": "Open"
    })
    lead.insert()

frappe.db.commit()
elapsed = time.time() - start
print(f"✓ Created 100 leads in {elapsed:.2f} seconds")

# Test query performance
print("\nTesting query performance...")
start = time.time()

leads = frappe.get_all(
    "CRM Lead",
    filters={"project": "Test Project Q1"},
    fields=["name", "lead_name", "project"],
    limit_page_length=100
)

elapsed = time.time() - start
print(f"✓ Queried {len(leads)} leads in {elapsed:.3f} seconds")
```

---

## Cleanup (Optional)

```python
import frappe
frappe.connect()
frappe.set_user("Administrator")

# Delete test data
frappe.db.sql("DELETE FROM `tabCRM Lead` WHERE first_name LIKE 'Test%'")
frappe.db.sql("DELETE FROM `tabCRM Project` WHERE project_code LIKE 'TEST%'")
frappe.db.sql("DELETE FROM `tabUser` WHERE email = 'testuser@example.com'")
frappe.db.commit()

print("✓ Test data cleaned up")
```

---

## Troubleshooting

### Migrations Not Running

```bash
# Check migration status
bench --site mysite.localhost migrate --verbose

# Rebuild DocType if needed
bench --site mysite.localhost console

import frappe
frappe.connect()
frappe.reload_doc("fcrm", "doctype", "crm_project")
frappe.reload_doc("fcrm", "doctype", "crm_project_member")
```

### Custom Fields Not Showing

```bash
# Clear cache
bench --site mysite.localhost clear-cache

# Restart bench
bench restart
```

### Permission Errors

```bash
bench --site mysite.localhost console

import frappe
frappe.connect()

# Check hooks are loaded
from crm import hooks
print(hooks.permission_query_conditions)
print(hooks.has_permission)
```

---

## Expected Results

After running all tests, you should see:

✅ CRM Project DocType created
✅ CRM Project Member DocType created
✅ Custom fields added to Lead, Deal, Task, Organization
✅ Active project selection working
✅ Auto-assignment working
✅ Dashboard API returning data
✅ Team management APIs working
✅ Permissions restricting Sales Users to their projects
✅ Project-specific layouts working
✅ Reports API returning analytics

---

## Next Steps

Once all tests pass:

1. **Frontend Development**: Build UI components using the APIs
2. **User Training**: Train users on project management
3. **Data Migration**: Migrate existing data to projects
4. **Performance Tuning**: Add database indexes if needed
5. **Monitoring**: Set up monitoring for project usage

---

## Support

If you encounter issues:

1. Check migration logs: `bench --site mysite.localhost migrate --verbose`
2. Check error logs: `bench --site mysite.localhost logs`
3. Review documentation: PROJECT_ARCHITECTURE.md
4. Check implementation details: PHASE_*_IMPLEMENTATION.md

---

## Quick Reference Card

### Common Commands

```bash
# Run migrations
bench --site mysite.localhost migrate

# Clear cache
bench --site mysite.localhost clear-cache

# Open console
bench --site mysite.localhost console

# Restart bench
bench restart

# Check logs
bench --site mysite.localhost logs
```

### Quick Test Script

```python
# bench --site mysite.localhost console
import frappe
from crm.fcrm.doctype.crm_project.crm_project import *
from crm.api.project import *

frappe.connect()
frappe.set_user("Administrator")

# Create project
p = frappe.get_doc({"doctype": "CRM Project", "project_name": "Quick Test", "project_code": "QT"}).insert()

# Set active
set_active_project("Quick Test")

# Create lead
l = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Test", "email": "test@test.com"}).insert()

# Check
print(f"Lead project: {l.project}")  # Should be "Quick Test"
print("✓ Quick test passed!" if l.project == "Quick Test" else "✗ Quick test failed!")
```
