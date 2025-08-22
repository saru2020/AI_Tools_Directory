import frappe


def _ensure_category(category_title: str) -> str:
    title = (category_title or "").strip() or "General"
    slug = frappe.scrub(title).strip("-")[:140]
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


@frappe.whitelist()
def run() -> dict:
    """Backfill categories by ensuring Category docs exist and relinking Tools."""
    updated = 0
    tools = frappe.get_all("Tool", fields=["name", "category"])
    for t in tools:
        category_value = t.get("category")
        if not category_value:
            category_value = "General"
        # Category might already be a proper link (existing name). If not, create or map by slug.
        catname = (
            frappe.db.get_value("Category", category_value, "name")
            or frappe.db.get_value("Category", {"slug": frappe.scrub(category_value)}, "name")
            or _ensure_category(category_value)
        )
        if catname and catname != category_value:
            frappe.db.set_value("Tool", t["name"], "category", catname)
            updated += 1
    frappe.db.commit()
    return {"updated": updated}


