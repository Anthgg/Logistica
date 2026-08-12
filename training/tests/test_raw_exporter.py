from pathlib import Path

import pandas as pd
import pytest

from src.common.hashing import sha256_bytes
from src.facial.raw_exporter import RawExportError, export_facial_raw


def _captures(content: bytes) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "capture_id": "capture-1",
                "session_id": "session-1",
                "sequence_number": 1,
                "storage_path": "session-1/capture-1.jpg",
                "checksum": sha256_bytes(content),
            }
        ]
    )


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    return (
        tmp_path / "data" / "raw" / "facial",
        tmp_path / "data" / "interim" / "facial_export_staging",
        tmp_path / "data" / "reports" / "pilot" / "facial_raw_export.json",
    )


def test_export_downloads_and_verifies_checksum(tmp_path):
    content = b"verified-image-content"
    raw, staging, report = _paths(tmp_path)

    def downloader(bucket: str, object_name: str, target: Path) -> None:
        assert bucket == "private-bucket"
        assert object_name == "session-1/capture-1.jpg"
        target.write_bytes(content)

    result = export_facial_raw(
        _captures(content),
        bucket="private-bucket",
        raw_root=raw,
        staging_root=staging,
        report_path=report,
        downloader=downloader,
    )

    assert result.exported == 1
    assert (raw / "session-1" / "capture-1.jpg").read_bytes() == content
    assert report.is_file()


def test_export_is_idempotent_and_never_overwrites(tmp_path):
    content = b"existing-image-content"
    raw, staging, report = _paths(tmp_path)
    target = raw / "session-1" / "capture-1.jpg"
    target.parent.mkdir(parents=True)
    target.write_bytes(content)

    def must_not_download(bucket: str, object_name: str, target: Path) -> None:
        raise AssertionError("No debe descargar un archivo raw existente.")

    result = export_facial_raw(
        _captures(content),
        bucket="private-bucket",
        raw_root=raw,
        staging_root=staging,
        report_path=report,
        downloader=must_not_download,
    )

    assert result.already_present == 1
    assert target.read_bytes() == content


def test_export_rejects_existing_checksum_mismatch(tmp_path):
    expected = b"expected"
    raw, staging, report = _paths(tmp_path)
    target = raw / "session-1" / "capture-1.jpg"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"different")

    with pytest.raises(RawExportError):
        export_facial_raw(
            _captures(expected),
            bucket="private-bucket",
            raw_root=raw,
            staging_root=staging,
            report_path=report,
        )

    assert target.read_bytes() == b"different"


def test_export_dry_run_does_not_create_raw(tmp_path):
    raw, staging, report = _paths(tmp_path)
    result = export_facial_raw(
        _captures(b"planned"),
        bucket="private-bucket",
        raw_root=raw,
        staging_root=staging,
        report_path=report,
        dry_run=True,
    )

    assert result.exported == 0
    assert not raw.exists()
    assert not staging.exists()
    assert not report.exists()
