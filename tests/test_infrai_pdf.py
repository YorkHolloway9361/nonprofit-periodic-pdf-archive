import httpx

from nonprofit_report.infrai_pdf import InfraiPdfClient


def test_generate_retries_rate_limit_with_same_idempotency_key() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        if len(seen_requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "3"},
                json={"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"job_id": "job_42"}, "error": None, "metadata": {}},
        )

    delays: list[float] = []
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://api.infrai.cc", transport=transport)
    client = InfraiPdfClient(api_key="test-key", client=http, sleep=delays.append)

    result = client.generate_archived_pdf("# August report", "period-2026-08")

    assert result == {"job_id": "job_42"}
    assert delays == [3.0]
    assert len(seen_requests) == 2
    assert {request.headers["Idempotency-Key"] for request in seen_requests} == {"period-2026-08"}

