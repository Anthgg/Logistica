# 22. Integración Futura con Fase 093

La Fase 093 implementará la firma digital remota de manifiestos y la validación SUNAT.

## Puntos de Contacto
- **Firma digital XAdES / XML**: Al emitirse el documento logístico, se enviará el snapshot al microservicio de firma digital para generar el XML sellado.
- **Envío a SUNAT**: El resultado del envío a SUNAT se agregará como un artefacto secundario de tipo `SUNAT_CDR` vinculado a la instancia de documento original.
