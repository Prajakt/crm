# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_project_permission_query_conditions(doctype):
	"""
	Get permission query conditions for project-based access control.

	Rules:
	- System Managers and Sales Managers can see all records
	- Sales Users can only see records from their projects
	- Records without a project are visible to all
	"""
	user = frappe.session.user

	# System Managers and Sales Managers see everything
	if "System Manager" in frappe.get_roles(user) or "Sales Manager" in frappe.get_roles(user):
		return None

	# Sales Users: filter by project membership
	if "Sales User" in frappe.get_roles(user):
		# Get all projects user belongs to
		user_projects = frappe.get_all(
			"CRM Project Member",
			filters={"user": user},
			pluck="parent"
		)

		if not user_projects:
			# User not in any project - can only see records without a project
			return f"""(`tab{doctype}`.`project` IS NULL OR `tab{doctype}`.`project` = '')"""

		# User can see records from their projects OR records without a project
		project_list = ", ".join([frappe.db.escape(p) for p in user_projects])
		return f"""(
			`tab{doctype}`.`project` IN ({project_list})
			OR `tab{doctype}`.`project` IS NULL
			OR `tab{doctype}`.`project` = ''
		)"""

	# Default: no additional restrictions
	return None


def has_project_permission(doc, ptype, user):
	"""
	Check if user has permission to access a document based on project membership.

	Rules:
	- System Managers and Sales Managers have full access
	- Sales Users can access records from their projects
	- Records without a project are accessible to all
	"""
	# System Managers and Sales Managers have full access
	if "System Manager" in frappe.get_roles(user) or "Sales Manager" in frappe.get_roles(user):
		return True

	# If document has no project, allow access
	if not doc.get("project"):
		return True

	# Check if user is a member of the document's project
	is_member = frappe.db.exists("CRM Project Member", {
		"parent": doc.project,
		"user": user
	})

	return bool(is_member)
