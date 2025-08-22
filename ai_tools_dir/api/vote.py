import frappe


@frappe.whitelist(allow_guest=True)
def toggle_upvote(slug: str | None = None):
    slug = slug or frappe.form_dict.get("slug")
    user = frappe.session.user
    if user == "Guest":
        return {"login_required": True}
    tool_name = frappe.db.get_value("Tool", {"slug": slug}, "name")
    if not tool_name:
        frappe.throw("Tool not found", frappe.DoesNotExistError)

    existing = frappe.db.get_value("Tool Vote", {"tool": tool_name, "user": user}, "name")
    if existing:
        frappe.delete_doc("Tool Vote", existing, ignore_permissions=True)
        frappe.db.sql("UPDATE `tabTool` SET upvote_count = GREATEST(COALESCE(upvote_count,0)-1,0) WHERE name=%s", (tool_name,))
        action = "removed"
    else:
        doc = frappe.get_doc({"doctype": "Tool Vote", "tool": tool_name, "user": user})
        doc.insert(ignore_permissions=True)
        frappe.db.sql("UPDATE `tabTool` SET upvote_count = COALESCE(upvote_count,0)+1 WHERE name=%s", (tool_name,))
        action = "added"
    frappe.db.commit()
    return {"status": action}


