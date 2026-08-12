# 08 — Parser Streaming Versionado (`RucRegistryParser`)

## 1. Procesamiento Streaming Línea a Línea

Para procesar padrones de más de 10 millones de registros sin saturar la memoria RAM del servidor (limitando el footprint a `< 256MB`), `RucRegistryParser` implementa un enfoque de lectura por bloques y generadores Python (`yield`):

```python
class RucRegistryParser:
    DEFAULT_ENCODING = "latin-1"  # Formato oficial de codificación SUNAT

    @classmethod
    def parse_general_padron_stream(cls, raw_bytes: bytes, chunk_size: int = 10000):
        buffer = ""
        stream = io.StringIO(raw_bytes.decode(cls.DEFAULT_ENCODING, errors="replace"))
        
        batch = []
        for line in stream:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) >= 5:
                ruc_raw = parts[0].strip()
                if PeruvianRucValidator.validate(ruc_raw):
                    record = {
                        "ruc": ruc_raw,
                        "normalized_ruc": PeruvianRucValidator.normalize(ruc_raw),
                        "legal_name": parts[1].strip().upper(),
                        "normalized_legal_name": cls.normalize_text(parts[1]),
                        "taxpayer_status_raw": parts[2].strip(),
                        "taxpayer_status_normalized": cls.map_status(parts[2].strip()),
                        "domicile_condition_raw": parts[3].strip(),
                        "domicile_condition_normalized": cls.map_condition(parts[3].strip()),
                        "ubigeo_code": parts[4].strip() if len(parts) > 4 else None,
                    }
                    batch.append(record)
                    
                    if len(batch) >= chunk_size:
                        yield batch
                        batch = []
        
        if batch:
            yield batch
```

---

## 2. Tolerancia a Fallos y Registro de Errores

1. **Líneas Malformadas**: Si una línea no contiene los delimitadores requeridos (`|`) o el RUC resulta sintácticamente inválido, el registro se desecha e incrementa el contador `rejected_rows` de la versión del dataset.
2. **Sustitución de Caracteres**: Se utiliza `errors="replace"` en el decodificador `latin-1` para evitar excepciones por bytes no imprimibles o secuencias corruptas en la Razón Social.
