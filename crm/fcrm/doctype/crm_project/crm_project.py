# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMProject(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_project_member.crm_project_member import CRMProjectMember

		default_currency: DF.Link | None
		default_territory: DF.Link | None
		description: DF.TextEditor | None
		end_date: DF.Date | None
		is_default: DF.Check
		project_code: DF.Data | None
		project_manager: DF.Link | None
		project_name: DF.Data
		start_date: DF.Date | None
		status: DF.Literal["Active", "On Hold", "Completed", "Archived"]
		team_members: DF.Table[CRMProjectMember]
	# end: auto-generated types

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
