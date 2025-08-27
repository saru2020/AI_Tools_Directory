frappe.listview_settings["Tool"] = {
	onload(listview) {
		// Quick filter for Pending Review
		listview.filter_area.add(["Tool", "ingestion_status", "=", "Pending Review"]);

		listview.page.add_menu_item("Test Background Job", async () => {
			try {
				const r = await frappe.call({ method: 'ai_tools_dir.api.scrape.test_bg_job' });
				frappe.msgprint({ 
					title: 'Test Job Started', 
					message: `Job ID: ${r.message.log_id}`, 
					indicator: 'blue' 
				});
			} catch (e) {
				frappe.msgprint({ 
					title: 'Test Failed', 
					message: e.message || e, 
					indicator: 'red' 
				});
			}
		});

		listview.page.add_menu_item("Import Tools CSV", async () => {
			const d = new frappe.ui.Dialog({
				title: "Import Tools from CSV",
				fields: [
					{ fieldtype: "Attach", fieldname: "file", label: "CSV File", reqd: 1 },
				],
				primary_action_label: "Import",
				primary_action: async (values) => {
					try {
						await frappe.call({
							method: "ai_tools_dir.api.import_tools.import_from_uploaded",
							args: { file_url: values.file },
						});
						frappe.show_alert({ message: "Import started", indicator: "green" });
						listview.refresh();
						d.hide();
					} catch (e) {
						frappe.msgprint({ title: "Import failed", message: e.message || e, indicator: "red" });
					}
				},
			});
			d.show();
		});

		listview.page.add_menu_item("Run Scraper (Background)", async () => {
			const d = new frappe.ui.Dialog({
				title: "Run Scraper (Background)",
				fields: [
					{ fieldtype: "Int", fieldname: "per_source", label: "Tools per source", default: 50, reqd: 1 },
					{ fieldtype: "Float", fieldname: "rate_limit", label: "Rate limit (reqs/sec)", default: 1.0 },
					{ fieldtype: "Int", fieldname: "timeout", label: "Request timeout (sec)", default: 20 },
					{ fieldtype: "HTML", fieldname: "log", label: "Log" },
				],
				primary_action_label: "Start",
				primary_action: async (values) => {
					d.get_primary_btn().prop('disabled', true).text('Starting...');
					let log_id = null;
					let offset = 0;
					let timer = null;
					const log_field = d.get_field('log');
					log_field.$wrapper.css({ maxHeight: '300px', overflow: 'auto', background: '#111', color: '#ddd', padding: '8px', fontFamily: 'monospace' });
					log_field.$wrapper.html('<div id="scrape-log"></div>');
					const $log = log_field.$wrapper.find('#scrape-log');
					const append = (txt) => {
						$log.append(`<div>${frappe.utils.escape_html(txt)}</div>`);
						log_field.$wrapper.scrollTop(log_field.$wrapper[0].scrollHeight);
					};
					try {
						const started = await frappe.call({ method: 'ai_tools_dir.api.scrape.start', args: values });
						log_id = started.message.log_id;
						append(`Started job: ${log_id}`);
						
						const poll = async () => {
							try {
								const r = await frappe.call({ method: 'ai_tools_dir.api.scrape.log', args: { log_id, since: offset } });
								offset = r.message.offset || offset;
								const chunk = r.message.chunk || '';
								if (chunk) {
									for (const line of chunk.split('\n')) {
										if (line) append(line);
									}
								}
								const status = (r.message.status || {}).status || 'unknown';
								if (status === 'completed' || status === 'failed') {
									append(`Status: ${status}`);
									clearInterval(timer);
									d.get_primary_btn().prop('disabled', false).text('Start');
									listview.refresh();
									return;
								}
							} catch (e) {
								append(`Error polling: ${e.message || e}`);
							}
						};
						timer = setInterval(poll, 1500);
						await poll();
					} catch (e) {
						frappe.msgprint({ title: 'Failed to start', message: e.message || e, indicator: 'red' });
						d.get_primary_btn().prop('disabled', false).text('Start');
					}
				},
			});
			d.show();
		});

		listview.page.add_actions_menu_item("Approve Selected", async () => {
			const names = listview.get_checked_items().map((d) => d.name);
			if (!names.length) return;
			await frappe.call({ method: "ai_tools_dir.api.ingestion.bulk_approve", args: { names } });
			listview.refresh();
		});

		listview.page.add_actions_menu_item("Reject Selected", async () => {
			const names = listview.get_checked_items().map((d) => d.name);
			if (!names.length) return;
			await frappe.call({ method: "ai_tools_dir.api.ingestion.bulk_reject", args: { names } });
			listview.refresh();
		});
	},
};


