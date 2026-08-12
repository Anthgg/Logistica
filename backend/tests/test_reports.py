from app.database.base import utc_now
from tests.support import authenticate, create_client, create_shipment


def test_reports_group_and_filter_shipments(client, database) -> None:
    _, headers = authenticate(client, database)
    report_params = {
        "date_from": utc_now().date().isoformat(),
        "date_to": utc_now().date().isoformat(),
    }
    before_status = {
        row["key"]: row["count"]
        for row in client.get(
            "/api/reports/shipments-by-status", params=report_params
        ).json()
    }
    before_priority = {
        row["key"]: row["count"]
        for row in client.get(
            "/api/reports/shipments-by-priority", params=report_params
        ).json()
    }
    customer = create_client(client, headers)
    create_shipment(client, headers, customer["id"])
    grouped = client.get(
        "/api/reports/shipments-by-status",
        params=report_params,
    )
    assert grouped.status_code == 200
    after_status = {row["key"]: row["count"] for row in grouped.json()}
    assert after_status["registered"] == before_status.get("registered", 0) + 1
    priorities = client.get(
        "/api/reports/shipments-by-priority", params=report_params
    )
    assert priorities.status_code == 200
    after_priority = {row["key"]: row["count"] for row in priorities.json()}
    assert after_priority["normal"] == before_priority.get("normal", 0) + 1
