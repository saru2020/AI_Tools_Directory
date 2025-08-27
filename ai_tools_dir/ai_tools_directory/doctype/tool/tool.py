import frappe
from frappe.model.document import Document


class Tool(Document):
	@frappe.whitelist()
	def approve(self):
		self.ingestion_status = "Approved"
		self.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "ok", "name": self.name}

	@frappe.whitelist()
	def reject(self):
		self.ingestion_status = "Rejected"
		self.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "ok", "name": self.name}
