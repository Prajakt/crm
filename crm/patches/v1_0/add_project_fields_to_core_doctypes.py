# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add project field to core CRM DocTypes"""

	# Only execute if CRM Project exists
	if not frappe.db.exists("DocType", "CRM Project"):
		return

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
				"read_only": 1,
			}
		],
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
