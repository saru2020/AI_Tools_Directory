import os
import subprocess
import sys
import uuid
import time
import frappe


def _test_job(log_id: str):
	"""Test job function that can be pickled."""
	time.sleep(5)  # Simulate 5 seconds of work
	_set_status(log_id, "completed", {"message": "Test job completed successfully"})


@frappe.whitelist()
def test_bg_job() -> dict:
	"""Test if background jobs are working."""
	log_id = f"test_{uuid.uuid4().hex}"
	_set_status(log_id, "queued")
	
	frappe.enqueue(_test_job, log_id=log_id, job_id=f"test-{log_id}", timeout=30)
	return {"log_id": log_id, "message": "Test job queued"}


def _coerce_int(val):
	if val in (None, "", "null"):
		return None
	try:
		return int(val)
	except Exception:
		return None


def _coerce_float(val):
	if val in (None, "", "null"):
		return None
	try:
		return float(val)
	except Exception:
		return None


def _resolve_paths():
	package_path = frappe.get_app_path("ai_tools_dir")
	app_root = os.path.dirname(package_path)
	script_path = os.path.join(app_root, "scripts", "scraper", "scrape.py")
	config_path = os.path.join(app_root, "scripts", "scraper", "config.yaml")
	if not os.path.exists(config_path):
		config_path = os.path.join(app_root, "scripts", "scraper", "config.example.yaml")
	output_csv = os.path.join(app_root, "ai_tools_seed.csv")
	return app_root, script_path, config_path, output_csv


def _write_line(path: str, text: str) -> None:
	with open(path, "a", encoding="utf-8") as f:
		f.write(text + ("" if text.endswith("\n") else "\n"))


def _status_key(log_id: str) -> str:
	return f"scrape:{log_id}:status"


def _log_path_for(log_id: str) -> str:
	return frappe.get_site_path("logs", f"{log_id}.log")


def _set_status(log_id: str, status: str, meta: dict | None = None) -> None:
	data = {"status": status, **(meta or {})}
	frappe.cache().set_value(_status_key(log_id), frappe.as_json(data))


def _get_status(log_id: str) -> dict:
	raw = frappe.cache().get_value(_status_key(log_id))
	return frappe.parse_json(raw) if raw else {"status": "unknown"}


def _bg_run(log_id: str, per_source=None, rate_limit=None, scraper_timeout=None) -> None:
	app_root, script_path, config_path, output_csv = _resolve_paths()
	log_file = _log_path_for(log_id)
	os.makedirs(os.path.dirname(log_file), exist_ok=True)
	_set_status(log_id, "running", {"output_csv": output_csv})
	_write_line(log_file, f"[info] Starting scraper: {script_path}")
	_write_line(log_file, f"[info] Config: {config_path}")
	_write_line(log_file, f"[info] Parameters: per_source={per_source}, rate_limit={rate_limit}, scraper_timeout={scraper_timeout}")
	try:
		per_source_i = _coerce_int(per_source)
		rate_limit_f = _coerce_float(rate_limit)
		timeout_i = _coerce_int(scraper_timeout)
		args = [sys.executable, script_path, config_path]
		if per_source_i is not None:
			args += ["--per-source", str(per_source_i)]
			_write_line(log_file, f"[info] Overriding source limits to {per_source_i} per source")
		if rate_limit_f is not None:
			args += ["--rate-limit", str(rate_limit_f)]
			_write_line(log_file, f"[info] Overriding rate limit to {rate_limit_f} reqs/sec")
		if timeout_i is not None:
			args += ["--timeout", str(timeout_i)]
			_write_line(log_file, f"[info] Overriding timeout to {timeout_i} seconds")
		_write_line(log_file, f"[info] CWD: {app_root}")
		_write_line(log_file, f"[info] CMD: {' '.join(args)}")
		_write_line(log_file, f"[info] Starting subprocess...")
		proc = subprocess.Popen(args, cwd=app_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
		assert proc.stdout is not None
		_write_line(log_file, f"[info] Subprocess started (PID: {proc.pid})")
		for line in proc.stdout:
			_write_line(log_file, line.rstrip("\n"))
		ret = proc.wait()
		_write_line(log_file, f"[info] Subprocess completed with return code: {ret}")
		if ret != 0:
			_write_line(log_file, f"[error] Scraper exited with code {ret}")
			_set_status(log_id, "failed", {"returncode": ret})
			return
		# Import results
		from ai_tools_dir.etl.import_tools import import_tools_from_csv
		if not os.path.exists(output_csv):
			_write_line(log_file, f"[error] Output CSV not found: {output_csv}")
			_set_status(log_id, "failed", {"error": "no_output"})
			return
		file_size = os.path.getsize(output_csv)
		_write_line(log_file, f"[info] Output CSV created: {output_csv} ({file_size} bytes)")
		_write_line(log_file, f"[info] Starting import...")
		stats = import_tools_from_csv(output_csv)
		_write_line(log_file, f"[info] Import completed: {frappe.as_json(stats)}")
		_set_status(log_id, "completed", {"stats": stats, "output_csv": output_csv, "file_size": file_size})
	except Exception as e:
		_write_line(log_file, f"[exception] {e}")
		_set_status(log_id, "failed", {"error": str(e)})


@frappe.whitelist()
def start(per_source=None, rate_limit=None, timeout=None) -> dict:
	"""Start scraper in background and return a log_id for streaming logs."""
	log_id = f"scrape_{uuid.uuid4().hex}"
	_set_status(log_id, "queued")
	
	# Try to use long queue first, fallback to default with timeout
	try:
		frappe.enqueue(
			"ai_tools_dir.api.scrape._bg_run",
			queue="long",
			job_id=f"scrape-{log_id}",
			timeout=3600,  # 1 hour timeout for scraping jobs
			log_id=log_id,
			per_source=per_source,
			rate_limit=rate_limit,
			scraper_timeout=timeout,  # Renamed to avoid conflict
		)
	except Exception as e:
		# Fallback to default queue with longer timeout
		frappe.logger().warning(f"Long queue failed, using default: {e}")
		frappe.enqueue(
			"ai_tools_dir.api.scrape._bg_run",
			job_id=f"scrape-{log_id}",
			timeout=3600,  # 1 hour timeout for scraping jobs
			log_id=log_id,
			per_source=per_source,
			rate_limit=rate_limit,
			scraper_timeout=timeout,  # Renamed to avoid conflict
		)
	
	return {"log_id": log_id}


@frappe.whitelist()
def log(log_id: str, since: int | None = None) -> dict:
	"""Fetch log content and status.
	- since: byte offset to read from; returns new offset and chunk
	"""
	path = _log_path_for(log_id)
	status = _get_status(log_id)
	if not os.path.exists(path):
		return {"status": status, "offset": 0, "chunk": ""}
	start = int(since or 0)
	with open(path, "r", encoding="utf-8", errors="ignore") as f:
		f.seek(start)
		chunk = f.read()
		offset = f.tell()
	return {"status": status, "offset": offset, "chunk": chunk}


@frappe.whitelist()
def run(per_source=None, rate_limit=None, timeout=None) -> dict:
	"""Synchronous run (fallback)."""
	app_root, script_path, config_path, output_csv = _resolve_paths()
	per_source_i = _coerce_int(per_source)
	rate_limit_f = _coerce_float(rate_limit)
	timeout_i = _coerce_int(timeout)
	args = [sys.executable, script_path, config_path]
	if per_source_i is not None:
		args += ["--per-source", str(per_source_i)]
	if rate_limit_f is not None:
		args += ["--rate-limit", str(rate_limit_f)]
	if timeout_i is not None:
		args += ["--timeout", str(timeout_i)]
	try:
		proc = subprocess.run(args, cwd=app_root, capture_output=True, text=True, timeout=300)
	except subprocess.TimeoutExpired:
		raise frappe.ValidationError("Scraper timed out after 5 minutes")
	except Exception as e:
		raise frappe.ValidationError(f"Failed to start scraper: {e}")
	stdout = proc.stdout or ""
	stderr = proc.stderr or ""
	if proc.returncode != 0:
		raise frappe.ValidationError(f"Scraper failed (code {proc.returncode}): {stderr or stdout}")
	from ai_tools_dir.etl.import_tools import import_tools_from_csv
	stats = import_tools_from_csv(output_csv)
	return {"scraper_stdout": stdout[-4000:], "scraper_stderr": stderr[-4000:], "import_stats": stats, "output_file": output_csv, "file_size": os.path.getsize(output_csv) if os.path.exists(output_csv) else 0}


