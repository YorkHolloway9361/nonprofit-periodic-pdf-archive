import json
import sys
from pathlib import Path

from nonprofit_report.infrai_pdf import InfraiPdfClient
from nonprofit_report.models import PeriodicReportRequest
from nonprofit_report.report_service import ReportService


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/run_report.py report.json")
    request = PeriodicReportRequest.model_validate_json(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = ReportService(InfraiPdfClient(), Path("archives")).run(request)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()

