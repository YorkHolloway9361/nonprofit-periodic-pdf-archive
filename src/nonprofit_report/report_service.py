import hashlib
import json
from pathlib import Path

from .infrai_pdf import InfraiPdfClient
from .models import PeriodicReportRequest, ReportRunResult
from .report_builder import build_report_markdown, select_period_items


class ReportService:
    def __init__(self, pdf_client: InfraiPdfClient, archive_dir: Path) -> None:
        self.pdf_client = pdf_client
        self.archive_dir = archive_dir

    def run(self, request: PeriodicReportRequest) -> ReportRunResult:
        selection = select_period_items(request)
        markdown = build_report_markdown(request, selection)
        identity = "|".join(
            (
                request.organization_name,
                request.period.starts_at.isoformat(),
                request.period.ends_at.isoformat(),
            )
        )
        run_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        pdf_data = self.pdf_client.generate_archived_pdf(markdown, run_key)

        self.archive_dir.mkdir(parents=True, exist_ok=True)
        record_path = self.archive_dir / f"{run_key}.json"
        record = {
            "organization_name": request.organization_name,
            "period": request.period.model_dump(mode="json"),
            "pdf": pdf_data,
        }
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return ReportRunResult(
            archive_record=str(record_path),
            receipt_count=len(selection.receipts),
            reminder_count=len(selection.reminders),
            campaign_count=len(selection.campaigns),
            pdf=pdf_data,
        )

