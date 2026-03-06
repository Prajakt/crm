# Phases 4, 5, 6 Implementation - Complete ✓

## What Was Implemented

Phases 4, 5, and 6 complete the CRM Project workspace functionality with project-specific schemas, comprehensive APIs, and full backend support for frontend integration.

---

## Phase 4: Project-Specific Schemas

### Overview
Enables project-specific field layouts, allowing different projects to have customized form layouts and field configurations.

### Implementation

#### 1. Updated CRM Fields Layout DocType

**Modified:** `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.json`

**Added Field:**
```json
{
  "fieldname": "project",
  "fieldtype": "Link",
  "label": "Project",
  "options": "CRM Project",
  "description": "If set, this layout applies only to the specified project. Leave empty for global layout.",
  "in_list_view": 1,
  "in_standard_filter": 1
}
```

**Benefits:**
- Project-specific form layouts
- Different field arrangements per project
- Isolated customizations

#### 2. Updated Fields Layout Controller

**Modified:** `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py`

**Enhanced Functions:**

##### `get_fields_layout(doctype, type, parent_doctype, project)`

Now supports project parameter with fallback logic:

```python
@frappe.whitelist()
def get_fields_layout(doctype: str, type: str, parent_doctype: str | None = None, project: str | None = None):
    # Priority 1: Project-specific layout
    if project and frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type, "project": project}):
        layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type, "project": project})
    # Priority 2: Global layout
    elif frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type, "project": ["in", [None, ""]]}):
        layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type, "project": ["in", [None, ""]]})
```

**Resolution Order:**
1. Project-specific layout (if project provided and exists)
2. Global layout (no project specified)
3. Default layout (generated from DocType)

##### `save_fields_layout(doctype, type, layout, project)`

Now saves project-specific layouts:

```python
@frappe.whitelist()
def save_fields_layout(doctype: str, type: str, layout: str, project: str | None = None):
    filters = {"dt": doctype, "type": type}
    if project:
        filters["project"] = project
    else:
        filters["project"] = ["in", [None, ""]]

    # Create or update layout
    if frappe.db.exists("CRM Fields Layout", filters):
        doc = frappe.get_doc("CRM Fields Layout", filters)
    else:
        doc = frappe.new_doc("CRM Fields Layout")

    doc.update({
        "dt": doctype,
        "type": type,
        "layout": layout,
        "project": project,
    })
    doc.save(ignore_permissions=True)
```

### Use Cases

#### Global Layout
```python
# Create global layout (no project)
save_fields_layout(
    doctype="CRM Lead",
    type="Quick Entry",
    layout=json.dumps(layout_config)
)
```

#### Project-Specific Layout
```python
# Create project-specific layout
save_fields_layout(
    doctype="CRM Lead",
    type="Quick Entry",
    layout=json.dumps(custom_layout),
    project="Project A"
)

# Get project-specific layout
layout = get_fields_layout(
    doctype="CRM Lead",
    type="Quick Entry",
    project="Project A"  # Will use Project A's layout if exists, else global
)
```

---

## Phase 5: Enhanced Project APIs

### Overview
Comprehensive API endpoints for project management, dashboards, team management, and analytics.

### API Endpoints

#### 1. **Project Dashboard** (New)

**Endpoint:** `crm.api.project.get_project_dashboard`

**Returns:**
```python
{
    "project": {
        "name": "Project A",
        "project_name": "Q1 Sales Campaign",
        "project_code": "Q1-2024",
        "status": "Active",
        "project_manager": "manager@example.com",
        "start_date": "2024-01-01",
        "end_date": "2024-03-31"
    },
    "stats": {
        "total_leads": 150,
        "total_deals": 45,
        "total_organizations": 30,
        "total_tasks": 75,
        "open_tasks": 25,
        "total_value": 500000,
        "expected_value": 750000
    },
    "lead_status_breakdown": [
        {"status": "Open", "count": 80},
        {"status": "Qualified", "count": 40},
        {"status": "Lost", "count": 30}
    ],
    "deal_status_breakdown": [
        {"status": "Proposal", "count": 20, "total_value": 300000},
        {"status": "Negotiation", "count": 15, "total_value": 200000}
    ],
    "recent_leads": [...],
    "recent_deals": [...],
    "team_performance": [
        {"user": "sales1@example.com", "leads_count": 50, "deals_count": 15}
    ]
}
```

**Usage:**
```javascript
frappe.call({
    method: 'crm.api.project.get_project_dashboard',
    args: { project: 'Project A' },
    callback: function(r) {
        console.log('Dashboard:', r.message);
    }
});
```

#### 2. **Get All Projects** (New)

**Endpoint:** `crm.api.project.get_all_projects`

**Returns:** All projects accessible to current user

```python
[
    {
        "name": "Project A",
        "project_name": "Q1 Sales Campaign",
        "project_code": "Q1-2024",
        "status": "Active",
        "project_manager": "manager@example.com",
        "team_size": 5
    },
    ...
]
```

**Access Control:**
- System Managers & Sales Managers: See all projects
- Sales Users: See only projects they belong to

#### 3. **Team Management APIs** (New)

##### Add Team Member
```python
frappe.call({
    method: 'crm.api.project.add_team_member',
    args: {
        project: 'Project A',
        user: 'sales1@example.com',
        role: 'Team Member'  # or 'Project Manager', 'Team Lead'
    }
});
```

##### Remove Team Member
```python
frappe.call({
    method: 'crm.api.project.remove_team_member',
    args: {
        project: 'Project A',
        user: 'sales1@example.com'
    }
});
```

##### Update Team Member Role
```python
frappe.call({
    method: 'crm.api.project.update_team_member_role',
    args: {
        project: 'Project A',
        user: 'sales1@example.com',
        role: 'Team Lead'
    }
});
```

#### 4. **Project Activity Feed** (New)

**Endpoint:** `crm.api.project.get_project_activity`

**Returns:** Recent activity timeline

```python
[
    {
        "type": "Lead",
        "doctype": "CRM Lead",
        "name": "CRM-LEAD-2024-0001",
        "title": "John Doe",
        "status": "Qualified",
        "owner": "sales1@example.com",
        "timestamp": "2024-03-06 10:30:00"
    },
    {
        "type": "Deal",
        "doctype": "CRM Deal",
        "name": "CRM-DEAL-2024-0001",
        "title": "Acme Corp",
        "status": "Proposal",
        "owner": "sales2@example.com",
        "value": 50000,
        "timestamp": "2024-03-06 09:15:00"
    },
    ...
]
```

#### 5. **Project Reports** (New)

**Endpoint:** `crm.api.project.get_project_reports`

**Returns:** Analytics and KPIs

```python
{
    "conversion_rate": 35.5,  # Lead to Deal conversion %
    "win_rate": 42.3,         # Deal win rate %
    "avg_deal_value": 28500,
    "leads_by_source": [
        {"source": "Website", "count": 45},
        {"source": "Referral", "count": 30},
        {"source": "Cold Call", "count": 20}
    ],
    "monthly_trend": [
        {"month": "2024-03", "leads": 50, "deals": 15},
        {"month": "2024-02", "leads": 45, "deals": 12},
        {"month": "2024-01", "leads": 40, "deals": 10}
    ]
}
```

---

## Phase 6: Project Settings & Configuration

### Overview
APIs for managing project settings, copying layouts, and configuring project-specific features.

### API Endpoints

#### 1. **Get Project Settings**

**Endpoint:** `crm.api.project.get_project_settings`

**Returns:**
```python
{
    "project": {
        "name": "Project A",
        "project_name": "Q1 Sales Campaign",
        "project_code": "Q1-2024",
        "status": "Active",
        "default_territory": "North America",
        "default_currency": "USD",
        "is_default": 0
    },
    "layouts": [
        {
            "name": "CRM Lead-Quick Entry-Project A",
            "dt": "CRM Lead",
            "type": "Quick Entry",
            "modified": "2024-03-06 10:00:00"
        }
    ],
    "views": [
        {
            "name": "View-001",
            "dt": "CRM Lead",
            "type": "list",
            "label": "My Leads",
            "is_default": 1
        }
    ]
}
```

#### 2. **Update Project Settings**

**Endpoint:** `crm.api.project.update_project_settings`

**Usage:**
```javascript
frappe.call({
    method: 'crm.api.project.update_project_settings',
    args: {
        project: 'Project A',
        settings: JSON.stringify({
            default_territory: 'Europe',
            default_currency: 'EUR',
            status: 'On Hold'
        })
    }
});
```

**Allowed Fields:**
- `default_territory`
- `default_currency`
- `is_default`
- `status`

#### 3. **Copy Project Layout**

**Endpoint:** `crm.api.project.copy_project_layout`

**Usage:**
```javascript
frappe.call({
    method: 'crm.api.project.copy_project_layout',
    args: {
        source_project: 'Project A',
        target_project: 'Project B',
        doctype: 'CRM Lead',
        layout_type: 'Quick Entry'
    },
    callback: function(r) {
        frappe.show_alert('Layout copied successfully');
    }
});
```

**Use Cases:**
- Clone layouts from template projects
- Standardize layouts across projects
- Quick project setup

---

## Complete API Reference

### Project Context & Switching

| Endpoint | Description | Returns |
|----------|-------------|---------|
| `get_project_context()` | Get user's active project and all projects | Active project + project list |
| `switch_project(project)` | Switch user's active project | Confirmation message |
| `get_active_project(user)` | Get user's active project | Project name |

### Project Information

| Endpoint | Description | Returns |
|----------|-------------|---------|
| `get_all_projects()` | Get all accessible projects | Project list |
| `get_project_stats(project)` | Get project statistics | Stats object |
| `get_project_team(project)` | Get project team members | Team member list |
| `get_project_dashboard(project)` | Get comprehensive dashboard data | Dashboard object |
| `get_project_activity(project, limit)` | Get recent activity | Activity feed |
| `get_project_reports(project)` | Get analytics and KPIs | Reports object |

### Team Management

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `add_team_member(project, user, role)` | Add member to project | project, user, role |
| `remove_team_member(project, user)` | Remove member from project | project, user |
| `update_team_member_role(project, user, role)` | Update member's role | project, user, role |

### Settings & Configuration

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `get_project_settings(project)` | Get project settings | project |
| `update_project_settings(project, settings)` | Update project settings | project, settings JSON |
| `copy_project_layout(source, target, doctype, type)` | Copy layout between projects | 4 parameters |

### Field Layouts

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `get_fields_layout(doctype, type, parent_doctype, project)` | Get field layout | doctype, type, optional project |
| `save_fields_layout(doctype, type, layout, project)` | Save field layout | doctype, type, layout JSON, optional project |

---

## Frontend Integration Examples

### 1. Project Selector Component

```javascript
// Get all projects
const { data } = await frappe.call('crm.api.project.get_all_projects');
const projects = data.message;

// Render dropdown
<select onChange={handleProjectChange}>
  {projects.map(p => (
    <option value={p.name}>{p.project_name}</option>
  ))}
</select>

// Switch project
async function handleProjectChange(projectName) {
  await frappe.call({
    method: 'crm.api.project.switch_project',
    args: { project: projectName }
  });
  window.location.reload();  // Refresh to apply new project context
}
```

### 2. Project Dashboard

```javascript
// Get dashboard data
const { data } = await frappe.call({
  method: 'crm.api.project.get_project_dashboard',
  args: { project: currentProject }
});

const dashboard = data.message;

// Render stats
<div className="stats-grid">
  <StatCard title="Total Leads" value={dashboard.stats.total_leads} />
  <StatCard title="Total Deals" value={dashboard.stats.total_deals} />
  <StatCard title="Pipeline Value" value={dashboard.stats.total_value} />
  <StatCard title="Open Tasks" value={dashboard.stats.open_tasks} />
</div>

// Render charts
<PieChart data={dashboard.lead_status_breakdown} />
<BarChart data={dashboard.deal_status_breakdown} />
```

### 3. Project Settings Panel

```javascript
// Get current settings
const { data } = await frappe.call({
  method: 'crm.api.project.get_project_settings',
  args: { project: currentProject }
});

const settings = data.message.project;

// Update settings
async function saveSettings(newSettings) {
  await frappe.call({
    method: 'crm.api.project.update_project_settings',
    args: {
      project: currentProject,
      settings: JSON.stringify(newSettings)
    }
  });
  frappe.show_alert('Settings saved');
}
```

### 4. Team Management UI

```javascript
// Get team
const { data } = await frappe.call({
  method: 'crm.api.project.get_project_team',
  args: { project: currentProject }
});

const team = data.message;

// Add member
async function addMember(email, role) {
  await frappe.call({
    method: 'crm.api.project.add_team_member',
    args: {
      project: currentProject,
      user: email,
      role: role
    }
  });
  refreshTeam();
}

// Remove member
async function removeMember(email) {
  await frappe.call({
    method: 'crm.api.project.remove_team_member',
    args: {
      project: currentProject,
      user: email
    }
  });
  refreshTeam();
}
```

### 5. Activity Feed

```javascript
// Get activity
const { data } = await frappe.call({
  method: 'crm.api.project.get_project_activity',
  args: {
    project: currentProject,
    limit: 50
  }
});

const activities = data.message;

// Render timeline
<Timeline>
  {activities.map(activity => (
    <TimelineItem
      type={activity.type}
      title={activity.title}
      status={activity.status}
      owner={activity.owner}
      timestamp={activity.timestamp}
      link={`/app/${activity.doctype}/${activity.name}`}
    />
  ))}
</Timeline>
```

### 6. Project Reports

```javascript
// Get reports
const { data } = await frappe.call({
  method: 'crm.api.project.get_project_reports',
  args: { project: currentProject }
});

const reports = data.message;

// Render KPIs
<KPIGrid>
  <KPI title="Conversion Rate" value={`${reports.conversion_rate.toFixed(1)}%`} />
  <KPI title="Win Rate" value={`${reports.win_rate.toFixed(1)}%`} />
  <KPI title="Avg Deal Value" value={`$${reports.avg_deal_value.toLocaleString()}`} />
</KPIGrid>

// Render charts
<BarChart
  title="Leads by Source"
  data={reports.leads_by_source}
  xKey="source"
  yKey="count"
/>

<LineChart
  title="Monthly Trend"
  data={reports.monthly_trend}
  xKey="month"
  series={[
    { key: 'leads', label: 'Leads', color: 'blue' },
    { key: 'deals', label: 'Deals', color: 'green' }
  ]}
/>
```

---

## Testing Guide

### Test Project-Specific Layouts

```python
import frappe
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import save_fields_layout, get_fields_layout

# Create global layout
global_layout = [{"name": "tab1", "sections": [...]}]
save_fields_layout("CRM Lead", "Quick Entry", json.dumps(global_layout))

# Create project-specific layout
project_layout = [{"name": "tab1", "sections": [...custom fields...]}]
save_fields_layout("CRM Lead", "Quick Entry", json.dumps(project_layout), "Project A")

# Get layout without project - returns global
layout1 = get_fields_layout("CRM Lead", "Quick Entry")
print("Global layout:", layout1)

# Get layout with project - returns project-specific
layout2 = get_fields_layout("CRM Lead", "Quick Entry", project="Project A")
print("Project A layout:", layout2)

# Get layout for project without custom layout - returns global
layout3 = get_fields_layout("CRM Lead", "Quick Entry", project="Project B")
print("Project B layout (fallback to global):", layout3)
```

### Test Dashboard API

```python
import frappe

# Get dashboard data
dashboard = frappe.call('crm.api.project.get_project_dashboard', project='Project A')

print(f"Total Leads: {dashboard['stats']['total_leads']}")
print(f"Total Deals: {dashboard['stats']['total_deals']}")
print(f"Conversion Rate: {dashboard['stats'].get('conversion_rate', 0)}%")
print(f"Team Size: {len(dashboard['team_performance'])}")
```

### Test Team Management

```python
import frappe

# Add team member
frappe.call('crm.api.project.add_team_member',
    project='Project A',
    user='sales1@example.com',
    role='Team Member'
)

# Update role
frappe.call('crm.api.project.update_team_member_role',
    project='Project A',
    user='sales1@example.com',
    role='Team Lead'
)

# Get team
team = frappe.call('crm.api.project.get_project_team', project='Project A')
print(f"Team members: {len(team)}")

# Remove member
frappe.call('crm.api.project.remove_team_member',
    project='Project A',
    user='sales1@example.com'
)
```

---

## Performance Considerations

### Caching Strategies

1. **User Projects Cache**
```python
# Cache user's projects for 5 minutes
cache_key = f"user_projects:{user}"
projects = frappe.cache().hget(cache_key, expires_in_sec=300)
```

2. **Active Project Cache**
```python
# Already implemented in Phase 1
frappe.cache().hset("active_project", user, project)
```

3. **Dashboard Cache**
```python
# Cache dashboard data for 1 minute
cache_key = f"project_dashboard:{project}"
frappe.cache().hset(cache_key, dashboard_data, expires_in_sec=60)
```

### Database Indexes

Add indexes for better query performance:

```sql
-- Project field indexes
ALTER TABLE `tabCRM Lead` ADD INDEX idx_project (project);
ALTER TABLE `tabCRM Deal` ADD INDEX idx_project (project);
ALTER TABLE `tabCRM Task` ADD INDEX idx_project (project);
ALTER TABLE `tabCRM Organization` ADD INDEX idx_project (project);

-- Project member lookup
ALTER TABLE `tabCRM Project Member` ADD INDEX idx_user (user);
ALTER TABLE `tabCRM Project Member` ADD INDEX idx_parent (parent);

-- Fields layout lookup
ALTER TABLE `tabCRM Fields Layout` ADD INDEX idx_dt_type_project (dt, type, project);
```

---

## Migration & Installation

From your Frappe bench directory:

```bash
cd /path/to/frappe-bench

# Pull latest changes
cd apps/crm
git pull

# Run migrations
cd ../..
bench --site [your-site] migrate

# Clear cache
bench --site [your-site] clear-cache

# Restart bench
bench restart
```

**Note:** Phase 4 requires database migration to add `project` field to CRM Fields Layout.

---

## Summary

### Phase 4 ✅
- Project-specific field layouts
- Layout inheritance (project → global → default)
- Isolated form customizations per project

### Phase 5 ✅
- Comprehensive dashboard API
- Team management APIs
- Activity feed
- Analytics and reports
- Enhanced project context

### Phase 6 ✅
- Project settings management
- Layout copying between projects
- Configuration APIs
- Full backend support for frontend

### Total Implementation

**Files Modified: 3**
- `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.json` - Added project field
- `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py` - Enhanced layout functions
- `crm/api/project.py` - Added 10+ new API endpoints

**New API Endpoints: 12**
1. `get_project_dashboard` - Dashboard data
2. `get_all_projects` - All accessible projects
3. `add_team_member` - Add member
4. `remove_team_member` - Remove member
5. `update_team_member_role` - Update role
6. `get_project_activity` - Activity feed
7. `get_project_reports` - Analytics
8. `get_project_settings` - Settings
9. `update_project_settings` - Update settings
10. `copy_project_layout` - Copy layouts

**Enhanced API Endpoints: 2**
1. `get_fields_layout` - Now supports project parameter
2. `save_fields_layout` - Now supports project parameter

---

## Complete Feature List

✅ **Phase 1**: Project entity, team management, active project
✅ **Phase 2**: Auto-assignment, field integration, standard filters
✅ **Phase 3**: Permissions, access control, data isolation
✅ **Phase 4**: Project-specific schemas and layouts
✅ **Phase 5**: Comprehensive APIs and dashboards
✅ **Phase 6**: Settings management and configuration

**All backend implementation is COMPLETE!**

Ready for frontend development and UI integration!
