import pytest

from app.core.config import settings
from app.ml.fusion_runtime import RiskThresholdConfig
from app.services.risk_decision_service import RiskDecisionService


def _service(auto_revoke: bool = False) -> RiskDecisionService:
    configured = settings.model_copy(
        update={"AUTO_REVOKE_CRITICAL_SESSION": auto_revoke}
    )
    return RiskDecisionService(
        RiskThresholdConfig(
            low_max=0.3,
            medium_max=0.6,
            high_max=0.8,
        ),
        configured,
    )


@pytest.mark.parametrize(
    ("risk", "level"),
    [(0.1, "low"), (0.4, "medium"), (0.7, "high"), (0.9, "critical")],
)
def test_risk_classification(risk: float, level: str) -> None:
    assert _service().classify(risk) == level


def test_single_high_measurement_does_not_restrict_session() -> None:
    decision = _service().decide(
        combined_risk=0.7,
        previous_level="low",
        recent_risks=[],
    )
    assert decision.applied_level == "medium"
    assert decision.authentication_level == "traditional"


def test_two_high_measurements_require_reverification() -> None:
    decision = _service().decide(
        combined_risk=0.7,
        previous_level="medium",
        recent_risks=[0.7],
    )
    assert decision.applied_level == "high"
    assert decision.authentication_level == "verification_required"


def test_recovery_requires_three_low_measurements() -> None:
    pending = _service().decide(
        combined_risk=0.1,
        previous_level="high",
        recent_risks=[0.1],
    )
    recovered = _service().decide(
        combined_risk=0.1,
        previous_level="high",
        recent_risks=[0.1, 0.1],
    )
    assert pending.applied_level == "high"
    assert recovered.applied_level == "low"


def test_confirmed_critical_does_not_revoke_when_disabled() -> None:
    decision = _service(auto_revoke=False).decide(
        combined_risk=0.9,
        previous_level="high",
        recent_risks=[0.9],
    )
    assert decision.authentication_level == "restricted"
    assert decision.applied_action == "mark_restricted"


def test_confirmed_critical_can_revoke_only_when_enabled() -> None:
    decision = _service(auto_revoke=True).decide(
        combined_risk=0.9,
        previous_level="high",
        recent_risks=[0.9],
    )
    assert decision.authentication_level == "terminated"
    assert decision.applied_action == "terminate_session"
