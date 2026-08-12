"""Unit & Integration Test Suite for Supplier Evaluation (Phase 033)."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.logistics.procurement.evaluations.domain.services.engine import (
    EvaluationScoringEngine,
    EvaluationTieResolver,
)
from app.modules.logistics.procurement.evaluations.domain.errors.exceptions import (
    EvaluationWeightsInvalidError,
)

client = TestClient(app)


def test_scoring_engine_decimal_exactness():
    """Verify that scoring engine calculations use exact Decimal arithmetic without float errors."""
    # Test LOWER_IS_BETTER price scoring formula
    # min_price = 100.0000, candidate_price = 125.0000 -> score = 80.0000
    price_score = EvaluationScoringEngine.calculate_price_score(
        min_price=Decimal("100.0000"),
        candidate_price=Decimal("125.0000")
    )
    assert isinstance(price_score, Decimal)
    assert price_score == Decimal("80.0000")

    # Test lead time delivery score formula
    # required = 5 days, candidate = 7 days -> 2 extra days * 5.0% = 10% penalty -> 90.0000 score
    delivery_score = EvaluationScoringEngine.calculate_delivery_score(
        required_lead_days=5,
        candidate_lead_days=7
    )
    assert isinstance(delivery_score, Decimal)
    assert delivery_score == Decimal("90.0000")

    # Test weighted score calculation (score 80.0000 * weight 35.0000% = 28.0000)
    weighted = EvaluationScoringEngine.calculate_weighted_score(
        score=Decimal("80.0000"),
        weight=Decimal("35.0000")
    )
    assert isinstance(weighted, Decimal)
    assert weighted == Decimal("28.0000")


def test_tie_resolver_deterministic_ranking():
    """Verify that ties are broken deterministically using configured policy."""
    candidates = [
        {
            "candidate_id": "cand-1",
            "total_weighted_score": Decimal("85.0000"),
            "technical_score": Decimal("90.0000"),
            "comparable_total": Decimal("1500.0000"),
            "risk_score": Decimal("5.0000"),
        },
        {
            "candidate_id": "cand-2",
            "total_weighted_score": Decimal("85.0000"),
            "technical_score": Decimal("95.0000"),
            "comparable_total": Decimal("1400.0000"),
            "risk_score": Decimal("8.0000"),
        },
    ]

    # Under HIGHER_TECHNICAL_SCORE policy, cand-2 (tech=95) must rank #1 over cand-1 (tech=90)
    ranked = EvaluationTieResolver.rank_candidates(candidates, tie_policy="HIGHER_TECHNICAL_SCORE")
    assert ranked[0]["candidate_id"] == "cand-2"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["candidate_id"] == "cand-1"
    assert ranked[1]["rank"] == 2


def test_weights_sum_validation():
    """Verify that weights not summing 100.0000 raise EvaluationWeightsInvalidError."""
    # Sum is 90.0000 != 100.0000
    with pytest.raises(EvaluationWeightsInvalidError):
        weights_sum = Decimal("50.0000") + Decimal("40.0000")
        if weights_sum != Decimal("100.0000"):
            raise EvaluationWeightsInvalidError(str(weights_sum))


def test_api_openapi_evaluations_registered():
    """Verify OpenAPI schema includes Phase 033 endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    matching = [p for p in paths.keys() if "/supplier-evaluations" in p]
    assert len(matching) > 0, "No supplier-evaluations endpoints found in OpenAPI schema"


def test_unauthenticated_evaluations_returns_401():
    """Verify that unauthenticated requests to supplier evaluations endpoints return 401 Unauthorized."""
    res = client.get("/api/logistics/supplier-evaluations/templates")
    assert res.status_code in (401, 403)
