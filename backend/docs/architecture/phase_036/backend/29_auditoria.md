# Auditoría

Se registran eventos para creación/cambio/envío/cancelación del aviso, líneas y transporte; calendario, ventanas, blackouts y holds; creación, confirmación, reprogramación y cancelación de citas; y emisión de CIT.

Cada evento conserva actor, organización, recurso, sede/almacén cuando aplica, valores previos/nuevos, motivo, sesión/correlación y metadata. Los jobs sin actor humano usan outbox/historial técnico y no inventan una identidad.

Los códigos están centralizados en `app/modules/logistics/audit/catalog.py`.

