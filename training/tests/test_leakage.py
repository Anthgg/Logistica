from pathlib import Path

import pandas as pd
import pytest

import src.pipeline as pipeline_module
from src.datasets.leakage_checker import CriticalLeakageError, check_leakage
from src.pilot.readiness import evaluate_readiness
from src.reports.pilot_report import build_pilot_report, write_pilot_report


def test_no_hash_is_repeated_between_train_and_test():
    frame = pd.DataFrame(
        [
            {"checksum": "a", "split": "train"},
            {"checksum": "b", "split": "test"},
        ]
    )
    assert check_leakage(frame) == []


def test_leakage_checker_stops_critical_leakage():
    frame = pd.DataFrame(
        [
            {"checksum": "same", "split": "train"},
            {"checksum": "same", "split": "test"},
        ]
    )
    with pytest.raises(CriticalLeakageError):
        check_leakage(frame)


def test_pilot_report_is_generated(tmp_path):
    readiness = {"status": "not_ready", "checks": []}
    report = build_pilot_report(
        dataset_version="pilot-v0.1.0",
        protocol_version="protocol",
        session_summary=pd.DataFrame(),
        facial_table=pd.DataFrame(),
        behavioral_table=pd.DataFrame(),
        split_table=pd.DataFrame(),
        readiness=readiness,
    )
    report_path, readiness_path = write_pilot_report(
        report, readiness, tmp_path
    )
    assert report_path.is_file()
    assert readiness_path.is_file()


def test_readiness_detects_critical_conditions(config):
    readiness = evaluate_readiness(
        config=config,
        audit=pd.DataFrame(),
        face_quality=pd.DataFrame(),
        validated_batches=pd.DataFrame(),
        windows=pd.DataFrame(),
        features=pd.DataFrame(),
        manifests={},
        leakage_findings=[],
        frozen_test_exists=False,
        freeze_requested=False,
        raw_unchanged=True,
    )
    assert readiness["status"] == "not_ready"
    assert "pilot_participants" in readiness["critical_failures"]


def test_complete_pipeline_works_without_fabricating_pilot(
    tmp_path, config, monkeypatch
):
    class FakeEngine:
        def dispose(self):
            return None

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/database")
    monkeypatch.setattr(pipeline_module, "load_config", lambda value=None: config)
    monkeypatch.setattr(
        pipeline_module, "create_database_engine", lambda value: FakeEngine()
    )
    monkeypatch.setattr(
        pipeline_module, "load_sessions", lambda engine, **values: pd.DataFrame()
    )
    monkeypatch.setattr(
        pipeline_module, "load_captures", lambda engine, **values: pd.DataFrame()
    )
    monkeypatch.setattr(
        pipeline_module,
        "load_behavioral_batches",
        lambda engine, **values: pd.DataFrame(),
    )
    result = pipeline_module.run_preparation_pipeline()
    assert result.readiness_status == "not_ready"
    assert result.report_path.is_file()
    assert result.readiness_path.is_file()
