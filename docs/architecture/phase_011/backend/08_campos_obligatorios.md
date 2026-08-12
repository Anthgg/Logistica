# 08 — Esquema de Campos Obligatorios y Validación

## Estructura del Contrato JSON Schema (`required_fields_schema`)

```json
{
  "fields": [
    {
      "key": "supplier_id",
      "label": "Proveedor ID",
      "type": "uuid",
      "required": true
    },
    {
      "key": "delivery_address",
      "label": "Dirección de Entrega",
      "type": "string",
      "required": true
    }
  ]
}
```

## Tipos de Datos Soportados
* `string`, `text`, `integer`, `decimal`, `boolean`, `date`, `datetime`, `uuid`, `enum`, `money`, `quantity`, `coordinates`, `signature_reference`, `image_reference`, `list`.
