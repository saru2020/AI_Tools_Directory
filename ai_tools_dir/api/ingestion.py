import frappe


def _coerce_names_arg(names):
	# Accept list, tuple, or JSON string (e.g., "[\"slug\"]")
	if names is None:
		return []
	if isinstance(names, (list, tuple)):
		return list(names)
	if isinstance(names, str):
		try:
			parsed = frappe.parse_json(names)
			if isinstance(parsed, list):
				return parsed
			return [str(parsed)] if parsed else []
		except Exception:
			return [names]
	return [names]


@frappe.whitelist()
def bulk_approve(names=None) -> dict:
	names_list = _coerce_names_arg(names)
	if not names_list:
		return {"updated": 0}
	updated = 0
	for name in names_list:
		try:
			doc = frappe.get_doc("Tool", name)
			doc.ingestion_status = "Approved"
			doc.save(ignore_permissions=True)
			updated += 1
		except Exception:
			frappe.db.rollback()
	frappe.db.commit()
	return {"updated": updated}


@frappe.whitelist()
def bulk_reject(names=None) -> dict:
	names_list = _coerce_names_arg(names)
	if not names_list:
		return {"updated": 0}
	updated = 0
	for name in names_list:
		try:
			doc = frappe.get_doc("Tool", name)
			doc.ingestion_status = "Rejected"
			doc.save(ignore_permissions=True)
			updated += 1
		except Exception:
			frappe.db.rollback()
	frappe.db.commit()
	return {"updated": updated}


