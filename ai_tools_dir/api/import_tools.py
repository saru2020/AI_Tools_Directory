import os
import tempfile
import frappe
from frappe.utils.file_manager import get_file


@frappe.whitelist()
def import_from_uploaded(file_url: str) -> dict:
	"""Accept a File URL (uploaded via Attach) and import tools from CSV.

	Handles both stored file paths and in-memory content. Runs synchronously.
	"""
	if not file_url:
		raise frappe.ValidationError("file_url is required")
	file_doc, blob_or_path = get_file(file_url)
	# Case 1: Frappe returned a filesystem path
	if isinstance(blob_or_path, str) and os.path.exists(blob_or_path):
		from ai_tools_dir.etl.import_tools import import_tools_from_csv
		return import_tools_from_csv(blob_or_path)
	
	# Case 2: Frappe returned file content as bytes/str
	if isinstance(blob_or_path, (bytes, bytearray)):
		data: bytes = bytes(blob_or_path)
	elif isinstance(blob_or_path, str):
		data = blob_or_path.encode("utf-8")
	else:
		raise FileNotFoundError(str(blob_or_path))

	with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
		tmp.write(data)
		tmp_path = tmp.name
	from ai_tools_dir.etl.import_tools import import_tools_from_csv
	try:
		return import_tools_from_csv(tmp_path)
	finally:
		try:
			os.unlink(tmp_path)
		except Exception:
			pass


