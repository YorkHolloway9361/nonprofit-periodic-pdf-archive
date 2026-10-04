from dataclasses import dataclass
from datetime import timezone
from decimal import Decimal

from .models import CampaignResult, DonorReceipt, PeriodicReportRequest, VolunteerReminder


@dataclass(frozen=True)
class ReportSelection:
    receipts: list[DonorReceipt]
    reminders: list[VolunteerReminder]
    campaigns: list[CampaignResult]


def select_period_items(request: PeriodicReportRequest) -> ReportSelection:
    starts_at = request.period.starts_at.astimezone(timezone.utc)
    ends_at = request.period.ends_at.astimezone(timezone.utc)

    receipts = [
        item
        for item in request.receipts
        if starts_at <= item.issued_at.astimezone(timezone.utc) < ends_at
    ]
    reminders = [
        item
        for item in request.volunteer_reminders
        if not item.acknowledged
        and starts_at <= item.scheduled_for.astimezone(timezone.utc) < ends_at
    ]
    start_date = starts_at.date()
    end_date = ends_at.date()
    campaigns = [
        item
        for item in request.campaign_results
        if start_date <= item.report_date < end_date
    ]
    return ReportSelection(receipts=receipts, reminders=reminders, campaigns=campaigns)


def money(value: Decimal) -> str:
    return f"${value:,.2f}"


def build_report_markdown(request: PeriodicReportRequest, selection: ReportSelection) -> str:
    total_receipted = sum((item.amount for item in selection.receipts), Decimal("0"))
    lines = [
        f"# {request.organization_name}: periodic report",
        "",
        f"Reporting window: {request.period.starts_at.isoformat()} to {request.period.ends_at.isoformat()}",
        "",
        "## Donor receipts",
        "",
        f"{len(selection.receipts)} receipts issued, totaling {money(total_receipted)}.",
        "",
    ]
    lines.extend(
        f"- {item.receipt_number} | {item.donor_name} | {money(item.amount)}"
        for item in selection.receipts
    )
    lines.extend(["", "## Volunteer reminders", ""])
    lines.extend(
        f"- {item.scheduled_for.isoformat()} | {item.volunteer_name} | {item.activity}"
        for item in selection.reminders
    )
    lines.extend(["", "## Campaign reporting", ""])
    lines.extend(
        f"- {item.campaign_name} | {money(item.raised)} of {money(item.goal)}"
        for item in selection.campaigns
    )
    if not selection.receipts:
        lines.insert(7, "No receipts were issued in this period.")
    if not selection.reminders:
        lines.append("No unacknowledged volunteer reminders fall in this period.")
    if not selection.campaigns:
        lines.append("No campaign results were reported in this period.")
    return "\n".join(lines) + "\n"

