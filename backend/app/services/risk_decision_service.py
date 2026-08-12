from dataclasses import dataclass

from app.core.config import Settings, settings
from app.ml.fusion_runtime import RiskThresholdConfig

RISK_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


@dataclass(frozen=True, slots=True)
class RiskDecision:
    raw_level: str
    applied_level: str
    authentication_level: str
    recommended_action: str
    applied_action: str
    continuous_auth_status: str
    reason_code: str


class RiskDecisionService:
    def __init__(
        self,
        thresholds: RiskThresholdConfig,
        source_settings: Settings = settings,
    ) -> None:
        self.thresholds = thresholds
        self.settings = source_settings

    def classify(self, risk: float) -> str:
        if risk <= self.thresholds.low_max:
            return "low"
        if risk <= self.thresholds.medium_max:
            return "medium"
        if risk <= self.thresholds.high_max:
            return "high"
        return "critical"

    def decide(
        self,
        *,
        combined_risk: float,
        previous_level: str | None,
        recent_risks: list[float],
    ) -> RiskDecision:
        raw_level = self.classify(combined_risk)
        recent_raw_levels = [
            raw_level,
            *(self.classify(value) for value in recent_risks),
        ]
        applied = raw_level
        reason = f"RISK_{raw_level.upper()}"
        if raw_level == "critical":
            confirmations = self._consecutive(
                recent_raw_levels, {"critical"}
            )
            if (
                confirmations
                < self.settings.RISK_CRITICAL_CONFIRMATION_COUNT
            ):
                applied = self._pending_level(previous_level)
                reason = "CRITICAL_PENDING_CONFIRMATION"
        elif raw_level == "high":
            confirmations = self._consecutive(
                recent_raw_levels, {"high", "critical"}
            )
            if confirmations < self.settings.RISK_HIGH_CONFIRMATION_COUNT:
                applied = self._pending_level(previous_level)
                reason = "HIGH_PENDING_CONFIRMATION"
        elif (
            previous_level
            and RISK_ORDER[previous_level] > RISK_ORDER[raw_level]
        ):
            acceptable = {"low"} if raw_level == "low" else {"low", "medium"}
            recoveries = self._consecutive(recent_raw_levels, acceptable)
            if (
                recoveries
                < self.settings.RISK_RECOVERY_CONFIRMATION_COUNT
            ):
                applied = previous_level
                reason = "RISK_RECOVERY_PENDING"
        return self._action(
            raw_level=raw_level,
            applied_level=applied,
            reason_code=reason,
        )

    @staticmethod
    def _consecutive(levels: list[str], accepted: set[str]) -> int:
        count = 0
        for level in levels:
            if level not in accepted:
                break
            count += 1
        return count

    @staticmethod
    def _pending_level(previous_level: str | None) -> str:
        if previous_level in {"high", "critical"}:
            return previous_level
        return "medium"

    def _action(
        self,
        *,
        raw_level: str,
        applied_level: str,
        reason_code: str,
    ) -> RiskDecision:
        if applied_level == "low":
            return RiskDecision(
                raw_level=raw_level,
                applied_level=applied_level,
                authentication_level="continuously_verified",
                recommended_action="maintain_session",
                applied_action="maintain_session",
                continuous_auth_status="active",
                reason_code=reason_code,
            )
        if applied_level == "medium":
            return RiskDecision(
                raw_level=raw_level,
                applied_level=applied_level,
                authentication_level="traditional",
                recommended_action="increase_monitoring",
                applied_action="observe_session",
                continuous_auth_status="active",
                reason_code=reason_code,
            )
        if applied_level == "high":
            return RiskDecision(
                raw_level=raw_level,
                applied_level=applied_level,
                authentication_level="verification_required",
                recommended_action="request_reverification",
                applied_action="mark_verification_required",
                continuous_auth_status="verification_required",
                reason_code=reason_code,
            )
        if self.settings.AUTO_REVOKE_CRITICAL_SESSION:
            return RiskDecision(
                raw_level=raw_level,
                applied_level=applied_level,
                authentication_level="terminated",
                recommended_action="terminate_session",
                applied_action="terminate_session",
                continuous_auth_status="terminated",
                reason_code=reason_code,
            )
        return RiskDecision(
            raw_level=raw_level,
            applied_level=applied_level,
            authentication_level="restricted",
            recommended_action="restrict_operations",
            applied_action="mark_restricted",
            continuous_auth_status="restricted",
            reason_code=reason_code,
        )
