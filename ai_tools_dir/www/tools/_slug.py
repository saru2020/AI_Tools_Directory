import frappe


def get_context(context):
    slug = frappe.form_dict.get("slug")
    if not slug:
        frappe.throw("Missing slug")
    docname = frappe.db.get_value("Tool", {"slug": slug}, "name")
    if not docname:
        frappe.throw("Not Found", frappe.DoesNotExistError)
    context.tool = frappe.get_doc("Tool", docname)
    # increment click/view count upon opening detail page
    frappe.db.sql("UPDATE `tabTool` SET click_count = COALESCE(click_count, 0) + 1 WHERE name = %s", (docname,))
    frappe.db.commit()
    # current user's vote state
    user = frappe.session.user
    has_voted = False
    if user and user != "Guest":
        has_voted = bool(frappe.db.exists("Tool Vote", {"tool": docname, "user": user}))
    context.has_voted = has_voted
    context.reviews = frappe.get_all(
        "Review",
        fields=["name", "user", "rating", "comment"],
        filters={"tool": context.tool.name},
        order_by="modified desc",
    )

