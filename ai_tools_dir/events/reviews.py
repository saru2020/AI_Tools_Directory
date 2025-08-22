import frappe


def update_tool_aggregates(doc, method=None):
    """Recompute average_rating and review_count for the linked Tool."""
    tool_name = doc.tool if getattr(doc, "tool", None) else None
    if not tool_name:
        return
    _recompute_for_tool(tool_name)


def backfill_all_tool_aggregates():
    """Periodic job to recompute aggregates for all tools."""
    tool_names = frappe.get_all("Tool", pluck="name")
    for name in tool_names:
        _recompute_for_tool(name)


def _recompute_for_tool(tool_name: str):
    res = frappe.db.sql(
        """
        SELECT COUNT(*) AS cnt, AVG(COALESCE(rating, 0)) AS avg
        FROM `tabReview`
        WHERE tool = %s
        """,
        (tool_name,),
        as_dict=True,
    )[0]
    count = int(res["cnt"] or 0)
    avg = float(res["avg"] or 0) if count else 0.0
    frappe.db.set_value("Tool", tool_name, {
        "review_count": count,
        "average_rating": round(avg, 2),
    })

