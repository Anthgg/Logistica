from app.database.base import Base


def test_phase9a_tables_and_session_columns_are_registered() -> None:
    evaluations = Base.metadata.tables["continuous_auth_evaluations"]
    events = Base.metadata.tables["risk_events"]
    sessions = Base.metadata.tables["sessions"]
    assert {
        "combined_risk",
        "risk_level",
        "model_versions",
        "latency_breakdown",
    } <= set(evaluations.columns.keys())
    assert {
        "continuous_auth_evaluation_id",
        "reason_code",
    } <= set(events.columns.keys())
    assert {
        "risk_score",
        "authentication_level",
        "last_continuous_verification_at",
        "last_risk_action",
        "continuous_auth_status",
    } <= set(sessions.columns.keys())
