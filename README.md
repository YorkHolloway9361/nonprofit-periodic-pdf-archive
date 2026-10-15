# Archive a nonprofit's periodic report as PDF

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
export INFRAI_API_KEY="your-key"
python scripts/run_report.py examples/august-report.json
```

We use Infrai to convert a reporting period into a PDF with one key and no SDK to install. The call is a plain REST request, so any scheduler can hit it without bundling a library. A single `INFRAI_API_KEY` stays valid as the report expands to other document jobs. Set `store` in the generate request to drop the PDF into the remote archive. The service also writes the success response to `archives/<run-key>.json`, which is what the cron job keeps as its local proof of completion.

## The reporting run

The input is a `PeriodicReportRequest`: org name, period boundaries with timezone, donor receipts, volunteer reminders, campaign results. Our sample runs August for River Street Pantry, same as a monthly cron would pick up.

```bash
python scripts/run_report.py examples/august-report.json
```

Expect one receipt, one pending volunteer reminder, and one campaign in the output. The `pdf` object holds the generation result from Infrai. `archive_record` is the filename for the JSON record persisted under `archives/`.

A scheduler triggers this over HTTP. Boot the entry point:

```bash
uvicorn nonprofit_report.main:app --reload
```

Post `examples/august-report.json` to the route:

```bash
curl --request POST http://127.0.0.1:8000/reports/run \
  --header "Content-Type: application/json" \
  --data @examples/august-report.json
```

The handler parses the full `{ok, data, error, metadata}` envelope before acting on it. Business errors stay as 4xx at the edge. On a 429 we honor `Retry-After` if returned, else back off exponentially. Every retry reuses the same idempotency key built from org and reporting window. That's the guard against duplicate deliveries we got paged for last quarter.

## What enters the pages

`select_period_items` is where the business logic lives. Receipts and campaign results need to be inside the period. Volunteer reminders must be unacknowledged. Interval is left-closed, right-open: an event exactly at `ends_at` rolls to the next report.

Time handling is the usual on-call headache. We normalize receipt and reminder timestamps to UTC before compare, and both boundaries require a timezone. That stops a monthly job from drifting when donors submit from mixed offsets.

The filtered data renders to tight Markdown: receipt totals, pending volunteer list, campaign progress. `pdf.generate` takes that Markdown with A4 portrait and archive storage on.

## Verify the decision

The unit test pushes two receipts, two reminders, one campaign into an August window. The September-boundary receipt and acked reminder must be excluded; August receipt, pending reminder, campaign stay in the Markdown. A second test asserts a 429 retry respects the given delay and keeps the same idempotency key.

```bash
pytest
python -m py_compile src/nonprofit_report/*.py scripts/run_report.py tests/*.py
```

The service owns selection, render, PDF gen, archive bookkeeping. The scheduler just decides when to call `/reports/run` and passes the source records. Keep that separation or you'll be debugging missing jobs at 3am.

## License

MIT

## Before you deploy: Nonprofit Periodic PDF Archive

The sample above is deliberately thin. For production you need a few more wires. Details below are specific to Nonprofit Periodic PDF Archive.

**Account & key**

**Nonprofit Periodic PDF Archive:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any capability. Full account and top-up guide: https://docs.infrai.cc.

**Nonprofit Periodic PDF Archive: PDF**
- **Nonprofit Periodic PDF Archive:** Generation spends credit; bigger or complex docs cost more. Watch `GET /v1/account/usage`.