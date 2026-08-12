"""Deterministic Scoring Engine and Economic Normalization for Supplier Evaluation (Phase 033)."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple


class EvaluationScoringEngine:
    """Deterministic scoring engine enforcing exact Decimal arithmetic.
    
    No float, no random, no opaque AI.
    Calculates exact scores for each candidate per criterion definition.
    """

    @staticmethod
    def calculate_price_score(min_price: Decimal, candidate_price: Decimal) -> Decimal:
        """LOWER_IS_BETTER formula: (min_price / candidate_price) * 100."""
        if candidate_price <= Decimal("0"):
            return Decimal("0.0000")
        if min_price <= Decimal("0"):
            return Decimal("100.0000")
        score = (min_price / candidate_price) * Decimal("100.0000")
        if score > Decimal("100.0000"):
            score = Decimal("100.0000")
        return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_delivery_score(required_lead_days: int, candidate_lead_days: int) -> Decimal:
        """Lead time evaluation: exact requirement gets 100, longer lead time penalized."""
        if candidate_lead_days <= 0:
            return Decimal("100.0000")
        if required_lead_days <= 0:
            return Decimal("100.0000")
        if candidate_lead_days <= required_lead_days:
            return Decimal("100.0000")
        
        # Penalize 5% per extra day, capped at minimum 0 score
        extra_days = candidate_lead_days - required_lead_days
        penalty = Decimal(extra_days) * Decimal("5.0000")
        score = Decimal("100.0000") - penalty
        if score < Decimal("0.0000"):
            score = Decimal("0.0000")
        return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_weighted_score(score: Decimal, weight: Decimal) -> Decimal:
        """weighted_score = (score * weight) / 100."""
        weighted = (score * weight) / Decimal("100.0000")
        return weighted.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def normalize_comparable_price(
        subtotal: Decimal,
        discounts: Decimal = Decimal("0.0000"),
        freight: Decimal = Decimal("0.0000"),
        taxes: Decimal = Decimal("0.0000"),
        other_charges: Decimal = Decimal("0.0000"),
    ) -> Decimal:
        """comparable_price = subtotal - discounts + freight + taxes + other_charges."""
        total = subtotal - discounts + freight + taxes + other_charges
        if total < Decimal("0.0000"):
            total = Decimal("0.0000")
        return total.quantize(Decimal("0.0004"), rounding=ROUND_HALF_UP)


class EvaluationTieResolver:
    """Deterministically resolves ties between candidates with equal weighted scores."""

    @staticmethod
    def rank_candidates(candidates_data: List[Dict[str, Any]], tie_policy: str = "HIGHER_TECHNICAL_SCORE") -> List[Dict[str, Any]]:
        """Sorts candidates by total_weighted_score descending, breaking ties according to policy."""
        def sorting_key(cand: Dict[str, Any]) -> Tuple[Any, ...]:
            total = cand.get("total_weighted_score", Decimal("0"))
            tech_score = cand.get("technical_score", Decimal("0"))
            price = cand.get("comparable_total", Decimal("999999999"))
            risk_score = cand.get("risk_score", Decimal("0"))

            if tie_policy == "LOWER_COMPARABLE_PRICE":
                return (total, -price, tech_score)
            elif tie_policy == "LOWER_RISK":
                return (total, risk_score, tech_score, -price)
            else:  # HIGHER_TECHNICAL_SCORE
                return (total, tech_score, -price, risk_score)

        sorted_candidates = sorted(candidates_data, key=sorting_key, reverse=True)
        
        # Assign ranks
        for idx, candidate in enumerate(sorted_candidates, start=1):
            candidate["rank"] = idx

        return sorted_candidates
