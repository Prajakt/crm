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
