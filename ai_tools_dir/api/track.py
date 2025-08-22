import frappe


@frappe.whitelist(allow_guest=True)
def click_tool(slug: str | None = None):
    slug = slug or frappe.form_dict.get("slug")
    if not slug:
        frappe.throw("Missing slug")
    name = frappe.db.get_value("Tool", {"slug": slug}, "name") or frappe.db.exists("Tool", slug)
    if not name:
        frappe.throw("Tool not found", frappe.DoesNotExistError)
    # increment atomically
    frappe.db.sql("UPDATE `tabTool` SET click_count = COALESCE(click_count, 0) + 1 WHERE name = %s", (name,))
    frappe.db.commit()
    return {"ok": True}


