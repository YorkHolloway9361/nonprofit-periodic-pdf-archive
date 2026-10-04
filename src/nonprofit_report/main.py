import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .models import PeriodicReportRequest, ReportRunResult
from .report_service import ReportService

app = FastAPI(title="Nonprofit report archive")


@app.post("/reports/run", response_model=ReportRunResult)
def run_periodic_report(request: PeriodicReportRequest) -> ReportRunResult:
    archive_dir = Path(os.environ.get("REPORT_ARCHIVE_DIR", "archives"))
    service = ReportService(InfraiPdfClient(), archive_dir)
    try:
        return service.run(request)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=exc.detail) from exc

