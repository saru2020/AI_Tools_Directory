import csv
import os
import frappe
from frappe.utils import cstr


def slugify(domain: str) -> str:
	# Use domain as slug (without scheme), keep dots/dashes
	return cstr(domain).strip().lower()


def map_pricing(val: str) -> str:
	val = (val or "").strip().title()
	if val in {"Free", "Freemium", "Paid"}:
		return val
	return ""


def import_tools_from_csv(csv_path: str) -> dict:
	if not os.path.exists(csv_path):
		raise FileNotFoundError(csv_path)
	created, updated, skipped = 0, 0, 0
	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		for row in reader:
			try:
				slug = slugify(row.get("domain"))
				if not slug:
					skipped += 1
					continue
				name = (row.get("name") or slug.split(".")[0]).strip()[:140]
				docname = frappe.db.exists("Tool", {"slug": slug})
				if docname:
					doc = frappe.get_doc("Tool", docname)
					updated += 1
				else:
					doc = frappe.new_doc("Tool")
					doc.slug = slug
					created += 1
				doc.tool_name = name
				doc.description = (row.get("description") or "").strip()
				doc.website = (row.get("website") or "").strip()
				doc.category = (row.get("category") or "").strip()
				doc.pricing = map_pricing(row.get("pricing") or "")
				# For logo, if Attach Image expects file, store URL in doc.logo as-is; app can fetch later
				doc.logo = (row.get("logo") or "").strip()
				doc.save(ignore_permissions=True)
			except Exception:
				frappe.db.rollback()
				skipped += 1
				continue
	frappe.db.commit()
	return {"created": created, "updated": updated, "skipped": skipped}


@frappe.whitelist()
def run(csv_path: str = None) -> dict:
	csv_path = csv_path or frappe.get_site_path("..", "..", "ai_tools_seed.csv")
	return import_tools_from_csv(csv_path)
