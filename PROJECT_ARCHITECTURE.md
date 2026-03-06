# CRM Project/Workspace Architecture Design

## Overview
This document outlines the architecture for adding a **CRM Project** entity to Frappe CRM, enabling multi-project workspaces where users can be assigned to projects, switch between active projects, and have project-specific data schemas.

## Core Concepts

### 1. CRM Project (New DocType)
A workspace that contains a team of users and project-specific configurations.

**Relationship Model:**
```
CRM Project
  ├── Team Members (Users)
  ├── Leads (filtered by project)
  ├── Deals (filtered by project)
  ├── Tasks (filtered by project)
  ├── Organizations (client companies, filtered by project)
  └── Project-specific settings & schemas
```

**Key Difference from CRM Organization:**
- **CRM Organization** = External client companies (Acme Corp, ABC Industries)
- **CRM Project** = Internal workspace/initiative (Q1 Sales Campaign, Enterprise Accounts, APAC Expansion)

---

## Implementation Plan

### Phase 1: Core Project Entity

#### 1.1 Create CRM Project DocType

**File:** `crm/fcrm/doctype/crm_project/crm_project.json`

```json
{
  "doctype": "DocType",
  "name": "CRM Project",
  "module": "FCRM",
  "autoname": "field:project_name",
  "allow_rename": 1,
  "fields": [
    {
      "fieldname": "project_name",
      "fieldtype": "Data",
      "label": "Project Name",
      "reqd": 1,
      "unique": 1
    },
    {
      "fieldname": "project_code",
      "fieldtype": "Data",
      "label": "Project Code",
      "description": "Short code for the project (e.g., Q1-ENT, APAC-2024)"
    },
    {
      "fieldname": "description",
      "fieldtype": "Text Editor",
      "label": "Description"
    },
    {
      "fieldname": "status",
      "fieldtype": "Select",
      "label": "Status",
      "options": "Active\nOn Hold\nCompleted\nArchived",
      "default": "Active"
    },
    {
      "fieldname": "project_manager",
      "fieldtype": "Link",
      "label": "Project Manager",
      "options": "User"
    },
    {
      "fieldname": "start_date",
      "fieldtype": "Date",
      "label": "Start Date"
    },
    {
      "fieldname": "end_date",
      "fieldtype": "Date",
      "label": "End Date"
    },
    {
      "fieldname": "team_section",
      "fieldtype": "Section Break",
      "label": "Team Members"
    },
    {
      "fieldname": "team_members",
      "fieldtype": "Table",
      "label": "Team Members",
      "options": "CRM Project Member"
    },
    {
      "fieldname": "settings_section",
      "fieldtype": "Section Break",
      "label": "Project Settings"
    },
    {
      "fieldname": "default_territory",
      "fieldtype": "Link",
      "label": "Default Territory",
      "options": "CRM Territory"
    },
    {
      "fieldname": "default_currency",
      "fieldtype": "Link",
      "label": "Default Currency",
      "options": "Currency"
    },
    {
      "fieldname": "is_default",
      "fieldtype": "Check",
      "label": "Is Default Project",
      "description": "New users will be assigned to this project by default"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1
    },
    {
      "role": "Sales Manager",
      "read": 1,
      "write": 1,
      "create": 1
    },
    {
      "role": "Sales User",
      "read": 1
    }
  ]
}
```

#### 1.2 Create CRM Project Member (Child Table)

**File:** `crm/fcrm/doctype/crm_project_member/crm_project_member.json`

```json
{
  "doctype": "DocType",
  "name": "CRM Project Member",
  "module": "FCRM",
  "istable": 1,
  "fields": [
    {
      "fieldname": "user",
      "fieldtype": "Link",
      "label": "User",
      "options": "User",
      "in_list_view": 1,
      "reqd": 1
    },
    {
      "fieldname": "full_name",
      "fieldtype": "Data",
      "label": "Full Name",
      "fetch_from": "user.full_name",
      "in_list_view": 1,
      "read_only": 1
    },
    {
      "fieldname": "role",
      "fieldtype": "Select",
      "label": "Project Role",
      "options": "Project Manager\nTeam Lead\nTeam Member",
      "default": "Team Member",
      "in_list_view": 1
    },
    {
      "fieldname": "joined_date",
      "fieldtype": "Date",
      "label": "Joined Date",
      "default": "Today"
    }
  ]
}
```

#### 1.3 Python Controller

**File:** `crm/fcrm/doctype/crm_project/crm_project.py`

```python
import frappe
from frappe import _
from frappe.model.document import Document


class CRMProject(Document):
    def validate(self):
        self.validate_team_members()
        self.ensure_single_default()

    def validate_team_members(self):
        """Ensure no duplicate users in team members"""
        users = [d.user for d in self.team_members]
        if len(users) != len(set(users)):
            frappe.throw(_("Duplicate users found in team members"))

        # Ensure project manager is in team members
        if self.project_manager:
            manager_in_team = any(d.user == self.project_manager for d in self.team_members)
            if not manager_in_team:
                self.append("team_members", {
                    "user": self.project_manager,
                    "role": "Project Manager"
                })

    def ensure_single_default(self):
        """Ensure only one project is marked as default"""
        if self.is_default:
            # Unset all other default projects
            frappe.db.sql("""
                UPDATE `tabCRM Project`
                SET is_default = 0
                WHERE name != %s AND is_default = 1
            """, self.name)

    def on_update(self):
        # Clear user's active project cache when team changes
        for member in self.team_members:
            frappe.cache().hdel("active_project", member.user)

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Project",
                "type": "Data",
                "key": "project_name",
                "width": "16rem",
            },
            {
                "label": "Status",
                "type": "Select",
                "key": "status",
                "width": "10rem",
            },
            {
                "label": "Project Manager",
                "type": "Link",
                "key": "project_manager",
                "options": "User",
                "width": "14rem",
            },
            {
                "label": "Team Size",
                "type": "Int",
                "key": "team_size",
                "width": "8rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "10rem",
            },
        ]
        rows = [
            "name",
            "project_name",
            "project_code",
            "status",
            "project_manager",
            "modified",
        ]
        return {"columns": columns, "rows": rows}


@frappe.whitelist()
def get_user_projects(user=None):
    """Get all projects a user belongs to"""
    if not user:
        user = frappe.session.user

    projects = frappe.get_all(
        "CRM Project Member",
        filters={"user": user},
        fields=["parent as project", "role"],
        order_by="creation desc"
    )

    project_details = []
    for p in projects:
        project_doc = frappe.get_doc("CRM Project", p.project)
        project_details.append({
            "name": project_doc.name,
            "project_name": project_doc.project_name,
            "project_code": project_doc.project_code,
            "status": project_doc.status,
            "role": p.role,
            "is_active": get_active_project(user) == project_doc.name
        })

    return project_details


@frappe.whitelist()
def set_active_project(project):
    """Set the user's currently active project"""
    user = frappe.session.user

    # Verify user belongs to this project
    member = frappe.db.exists("CRM Project Member", {
        "parent": project,
        "user": user
    })

    if not member:
        frappe.throw(_("You are not a member of this project"))

    # Store in user defaults
    frappe.db.set_value("User", user, "crm_active_project", project, update_modified=False)

    # Also cache it for quick access
    frappe.cache().hset("active_project", user, project)

    return {"project": project}


@frappe.whitelist()
def get_active_project(user=None):
    """Get the user's currently active project"""
    if not user:
        user = frappe.session.user

    # Try cache first
    cached_project = frappe.cache().hget("active_project", user)
    if cached_project:
        return cached_project

    # Try user defaults
    active_project = frappe.db.get_value("User", user, "crm_active_project")

    # If no active project, get the first project user belongs to
    if not active_project:
        first_project = frappe.db.get_value(
            "CRM Project Member",
            {"user": user},
            "parent",
            order_by="creation desc"
        )
        if first_project:
            active_project = first_project
            set_active_project(first_project)

    return active_project
```

---

### Phase 2: Extend Core DocTypes

#### 2.1 Add Project Field to Core DocTypes

Add `project` field to: CRM Lead, CRM Deal, CRM Task, CRM Organization

**Example migration script:**

**File:** `crm/patches/add_project_field.py`

```python
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add project field to core CRM doctypes"""

    custom_fields = {
        "CRM Lead": [
            {
                "fieldname": "project",
                "label": "Project",
                "fieldtype": "Link",
                "options": "CRM Project",
                "insert_after": "lead_owner",
                "in_list_view": 0,
                "in_standard_filter": 1,
                "translatable": 0,
            }
        ],
        "CRM Deal": [
            {
                "fieldname": "project",
                "label": "Project",
                "fieldtype": "Link",
                "options": "CRM Project",
                "insert_after": "deal_owner",
                "in_list_view": 0,
                "in_standard_filter": 1,
                "translatable": 0,
            }
        ],
        "CRM Task": [
            {
                "fieldname": "project",
                "label": "Project",
                "fieldtype": "Link",
                "options": "CRM Project",
                "insert_after": "assigned_to",
                "in_list_view": 0,
                "in_standard_filter": 1,
                "translatable": 0,
            }
        ],
        "CRM Organization": [
            {
                "fieldname": "project",
                "label": "Project",
                "fieldtype": "Link",
                "options": "CRM Project",
                "insert_after": "territory",
                "in_list_view": 0,
                "in_standard_filter": 1,
                "translatable": 0,
            }
        ],
        "User": [
            {
                "fieldname": "crm_active_project",
                "label": "Active CRM Project",
                "fieldtype": "Link",
                "options": "CRM Project",
                "insert_after": "user_type",
                "hidden": 1,  # Managed programmatically
                "translatable": 0,
            }
        ],
    }

    create_custom_fields(custom_fields, update=True)
```

#### 2.2 Auto-assign Project on Record Creation

**File:** `crm/fcrm/doctype/crm_lead/crm_lead.py` (modifications)

```python
# Add this to CRMLead class validate method

def validate(self):
    # Existing validation...
    self.auto_assign_project()

def auto_assign_project(self):
    """Auto-assign current user's active project if not set"""
    if not self.project:
        from crm.fcrm.doctype.crm_project.crm_project import get_active_project
        active_project = get_active_project(frappe.session.user)
        if active_project:
            self.project = active_project
```

**Apply similar changes to:** `crm_deal.py`, `crm_task.py`, `crm_organization.py`

---

### Phase 3: Project-Aware Data Filtering

#### 3.1 Permission Query for Project-Based Access

**File:** `crm/fcrm/doctype/crm_lead/crm_lead.py` (add permission query)

```python
def has_permission(doc, ptype, user):
    """Custom permission check for project-based access"""

    # System Managers and Sales Managers can see all
    if "System Manager" in frappe.get_roles(user) or "Sales Manager" in frappe.get_roles(user):
        return True

    # Check if user belongs to the lead's project
    if doc.project:
        is_member = frappe.db.exists("CRM Project Member", {
            "parent": doc.project,
            "user": user
        })
        return bool(is_member)

    # If no project assigned, fall back to standard permissions
    return True
```

**Apply to:** `crm_deal.py`, `crm_task.py`

#### 3.2 List View Filter Hook

**File:** `crm/api/doc.py` (modify get_list functions)

```python
@frappe.whitelist()
def get_leads(filters=None, order_by=None, page_length=20, start=0):
    """Get leads filtered by active project"""
    from crm.fcrm.doctype.crm_project.crm_project import get_active_project

    # Parse filters
    if isinstance(filters, str):
        filters = json.loads(filters)
    if not filters:
        filters = {}

    # Add project filter if user has active project
    # (unless they're viewing a different project explicitly)
    if "project" not in filters:
        active_project = get_active_project()
        if active_project:
            # Sales Users see only their project
            # Managers can see all projects but default to active
            if "Sales User" in frappe.get_roles() and "Sales Manager" not in frappe.get_roles():
                filters["project"] = active_project

    # Continue with existing get_list logic...
```

---

### Phase 4: Project-Specific Schemas

#### 4.1 Extend CRM Fields Layout for Projects

**File:** `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.json` (add field)

```json
{
  "fieldname": "project",
  "fieldtype": "Link",
  "label": "Project",
  "options": "CRM Project",
  "description": "If set, this layout applies only to the specified project"
}
```

#### 4.2 Update Fields Layout Controller

**File:** `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py`

```python
def get_fields_layout(doctype, type, project=None):
    """Get fields layout for doctype, optionally project-specific"""

    filters = {
        "dt": doctype,
        "type": type
    }

    # Try project-specific layout first
    if project:
        filters["project"] = project
        layout = frappe.get_value("CRM Fields Layout", filters, "layout")
        if layout:
            return json.loads(layout)

    # Fall back to global layout
    filters.pop("project", None)
    layout = frappe.get_value("CRM Fields Layout", filters, "layout")

    return json.loads(layout) if layout else get_default_layout(doctype, type)
```

---

### Phase 5: API Endpoints

#### 5.1 Project Management API

**File:** `crm/api/project.py` (new file)

```python
import frappe
from frappe import _


@frappe.whitelist()
def get_project_context():
    """Get current user's project context"""
    from crm.fcrm.doctype.crm_project.crm_project import (
        get_user_projects,
        get_active_project
    )

    return {
        "active_project": get_active_project(),
        "user_projects": get_user_projects(),
    }


@frappe.whitelist()
def switch_project(project):
    """Switch to a different project"""
    from crm.fcrm.doctype.crm_project.crm_project import set_active_project

    return set_active_project(project)


@frappe.whitelist()
def get_project_stats(project):
    """Get statistics for a project"""
    frappe.has_permission("CRM Project", "read", project, throw=True)

    stats = {
        "total_leads": frappe.db.count("CRM Lead", {"project": project}),
        "total_deals": frappe.db.count("CRM Deal", {"project": project}),
        "total_organizations": frappe.db.count("CRM Organization", {"project": project}),
        "total_tasks": frappe.db.count("CRM Task", {"project": project}),
        "open_tasks": frappe.db.count("CRM Task", {
            "project": project,
            "status": ["in", ["Todo", "In Progress"]]
        }),
    }

    # Deal value stats
    deal_stats = frappe.db.sql("""
        SELECT
            SUM(deal_value) as total_value,
            SUM(expected_deal_value) as expected_value,
            COUNT(*) as count
        FROM `tabCRM Deal`
        WHERE project = %s AND status NOT IN ('Lost', 'Closed')
    """, project, as_dict=True)

    if deal_stats:
        stats.update(deal_stats[0])

    return stats


@frappe.whitelist()
def get_project_team(project):
    """Get team members for a project"""
    frappe.has_permission("CRM Project", "read", project, throw=True)

    members = frappe.get_all(
        "CRM Project Member",
        filters={"parent": project},
        fields=["user", "full_name", "role", "joined_date"],
        order_by="role desc, full_name asc"
    )

    # Enhance with user details
    for member in members:
        user_image = frappe.db.get_value("User", member.user, "user_image")
        member["user_image"] = user_image

    return members
```

---

### Phase 6: Frontend Integration Points

#### 6.1 Project Selector Component (Pseudo-code)

```javascript
// Location: frontend/src/components/ProjectSelector.vue

<template>
  <Dropdown>
    <template #default>
      <Button>
        {{ activeProject?.project_name || 'Select Project' }}
      </Button>
    </template>
    <template #content>
      <div v-for="project in userProjects" :key="project.name">
        <DropdownItem
          @click="switchProject(project.name)"
          :active="project.is_active"
        >
          {{ project.project_name }}
          <Badge v-if="project.is_active">Active</Badge>
        </DropdownItem>
      </div>
    </template>
  </Dropdown>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const activeProject = ref(null)
const userProjects = ref([])

onMounted(async () => {
  const context = await call('crm.api.project.get_project_context')
  activeProject.value = context.active_project
  userProjects.value = context.user_projects
})

async function switchProject(projectName) {
  await call('crm.api.project.switch_project', { project: projectName })
  // Refresh current view
  location.reload()
}
</script>
```

#### 6.2 Global Filter Integration

Modify list views to respect active project:

```javascript
// Before fetching leads/deals/etc:
const filters = {
  ...userFilters,
  // Auto-add project filter if user has active project
  // (unless explicitly filtering by project)
}
```

---

## Migration Strategy

### Step 1: Database Changes
1. Create `CRM Project` and `CRM Project Member` DocTypes
2. Add custom field `project` to CRM Lead, Deal, Task, Organization
3. Add custom field `crm_active_project` to User

### Step 2: Data Migration (Optional)
```python
# If you want to create a default project for existing data
def migrate_existing_data():
    # Create a default project
    default_project = frappe.get_doc({
        "doctype": "CRM Project",
        "project_name": "Default Project",
        "status": "Active",
        "is_default": 1
    }).insert()

    # Add all existing CRM users to default project
    users = frappe.get_all("User", filters={"enabled": 1})
    for user in users:
        roles = frappe.get_roles(user.name)
        if any(role in roles for role in ["Sales User", "Sales Manager", "System Manager"]):
            default_project.append("team_members", {
                "user": user.name,
                "role": "Team Member"
            })

    default_project.save()

    # Optionally assign all existing records to default project
    for doctype in ["CRM Lead", "CRM Deal", "CRM Task", "CRM Organization"]:
        frappe.db.sql(f"""
            UPDATE `tab{doctype}`
            SET project = %s
            WHERE project IS NULL
        """, default_project.name)
```

### Step 3: Permission Updates
1. Update role permissions to respect project membership
2. Add permission queries to enforce project-level access
3. Test with different user roles

### Step 4: Frontend Updates
1. Add project selector to main navigation
2. Update list views to filter by active project
3. Add project field to forms
4. Create project management UI (team, settings, stats)

---

## Key Benefits

1. **Multi-Project Support**: Users can work across multiple initiatives
2. **Data Isolation**: Each project's data can be separate (optional strict mode)
3. **Team Management**: Clear project membership and roles
4. **Flexible Schemas**: Customize fields per project
5. **Backward Compatible**: Existing data continues to work without projects
6. **Progressive Enhancement**: Projects are optional, not mandatory

---

## Configuration Options

### Option A: Strict Project Mode
- All records MUST have a project
- Users can only see records from their projects
- Enforced via permission queries

### Option B: Soft Project Mode (Recommended)
- Projects are optional
- Records without projects are visible to all
- Projects provide organization, not strict isolation
- Sales Managers can see across all projects

---

## Next Steps

1. Review this architecture
2. Decide on Strict vs Soft mode
3. Create DocTypes (Phase 1)
4. Add project fields to core doctypes (Phase 2)
5. Implement API endpoints (Phase 5)
6. Build frontend components (Phase 6)
7. Test with sample data
8. Roll out to production

---

## Questions to Resolve

1. Should project membership be strictly enforced, or should managers see all projects?
2. Should records be required to have a project, or is it optional?
3. Do you want project-specific field layouts, or just data filtering?
4. Should territories be project-specific or global?
5. How should lead-to-deal conversion work across projects?
