import frappe


def get_context(context):
    """Log out current session and redirect.

    Accepts optional query param `redirect-to` to control the target location.
    Example: /logout?cmd=web_logout&redirect-to=/
    """
    redirect_to = frappe.form_dict.get("redirect-to") or "/"

    try:
        frappe.local.login_manager.logout()
    except Exception:
        pass

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = redirect_to
    return context


