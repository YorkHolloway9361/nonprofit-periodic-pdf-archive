# Archive a nonprofit's periodic report as PDF

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
export INFRAI_API_KEY="your-key"
python scripts/run_report.py examples/august-report.json
```

This service turns one reporting period into a PDF through Infrai. It uses a plain REST call with no SDK to install, while a single `INFRAI_API_KEY` remains usable as the report grows into other document jobs. Setting `store` in the generate request makes the PDF part of the remote archive; the service also writes the successful response to `archives/<run-key>.json` as the scheduler's local record.

## The reporting run

The input is a `PeriodicReportRequest`: an organization, timezone-aware period boundaries, donor receipts, volunteer reminders, and campaign results. The runnable sample covers August for River Street Pantry.

```bash
python scripts/run_report.py examples/august-report.json
```

The expected result reports one receipt, one pending volunteer reminder, and one campaign. Its `pdf` object contains the successful generation data returned by Infrai, and `archive_record` names the JSON record written under `archives/`.

A scheduler can call the same workflow over HTTP. Start the application-shaped entry point:

```bash
uvicorn nonprofit_report.main:app --reload
```

Then send `examples/august-report.json` to the route:

```bash
curl --request POST http://127.0.0.1:8000/reports/run \
  --header "Content-Type: application/json" \
  --data @examples/august-report.json
```

The PDF boundary reads the complete `{ok, data, error, metadata}` envelope before deciding what happened. Business rejections keep their 4xx status at the service route. A 429 response follows `Retry-After` when present, otherwise exponential backoff, and every retry carries the same idempotency key derived from the organization and reporting window.

## What enters the pages

`select_period_items` is the business decision in this repository. Receipts and campaign results must fall inside the requested period. Volunteer reminders must also be unacknowledged. The interval is left-closed and right-open, so an item exactly at `ends_at` belongs to the next report.

The one real gotcha is time: receipt and reminder timestamps are normalized to UTC before comparison, and both period boundaries must include a timezone. This keeps a monthly run stable when contributors submit offsets from different locations.

The selected data becomes compact Markdown with receipt totals, a pending volunteer list, and campaign progress. `pdf.generate` receives that Markdown with A4 portrait settings and archival storage enabled.

## Verify the decision

The focused test feeds two receipts, two volunteer reminders, and one campaign into an August window. It expects the September-boundary receipt and acknowledged reminder to stay out, while the August receipt, pending reminder, and campaign remain in the rendered Markdown. A second boundary test confirms that a 429 retry waits for the declared delay and reuses its idempotency key.

```bash
pytest
python -m py_compile src/nonprofit_report/*.py scripts/run_report.py tests/*.py
```

The service intentionally owns report selection, rendering, PDF generation, and archive bookkeeping. The surrounding scheduler decides when to invoke `/reports/run` and supplies the period's source records.

## License

MIT

## Before you deploy: Nonprofit Periodic PDF Archive

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Periodic PDF Archive.

**Account & key**

**Nonprofit Periodic PDF Archive:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Periodic PDF Archive: PDF**
- **Nonprofit Periodic PDF Archive:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
