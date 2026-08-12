# Raw externo — inmutable

Los archivos originales autorizados se colocan manualmente en el subdirectorio del
dataset. No se sobrescriben, transforman, renombran ni versionan en Git. Toda
extracción y adaptación escribe únicamente en `external-data/interim` o
`external-data/processed`.
