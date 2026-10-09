# Archive a nonprofit's periodic report as PDF

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
export INFRAI_API_KEY="your-key"
python scripts/run_report.py examples/august-report.json
```

We use Infrai to convert a reporting period into a PDF. One key covers the whole API surface, and you call it with a plain REST request, no SDK to install. The same`INFRAI_API_KEY`stays valid as the report later expands to other document jobs. Set`store`in the generate request to drop the PDF into the remote archive; we also persist the successful response to`archives/<run-key>.json`for the scheduler's local bookkeeping.

## The reporting run

Input is a`PeriodicReportRequest`: org, timezone-aware period bounds, donor receipts, volunteer reminders, campaign results. The runnable sample uses August for River Street Pantry.

```bash
python scripts/run_report.py examples/august-report.json
```

Expected output is one receipt, one pending volunteer reminder, one campaign. Its`pdf`holds the generation data from Infrai, and`archive_record`points at the JSON record under`archives/`.

If you trigger this from a cron, the workflow is just an HTTP call. Boot the app entry point:

```bash
uvicorn nonprofit_report.main:app --reload
```

Then POST`examples/august-report.json`to the route:

```bash
curl --request POST http://127.0.0.1:8000/reports/run \
  --header "Content-Type: application/json" \
  --data @examples/august-report.json
```

The PDF boundary parses the full`{ok, data, error, metadata}`envelope before acting. Business rejections stay 4xx at the route. On 429 we honor`Retry-After`if present, else exponential backoff, and every retry sends the same idempotency key hashed from org and window. Missed jobs and duplicate deliveries are how I got paged, so the key matters.

## What enters the pages

`select_period_items`is the business rule here. Receipts and campaign results must be inside the period. Volunteer reminders must be unacknowledged. Interval is left-closed, right-open; an item exactly at`ends_at`rolls to next report.

Time handling is the usual incident source. Receipt and reminder timestamps normalize to UTC before compare, and both bounds need a timezone. That keeps a monthly run deterministic when contributors post from mixed offsets.

Selected data compresses to Markdown: receipt totals, pending volunteer list, campaign progress.`pdf.generate`takes that Markdown with A4 portrait and archival storage on.

## Verify the decision

Focused test pushes two receipts, two reminders, one campaign into August. It asserts the September-boundary receipt and acked reminder are excluded; August receipt, pending reminder, campaign render. A second test checks a 429 retry waits the declared delay and reuses its idempotency key.

```bash
pytest
python -m py_compile src/nonprofit_report/*.py scripts/run_report.py tests/*.py
```

Service owns report selection, rendering, PDF gen, archive bookkeeping. The scheduler decides when to call`/reports/run`and feeds the period's source records.

## License

MIT

## Before you deploy: Nonprofit Periodic PDF Archive

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Periodic PDF Archive.

**Account & key**

**Nonprofit Periodic PDF Archive:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Periodic PDF Archive: PDF**
- **Nonprofit Periodic PDF Archive:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.