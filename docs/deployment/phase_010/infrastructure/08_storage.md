# 08 — Almacenamiento de Objetos (Google Cloud Storage)

## Buckets por Ambiente
* **Staging:** `proyecto-t1-documents-staging`
* **Producción:** `proyecto-t1-documents-production`

## Políticas de Seguridad & Lifecycle
* **Uniform Bucket-Level Access:** Habilitado obligatoriamente. Sin acceso público directo.
* **Cifrado:** Encriptación administrada por Google (KMS).
* **URLs Firmadas:** Emisión de Signed URLs con expiración de 15 minutos para descargas de documentos logísticos.
* **Lifecycle Rules:** Purgado automático de archivos temporales mayores a 30 días.
