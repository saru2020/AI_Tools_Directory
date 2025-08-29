from __future__ import annotations

import frappe


def get_context(context):
    # Request params
    q = (frappe.form_dict.get("q") or "").strip()
    sort = frappe.form_dict.get("sort") or "modified desc"
    category_slug = frappe.form_dict.get("category") or ""
    try:
        page = int(frappe.form_dict.get("page") or 1)
    except Exception:
        page = 1

    page_size = 24
    start = (page - 1) * page_size

    # Categories
    categories = frappe.get_all("Category", fields=["name", "slug"])  # safe

    # Build filters
    filters = []
    if q:
        filters.append(["tool_name", "like", f"%{q}%"])  # safe like
    if category_slug:
        category_name = frappe.db.get_value("Category", {"slug": category_slug}, "name")
        if category_name:
            filters.append(["category", "=", category_name])
    filters.append(["ingestion_status", "=", "Approved"])

    # Query tools
    tools = frappe.get_all(
        "Tool",
        fields=[
            "name",
            "tool_name",
            "slug",
            "pricing",
            "logo",
            "average_rating",
            "upvote_count",
        ],
        filters=filters,
        order_by=sort,
        start=start,
        limit=page_size,
    )

    # My votes (if logged in)
    my_voted_tools = []
    if frappe.session.user and frappe.session.user != "Guest":
        votes = frappe.get_all("Tool Vote", fields=["tool"], filters={"user": frappe.session.user})
        my_voted_tools = [v["tool"] for v in votes]

    # Annotate tools with voted flag to avoid complex template logic
    voted_set = set(my_voted_tools)
    for t in tools:
        t["voted_by_me"] = t.get("name") in voted_set

    total = frappe.db.count("Tool", filters=filters)
    total_pages = (total + page_size - 1) // page_size

    # Expose to template
    context.categories = categories
    context.q = q
    context.sort = sort
    context.category_slug = category_slug
    context.page = page
    context.page_size = page_size
    context.tools = tools
    context.total = total
    context.total_pages = total_pages
    context.my_voted_tools = my_voted_tools

    return context


