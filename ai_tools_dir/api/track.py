import frappe


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def click_tool(slug: str | None = None):
    """Track tool clicks - supports both GET and POST methods"""
    # Get slug from various possible sources
    if not slug:
        slug = frappe.form_dict.get("slug")
    if not slug:
        # Try to get from request body for POST requests
        try:
            import json
            if frappe.request and frappe.request.get_data():
                data = json.loads(frappe.request.get_data())
                slug = data.get("slug")
        except:
            pass
    
    if not slug:
        frappe.throw("Missing slug")
    
    # Find the tool by slug
    name = frappe.db.get_value("Tool", {"slug": slug}, "name")
    if not name:
        frappe.throw("Tool not found", frappe.DoesNotExistError)
    
    try:
        # Check if click_count column exists in the table
        try:
            # Try to get current click_count value first
            current_count = frappe.db.get_value("Tool", name, "click_count") or 0
            # Update the click_count
            frappe.db.set_value("Tool", name, "click_count", current_count + 1)
            frappe.db.commit()
            return {"ok": True, "message": "Click tracked successfully"}
        except Exception as db_error:
            # If direct update fails, try using SQL with error handling
            try:
                frappe.db.sql("UPDATE `tabTool` SET click_count = COALESCE(click_count, 0) + 1 WHERE name = %s", (name,))
                frappe.db.commit()
                return {"ok": True, "message": "Click tracked successfully"}
            except Exception as sql_error:
                frappe.log_error(f"SQL update failed for tool {slug}: {str(sql_error)}")
                # Try to create the column if it doesn't exist
                try:
                    frappe.db.sql("ALTER TABLE `tabTool` ADD COLUMN `click_count` INT DEFAULT 0")
                    frappe.db.sql("UPDATE `tabTool` SET click_count = 1 WHERE name = %s", (name,))
                    frappe.db.commit()
                    return {"ok": True, "message": "Click tracked successfully (column created)"}
                except Exception as alter_error:
                    frappe.log_error(f"Failed to create click_count column: {str(alter_error)}")
                    return {"ok": False, "error": "Database schema issue"}
    except Exception as e:
        frappe.log_error(f"Error tracking click for tool {slug}: {str(e)}")
        return {"ok": False, "error": str(e)}


