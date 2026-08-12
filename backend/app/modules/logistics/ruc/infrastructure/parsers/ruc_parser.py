"""Streaming Parser for SUNAT Reduced Padrón files (General & Annexes)."""

import hashlib
import io
import re
from typing import Generator, List, Tuple

from app.modules.logistics.ruc.domain.value_objects.enums import DomicileCondition, TaxpayerStatus


class RucRegistryParser:
    """Streams and parses raw text lines from SUNAT reduced padrón files."""

    @classmethod
    def parse_general_padron_stream(cls, raw_bytes: bytes) -> Generator[dict, None, None]:
        """Parses SUNAT RUC general padrón text line by line.

        Format: RUC|RAZON_SOCIAL|ESTADO_PATRON|CONDICION_DOMICILIO|UBIGEO|...
        """
        # Try encodings ISO-8859-1 / Latin-1 or UTF-8
        try:
            text_content = raw_bytes.decode("latin-1")
        except UnicodeDecodeError:
            text_content = raw_bytes.decode("utf-8", errors="replace")

        stream = io.StringIO(text_content)
        for line_num, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                parts = line.split(",")

            if len(parts) < 2:
                continue

            raw_ruc = parts[0].strip()
            if not raw_ruc.isdigit() or len(raw_ruc) != 11:
                continue

            legal_name = parts[1].strip() if len(parts) > 1 else ""
            if not legal_name:
                continue

            status_raw = parts[2].strip() if len(parts) > 2 else ""
            cond_raw = parts[3].strip() if len(parts) > 3 else ""
            ubigeo = parts[4].strip() if len(parts) > 4 else ""

            status_norm = TaxpayerStatus.normalize_raw(status_raw).value
            cond_norm = DomicileCondition.normalize_raw(cond_raw).value

            record_hash = hashlib.sha256(f"{raw_ruc}|{legal_name}|{status_norm}|{cond_norm}|{ubigeo}".encode("utf-8")).hexdigest()

            yield {
                "ruc": raw_ruc,
                "normalized_ruc": raw_ruc,
                "legal_name": legal_name[:300],
                "normalized_legal_name": legal_name.upper()[:300],
                "taxpayer_status_raw": status_raw[:100],
                "taxpayer_status_normalized": status_norm,
                "domicile_condition_raw": cond_raw[:100],
                "domicile_condition_normalized": cond_norm,
                "ubigeo_code": ubigeo[:10] if ubigeo else None,
                "record_hash": record_hash,
            }

    @classmethod
    def parse_annex_padron_stream(cls, raw_bytes: bytes) -> Generator[dict, None, None]:
        """Parses SUNAT annex address padrón text line by line.

        Format: RUC|UBIGEO|DIRECCION_ANEXA|...
        """
        try:
            text_content = raw_bytes.decode("latin-1")
        except UnicodeDecodeError:
            text_content = raw_bytes.decode("utf-8", errors="replace")

        stream = io.StringIO(text_content)
        for line_num, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < 2:
                parts = line.split(",")

            if len(parts) < 2:
                continue

            raw_ruc = parts[0].strip()
            if not raw_ruc.isdigit() or len(raw_ruc) != 11:
                continue

            ubigeo = parts[1].strip() if len(parts) > 1 else ""
            address = parts[2].strip() if len(parts) > 2 else parts[1].strip()

            if not address:
                continue

            record_hash = hashlib.sha256(f"{raw_ruc}|{ubigeo}|{address}".encode("utf-8")).hexdigest()

            yield {
                "ruc": raw_ruc,
                "ubigeo_code": ubigeo[:10] if ubigeo else None,
                "address_raw": address,
                "address_normalized": address.upper(),
                "record_hash": record_hash,
            }
