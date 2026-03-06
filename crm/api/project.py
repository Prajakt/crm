# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

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


@frappe.whitelist()
def get_project_dashboard(project):
	"""Get comprehensive dashboard data for a project"""
	frappe.has_permission("CRM Project", "read", project, throw=True)

	# Get basic project info
	project_doc = frappe.get_doc("CRM Project", project)

	# Get statistics
	stats = get_project_stats(project)

	# Get lead status breakdown
	lead_status_breakdown = frappe.db.sql("""
		SELECT
			status,
			COUNT(*) as count
		FROM `tabCRM Lead`
		WHERE project = %s
		GROUP BY status
		ORDER BY count DESC
	""", project, as_dict=True)

	# Get deal status breakdown
	deal_status_breakdown = frappe.db.sql("""
		SELECT
			status,
			COUNT(*) as count,
			SUM(deal_value) as total_value
		FROM `tabCRM Deal`
		WHERE project = %s
		GROUP BY status
		ORDER BY count DESC
	""", project, as_dict=True)

	# Get recent activity (last 10 leads/deals)
	recent_leads = frappe.get_all(
		"CRM Lead",
		filters={"project": project},
		fields=["name", "lead_name", "status", "modified"],
		order_by="modified desc",
		limit=10
	)

	recent_deals = frappe.get_all(
		"CRM Deal",
		filters={"project": project},
		fields=["name", "organization", "deal_value", "status", "modified"],
		order_by="modified desc",
		limit=10
	)

	# Get team performance
	team_performance = frappe.db.sql("""
		SELECT
			l.lead_owner as user,
			COUNT(l.name) as leads_count,
			COUNT(d.name) as deals_count
		FROM `tabCRM Lead` l
		LEFT JOIN `tabCRM Deal` d ON d.lead = l.name
		WHERE l.project = %s
		GROUP BY l.lead_owner
		ORDER BY deals_count DESC, leads_count DESC
	""", project, as_dict=True)

	return {
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
			"project_code": project_doc.project_code,
			"status": project_doc.status,
			"project_manager": project_doc.project_manager,
			"start_date": project_doc.start_date,
			"end_date": project_doc.end_date,
		},
		"stats": stats,
		"lead_status_breakdown": lead_status_breakdown,
		"deal_status_breakdown": deal_status_breakdown,
		"recent_leads": recent_leads,
		"recent_deals": recent_deals,
		"team_performance": team_performance,
	}


@frappe.whitelist()
def get_all_projects():
	"""Get all projects accessible to the current user"""
	user = frappe.session.user

	# System Managers and Sales Managers see all projects
	if "System Manager" in frappe.get_roles(user) or "Sales Manager" in frappe.get_roles(user):
		projects = frappe.get_all(
			"CRM Project",
			fields=["name", "project_name", "project_code", "status", "project_manager"],
			order_by="modified desc"
		)
	else:
		# Sales Users see only their projects
		user_projects = frappe.get_all(
			"CRM Project Member",
			filters={"user": user},
			pluck="parent"
		)

		if user_projects:
			projects = frappe.get_all(
				"CRM Project",
				filters={"name": ["in", user_projects]},
				fields=["name", "project_name", "project_code", "status", "project_manager"],
				order_by="modified desc"
			)
		else:
			projects = []

	# Enhance with team size
	for project in projects:
		team_size = frappe.db.count("CRM Project Member", {"parent": project.name})
		project["team_size"] = team_size

	return projects


@frappe.whitelist()
def add_team_member(project, user, role="Team Member"):
	"""Add a team member to a project"""
	frappe.has_permission("CRM Project", "write", project, throw=True)

	project_doc = frappe.get_doc("CRM Project", project)

	# Check if user already exists
	existing = [m for m in project_doc.team_members if m.user == user]
	if existing:
		frappe.throw(_("User {0} is already a member of this project").format(user))

	# Add new member
	project_doc.append("team_members", {
		"user": user,
		"role": role
	})

	project_doc.save()

	return {"message": "Team member added successfully"}


@frappe.whitelist()
def remove_team_member(project, user):
	"""Remove a team member from a project"""
	frappe.has_permission("CRM Project", "write", project, throw=True)

	project_doc = frappe.get_doc("CRM Project", project)

	# Remove member
	project_doc.team_members = [m for m in project_doc.team_members if m.user != user]

	project_doc.save()

	# Clear user's active project if this was it
	if frappe.db.get_value("User", user, "crm_active_project") == project:
		frappe.db.set_value("User", user, "crm_active_project", None)
		frappe.cache().hdel("active_project", user)

	return {"message": "Team member removed successfully"}


@frappe.whitelist()
def update_team_member_role(project, user, role):
	"""Update a team member's role"""
	frappe.has_permission("CRM Project", "write", project, throw=True)

	project_doc = frappe.get_doc("CRM Project", project)

	# Update role
	for member in project_doc.team_members:
		if member.user == user:
			member.role = role
			break
	else:
		frappe.throw(_("User {0} is not a member of this project").format(user))

	project_doc.save()

	return {"message": "Team member role updated successfully"}


@frappe.whitelist()
def get_project_settings(project):
	"""Get project settings and configurations"""
	frappe.has_permission("CRM Project", "read", project, throw=True)

	project_doc = frappe.get_doc("CRM Project", project)

	# Get project-specific field layouts
	project_layouts = frappe.get_all(
		"CRM Fields Layout",
		filters={"project": project},
		fields=["name", "dt", "type", "modified"],
		order_by="dt, type"
	)

	# Get project-specific views
	project_views = frappe.get_all(
		"CRM View Settings",
		filters={"project": project} if frappe.db.exists("DocField", {"parent": "CRM View Settings", "fieldname": "project"}) else {},
		fields=["name", "dt", "type", "label", "is_default"],
		order_by="dt, type"
	)

	return {
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
			"project_code": project_doc.project_code,
			"status": project_doc.status,
			"default_territory": project_doc.default_territory,
			"default_currency": project_doc.default_currency,
			"is_default": project_doc.is_default,
		},
		"layouts": project_layouts,
		"views": project_views,
	}


@frappe.whitelist()
def update_project_settings(project, settings):
	"""Update project settings"""
	frappe.has_permission("CRM Project", "write", project, throw=True)

	settings = frappe.parse_json(settings)

	project_doc = frappe.get_doc("CRM Project", project)

	# Update allowed fields
	allowed_fields = ["default_territory", "default_currency", "is_default", "status"]
	for field in allowed_fields:
		if field in settings:
			setattr(project_doc, field, settings[field])

	project_doc.save()

	return {"message": "Project settings updated successfully"}


@frappe.whitelist()
def get_project_activity(project, limit=50):
	"""Get recent activity for a project"""
	frappe.has_permission("CRM Project", "read", project, throw=True)

	activities = []

	# Get recent leads
	leads = frappe.get_all(
		"CRM Lead",
		filters={"project": project},
		fields=["name", "lead_name", "status", "lead_owner", "creation", "modified"],
		order_by="modified desc",
		limit=limit // 2
	)

	for lead in leads:
		activities.append({
			"type": "Lead",
			"doctype": "CRM Lead",
			"name": lead.name,
			"title": lead.lead_name,
			"status": lead.status,
			"owner": lead.lead_owner,
			"timestamp": lead.modified,
		})

	# Get recent deals
	deals = frappe.get_all(
		"CRM Deal",
		filters={"project": project},
		fields=["name", "organization", "status", "deal_owner", "deal_value", "creation", "modified"],
		order_by="modified desc",
		limit=limit // 2
	)

	for deal in deals:
		activities.append({
			"type": "Deal",
			"doctype": "CRM Deal",
			"name": deal.name,
			"title": deal.organization,
			"status": deal.status,
			"owner": deal.deal_owner,
			"value": deal.deal_value,
			"timestamp": deal.modified,
		})

	# Sort by timestamp
	activities.sort(key=lambda x: x["timestamp"], reverse=True)

	return activities[:limit]


@frappe.whitelist()
def copy_project_layout(source_project, target_project, doctype, layout_type):
	"""Copy field layout from one project to another"""
	frappe.has_permission("CRM Project", "read", source_project, throw=True)
	frappe.has_permission("CRM Project", "write", target_project, throw=True)

	# Get source layout
	source_layout = frappe.db.get_value(
		"CRM Fields Layout",
		{"dt": doctype, "type": layout_type, "project": source_project},
		"layout"
	)

	if not source_layout:
		frappe.throw(_("Source layout not found"))

	# Save to target project
	from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import save_fields_layout

	save_fields_layout(doctype, layout_type, source_layout, target_project)

	return {"message": "Layout copied successfully"}


@frappe.whitelist()
def get_project_reports(project):
	"""Get project-specific reports and analytics"""
	frappe.has_permission("CRM Project", "read", project, throw=True)

	# Lead conversion rate
	total_leads = frappe.db.count("CRM Lead", {"project": project})
	converted_leads = frappe.db.count("CRM Lead", {"project": project, "converted": 1})
	conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

	# Deal win rate
	total_deals = frappe.db.count("CRM Deal", {"project": project})
	won_deals = frappe.db.sql("""
		SELECT COUNT(*) as count
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE d.project = %s AND s.type = 'Won'
	""", project, as_dict=True)
	win_rate = (won_deals[0].count / total_deals * 100) if total_deals > 0 and won_deals else 0

	# Average deal value
	avg_deal_value = frappe.db.sql("""
		SELECT AVG(deal_value) as avg_value
		FROM `tabCRM Deal`
		WHERE project = %s AND deal_value > 0
	""", project, as_dict=True)

	# Leads by source
	leads_by_source = frappe.db.sql("""
		SELECT source, COUNT(*) as count
		FROM `tabCRM Lead`
		WHERE project = %s AND source IS NOT NULL
		GROUP BY source
		ORDER BY count DESC
		LIMIT 10
	""", project, as_dict=True)

	# Monthly trend (last 6 months)
	monthly_trend = frappe.db.sql("""
		SELECT
			DATE_FORMAT(creation, '%%Y-%%m') as month,
			COUNT(CASE WHEN doctype = 'CRM Lead' THEN 1 END) as leads,
			COUNT(CASE WHEN doctype = 'CRM Deal' THEN 1 END) as deals
		FROM (
			SELECT 'CRM Lead' as doctype, creation FROM `tabCRM Lead` WHERE project = %s
			UNION ALL
			SELECT 'CRM Deal' as doctype, creation FROM `tabCRM Deal` WHERE project = %s
		) combined
		WHERE creation >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
		GROUP BY month
		ORDER BY month DESC
	""", (project, project), as_dict=True)

	return {
		"conversion_rate": conversion_rate,
		"win_rate": win_rate,
		"avg_deal_value": avg_deal_value[0].avg_value if avg_deal_value and avg_deal_value[0].avg_value else 0,
		"leads_by_source": leads_by_source,
		"monthly_trend": monthly_trend,
	}
