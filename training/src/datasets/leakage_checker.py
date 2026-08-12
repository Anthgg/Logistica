from dataclasses import dataclass

import pandas as pd


class CriticalLeakageError(RuntimeError):
    pass


@dataclass(frozen=True)
class LeakageFinding:
    check: str
    severity: str
    count: int
    identifiers: list[str]


def _cross_split_duplicates(
    frame: pd.DataFrame, column: str, check: str
) -> LeakageFinding | None:
    if frame.empty or column not in frame or "split" not in frame:
        return None
    grouped = (
        frame.dropna(subset=[column, "split"])
        .groupby(column)["split"]
        .nunique()
    )
    leaked = grouped[grouped > 1]
    if leaked.empty:
        return None
    return LeakageFinding(
        check=check,
        severity="critical",
        count=len(leaked),
        identifiers=sorted(str(value) for value in leaked.index)[:100],
    )


def _overlap_findings(frame: pd.DataFrame) -> LeakageFinding | None:
    required = {"session_id", "window_started_at", "window_ended_at", "split"}
    if frame.empty or not required <= set(frame.columns):
        return None
    leaked: set[str] = set()
    for session_id, windows in frame.groupby("session_id"):
        records = windows.sort_values("window_started_at").to_dict(orient="records")
        for index, left in enumerate(records):
            for right in records[index + 1 :]:
                if right["window_started_at"] >= left["window_ended_at"]:
                    break
                if left["split"] != right["split"]:
                    leaked.add(str(session_id))
    if not leaked:
        return None
    return LeakageFinding(
        check="window_overlap_cross_split",
        severity="critical",
        count=len(leaked),
        identifiers=sorted(leaked)[:100],
    )


def check_leakage(
    frame: pd.DataFrame,
    *,
    raise_on_critical: bool = True,
) -> list[LeakageFinding]:
    checks = {
        "capture_id": "capture_id_cross_split",
        "checksum": "checksum_cross_split",
        "session_id": "session_cross_split",
        "batch_id": "batch_id_cross_split",
        "event_id": "event_id_cross_split",
        "window_id": "window_id_cross_split",
        "segment_id": "segment_cross_split",
        "pad_source_id": "pad_source_cross_split",
    }
    findings = [
        finding
        for column, check in checks.items()
        if (finding := _cross_split_duplicates(frame, column, check)) is not None
    ]
    overlap = _overlap_findings(frame)
    if overlap:
        findings.append(overlap)
    if raise_on_critical and any(item.severity == "critical" for item in findings):
        summary = ", ".join(
            f"{item.check}={item.count}" for item in findings
        )
        raise CriticalLeakageError(
            "Se detectó fuga crítica entre particiones: " + summary
        )
    return findings


def check_manifest_collection(
    manifests: list[pd.DataFrame], *, raise_on_critical: bool = True
) -> list[LeakageFinding]:
    findings: list[LeakageFinding] = []
    for frame in manifests:
        findings.extend(check_leakage(frame, raise_on_critical=False))
    if raise_on_critical and findings:
        raise CriticalLeakageError(
            "Se detectó fuga crítica: "
            + ", ".join(f"{item.check}={item.count}" for item in findings)
        )
    return findings
