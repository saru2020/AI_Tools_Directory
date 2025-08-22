import frappe
from frappe.model.document import Document


class Review(Document):
	def validate(self):
		if self.rating is None:
			raise frappe.ValidationError("Rating is required")
		if not (1 <= int(self.rating) <= 5):
			raise frappe.ValidationError("Rating must be between 1 and 5")
