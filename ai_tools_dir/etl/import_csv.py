import csv
from typing import Optional
import frappe


@frappe.whitelist()
def import_tools(csv_path: str, default_category: str = "Uncategorized") -> dict:
	"""
	Import tools from a normalized CSV with columns:
	name, description, website, category, pricing, logo, source
	"""
	created = 0
	skipped = 0
	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		for row in reader:
			name = (row.get("name") or "").strip()
			website = (row.get("website") or "").strip()
			if not name or not website:
				skipped += 1
				continue
			category_name = (row.get("category") or default_category).strip() or default_category
			# Ensure category
			cat = frappe.db.get_value("Category", {"slug": slugify(category_name)}, "name")
			if not cat:
				cat_doc = frappe.get_doc({
					"doctype": "Category",
					"name": category_name,
					"slug": slugify(category_name),
					"description": category_name,
				})
				cat_doc.insert(ignore_permissions=True)
				cat = cat_doc.name
			# Upsert tool by slug
			slug = slugify(f"{name}")
			tool_name = frappe.db.get_value("Tool", {"slug": slug}, "name")
			if tool_name:
				tool = frappe.get_doc("Tool", tool_name)
				tool.description = row.get("description")
				tool.website = website
				tool.pricing = row.get("pricing")
				tool.logo = row.get("logo")
				tool.category = cat
				tool.save(ignore_permissions=True)
			else:
				tool = frappe.get_doc({
					"doctype": "Tool",
					"tool_name": name,
					"slug": slug,
					"description": row.get("description"),
					"website": website,
					"pricing": row.get("pricing"),
					"logo": row.get("logo"),
					"category": cat,
				})
				tool.insert(ignore_permissions=True)
			created += 1
	return {"created_or_updated": created, "skipped": skipped}


def slugify(text: str) -> str:
	return frappe.scrub(text).strip("-")[:140]
