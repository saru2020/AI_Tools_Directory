import frappe


def get_context(context):
    slug = frappe.form_dict.get("slug")
    if not slug:
        frappe.throw("Missing slug")
    catname = frappe.db.get_value("Category", {"slug": slug}, "name")
    if not catname:
        frappe.throw("Not Found", frappe.DoesNotExistError)
    context.category = frappe.get_doc("Category", catname)
    context.tools = frappe.get_all(
        "Tool",
        fields=["name", "tool_name", "slug", "pricing", "logo", "average_rating"],
        filters={"category": context.category.name},
        order_by="modified desc",
        limit=100,
    )

