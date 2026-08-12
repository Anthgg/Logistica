from pathlib import Path

import pytest

from evaluation.src.common.integrity import (
    EvaluationGateError,
    begin_execution,
    create_or_verify_lock,
    preflight,
    verify_and_open_frozen_test,
)
from evaluation.src.common.io import sha256_file


def test_preflight_approves_complete_synthetic_bundle(
    synthetic_config,
) -> None:
    result = preflight(synthetic_config)
    assert result.approved
    assert result.as_json()["test_manifest_opened"] is False


def test_frozen_manifest_hash_mismatch_stops_before_parquet_load(
    synthetic_config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synthetic_config.paths.frozen_test_checksum.write_text(
        "0" * 64 + "\n", encoding="utf-8"
    )
    opened = False

    def forbidden_read(*args: object, **kwargs: object) -> object:
        nonlocal opened
        opened = True
        raise AssertionError("read_parquet no debe ejecutarse")

    monkeypatch.setattr("pandas.read_parquet", forbidden_read)
    with pytest.raises(EvaluationGateError, match="SHA-256"):
        verify_and_open_frozen_test(synthetic_config)
    assert not opened


def test_full_frozen_verification_uses_only_synthetic_data(
    synthetic_config,
) -> None:
    frame = verify_and_open_frozen_test(synthetic_config)
    assert len(frame) == 2
    assert set(frame["split"]) == {"test"}


def test_multiple_samples_in_one_session_are_valid(
    synthetic_config,
) -> None:
    import pandas as pd

    manifest = synthetic_config.paths.frozen_test_manifest
    frame = pd.read_parquet(manifest)
    frame["session_id"] = "shared-test-session"
    frame.to_parquet(manifest, index=False)
    synthetic_config.paths.frozen_test_checksum.write_text(
        sha256_file(manifest) + "\n",
        encoding="utf-8",
    )
    verified = verify_and_open_frozen_test(synthetic_config)
    assert len(verified) == 2


def test_session_shared_with_development_is_rejected(
    synthetic_config,
) -> None:
    import pandas as pd

    manifest = synthetic_config.paths.frozen_test_manifest
    frame = pd.read_parquet(manifest)
    frame.loc[0, "session_id"] = "session-development-0"
    frame.to_parquet(manifest, index=False)
    synthetic_config.paths.frozen_test_checksum.write_text(
        sha256_file(manifest) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(EvaluationGateError, match="session_id=1"):
        verify_and_open_frozen_test(synthetic_config)


def test_lock_is_idempotent_and_detects_config_change(
    synthetic_config,
) -> None:
    lock = create_or_verify_lock(synthetic_config, device="cpu")
    assert lock.is_file()
    assert create_or_verify_lock(synthetic_config, device="cpu") == lock
    synthetic_config.source_path.write_text(
        "synthetic: changed\n", encoding="utf-8"
    )
    with pytest.raises(EvaluationGateError, match="no coincide"):
        create_or_verify_lock(synthetic_config, device="cpu")


def test_second_execution_requires_authorized_reason(
    synthetic_config,
) -> None:
    first = begin_execution(
        synthetic_config,
        authorized_rerun=False,
        rerun_reason=None,
        command=["run_final_evaluation.py"],
    )
    assert first.started_path.is_file()
    with pytest.raises(EvaluationGateError, match="repetición"):
        begin_execution(
            synthetic_config,
            authorized_rerun=False,
            rerun_reason=None,
            command=["run_final_evaluation.py"],
        )
    with pytest.raises(EvaluationGateError, match="al menos 10"):
        begin_execution(
            synthetic_config,
            authorized_rerun=True,
            rerun_reason="corto",
            command=["run_final_evaluation.py"],
        )
    rerun = begin_execution(
        synthetic_config,
        authorized_rerun=True,
        rerun_reason="Revisión extraordinaria autorizada",
        command=["run_final_evaluation.py"],
    )
    assert rerun.authorized_rerun
    assert rerun.rerun_reason == "Revisión extraordinaria autorizada"


def test_authorized_rerun_requires_previous_execution(
    synthetic_config,
) -> None:
    with pytest.raises(EvaluationGateError, match="ejecución previa"):
        begin_execution(
            synthetic_config,
            authorized_rerun=True,
            rerun_reason="Incidente técnico ya autorizado",
            command=["run_final_evaluation.py"],
        )
