"""Fase 7.5: incorporación controlada de datasets biométricos externos."""

from .registry import (
    DatasetEntry,
    DatasetNotApprovedError,
    LicenseGateError,
    load_registry,
)

__all__ = [
    "DatasetEntry",
    "DatasetNotApprovedError",
    "LicenseGateError",
    "load_registry",
]
