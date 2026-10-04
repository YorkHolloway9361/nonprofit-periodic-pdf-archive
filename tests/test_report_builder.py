from datetime import UTC, datetime

from nonprofit_report.models import PeriodicReportRequest
from nonprofit_report.report_builder import build_report_markdown, select_period_items


def test_report_keeps_period_activity_and_only_pending_reminders() -> None:
    request = PeriodicReportRequest.model_validate(
        {
            "organization_name": "River Street Pantry",
            "period": {
                "starts_at": "2026-08-01T00:00:00Z",
                "ends_at": "2026-09-01T00:00:00Z",
            },
            "receipts": [
                {
                    "receipt_number": "R-108",
                    "donor_name": "Avery Chen",
                    "amount": "125.00",
                    "issued_at": "2026-08-12T14:00:00Z",
                },
                {
                    "receipt_number": "R-109",
                    "donor_name": "Morgan Lee",
                    "amount": "40.00",
                    "issued_at": "2026-09-01T00:00:00Z",
                },
            ],
            "volunteer_reminders": [
                {
                    "volunteer_name": "Sam Ortiz",
                    "activity": "Pantry packing",
                    "scheduled_for": "2026-08-20T09:00:00Z",
                    "acknowledged": False,
                },
                {
                    "volunteer_name": "Riley Kim",
                    "activity": "Delivery route",
                    "scheduled_for": "2026-08-22T09:00:00Z",
                    "acknowledged": True,
                },
            ],
            "campaign_results": [
                {
                    "campaign_name": "Backpack drive",
                    "raised": "2800.00",
                    "goal": "3500.00",
                    "report_date": "2026-08-31",
                }
            ],
        }
    )

    selection = select_period_items(request)
    markdown = build_report_markdown(request, selection)

    assert [item.receipt_number for item in selection.receipts] == ["R-108"]
    assert [item.volunteer_name for item in selection.reminders] == ["Sam Ortiz"]
    assert [item.campaign_name for item in selection.campaigns] == ["Backpack drive"]
    assert "$125.00" in markdown
    assert "Morgan Lee" not in markdown
    assert "Riley Kim" not in markdown
    assert request.period.ends_at == datetime(2026, 9, 1, tzinfo=UTC)

