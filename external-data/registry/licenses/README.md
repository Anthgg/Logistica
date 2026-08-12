# Evidencias de licencia

Este directorio registra metadatos, pero no incluye acuerdos firmados ni datasets.

Antes de cambiar un dataset a `approved`:

1. Guarde una copia de la licencia o EULA vigente.
2. Si requiere acuerdo, guarde también la evidencia de aprobación.
3. Mantenga esos documentos fuera de Git; `.gitignore` los bloquea.
4. Complete `license_copy_path`, `agreement_evidence_path`, `download_url`,
   `approved_download_hosts` y el SHA-256 esperado en `datasets.yaml`.
5. Ejecute `python scripts/verify_dataset_licenses.py`.

Los resúmenes de términos no sustituyen una revisión legal ni el documento oficial.
