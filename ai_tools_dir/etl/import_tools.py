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


def ensure_category(category_title: str) -> str:
	"""Ensure Category exists and return its name. Defaults to 'General' when empty."""
	title = (category_title or "").strip() or "General"
	slug = slugify(title)
	existing = frappe.db.get_value("Category", {"slug": slug}, "name") or frappe.db.exists("Category", slug)
	if existing:
		return existing
	cat = frappe.get_doc({
		"doctype": "Category",
		"name": title,
		"slug": slug,
		"description": title,
	})
	cat.insert(ignore_permissions=True)
	return cat.name


def import_tools_from_csv(csv_path: str) -> dict:
	if not os.path.exists(csv_path):
		raise FileNotFoundError(csv_path)
	created, updated, skipped = 0, 0, 0
	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)

		def get_first(row: dict, keys: list[str]) -> str:
			for k in keys:
				if k in row and row[k] is not None and str(row[k]).strip() != "":
					return str(row[k])
			return ""

		for row in reader:
			try:
				# Accept both seed schema and Frappe export schema
				domain = get_first(row, ["domain", "Domain"]) or ""
				slug_field = get_first(row, ["slug", "Slug"]) or ""
				website_field = get_first(row, ["website", "Website"]) or ""
				# Prefer domain -> slug column -> fallback to website host
				base_for_slug = domain or slug_field or website_field
				slug = slugify(base_for_slug)
				if not slug:
					skipped += 1
					continue
				name = (get_first(row, ["name", "Tool Name"]) or slug.split(".")[0]).strip()[:140]
				docname = frappe.db.exists("Tool", {"slug": slug})
				if docname:
					doc = frappe.get_doc("Tool", docname)
					updated += 1
				else:
					doc = frappe.new_doc("Tool")
					doc.slug = slug
					created += 1
				doc.tool_name = name
				doc.description = get_first(row, ["description", "Description"]).strip()
				doc.website = website_field.strip()
				category_title = get_first(row, ["category", "Category"]).strip()
				catname = ensure_category(category_title)
				if catname:
					doc.category = catname
				doc.pricing = map_pricing(get_first(row, ["pricing", "Pricing"]))
				# For logo, if Attach Image expects file, store URL in doc.logo as-is; app can fetch later
				doc.logo = get_first(row, ["logo", "Logo"]).strip()
				# Ingestion tracking
				doc.source = (get_first(row, ["source", "Source"]) or "scraper").strip()
				if not getattr(doc, "ingestion_status", None):
					# default new records to Pending Review; preserve existing status on updates
					doc.ingestion_status = "Pending Review"
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
