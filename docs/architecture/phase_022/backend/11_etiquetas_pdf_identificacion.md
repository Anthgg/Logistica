# 11. Renderizado de Etiquetas PDF de Identificación Física

## Servicio `WarehouseLocationLabelService`

El servicio `WarehouseLocationLabelService` se encarga de la generación vectorial de etiquetas físicas para pegado en anaqueles, estantes y bins de almacenamiento. Integra la infraestructura de renderizado PDF de ReportLab y reutiliza el motor de plantillas configurado en la Fase 017 (`inventory.location_label`).

---

## Formato y Dimensiones de Etiqueta Estándar

El renderizador soporta dimensiones físicas parametrizables para impresoras térmicas industriales (Zebra, Honeywell, TSC):

| Formato | Ancho x Alto (mm) | Puntos ReportLab ($pt$) | Uso Tipico |
| :--- | :---: | :---: | :--- |
| **Estándar Anaquel** | $100 \times 50 \text{ mm}$ | $283.46 \times 141.73 \text{ pt}$ | Racks y niveles de almacenamiento principal. |
| **Mini Bin / Casillero**| $50 \times 25 \text{ mm}$ | $141.73 \times 70.86 \text{ pt}$ | Casilleros pequeños y gabinetes. |
| **Muelle / Pallet Area**| $150 \times 100 \text{ mm}$ | $425.20 \times 283.46 \text{ pt}$ | Letreros colgantes de zonas y muelles. |

---

## Estructura Visual de la Etiqueta (Plantilla Fase 017)

```
+-------------------------------------------------------------------+
|  ORGANIZACIÓN DEMO S.A.C.                      ALM-CENTRAL-01    |
|                                                                   |
|   +---------------+   CÓDIGO: ALM01-Z01-A03-R02-N04-P06           |
|   |               |   UBICACIÓN: POSICIÓN DE PICKING              |
|   |  CÓDIGO QR    |   ZONA: ALMACENAMIENTO GENERAL                |
|   |    OPACO      |   TIPO: POSITION                              |
|   |               |   RESTRICT: COLD_CHAIN (2°C - 8°C)            |
|   +---------------+                                               |
|   t1loc:v1:a8f9c1e2b4d5...                                        |
+-------------------------------------------------------------------+
```

---

## Implementación del Generador PDF Vectorial

```python
# app/services/logistics/label_service.py

import io
from typing import List
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.barcode import qr
from app.models.logistics.warehouse_location import WarehouseLocationModel
from app.services.logistics.qr_service import WarehouseLocationQRService

class WarehouseLocationLabelService:
    PAGE_WIDTH = 100 * mm
    PAGE_HEIGHT = 50 * mm

    @classmethod
    def generate_single_label_pdf(cls, location: WarehouseLocationModel) -> bytes:
        """Genera un PDF de página única para una ubicación."""
        return cls.generate_batch_labels_pdf([location])

    @classmethod
    def generate_batch_labels_pdf(cls, locations: List[WarehouseLocationModel]) -> bytes:
        """Genera un archivo PDF multipágina listo para impresión en lote."""
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(cls.PAGE_WIDTH, cls.PAGE_HEIGHT))

        for loc in locations:
            # Dibujar borde y encabezado
            pdf.setLineWidth(1)
            pdf.rect(2 * mm, 2 * mm, cls.PAGE_WIDTH - 4 * mm, cls.PAGE_HEIGHT - 4 * mm)
            
            # Nombre Organización / Almacén
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(5 * mm, cls.PAGE_HEIGHT - 7 * mm, f"ALMACÉN: {loc.warehouse.code}")
            
            # Código Completo Mnemónico en Negrita Grande
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(5 * mm, cls.PAGE_HEIGHT - 14 * mm, loc.full_code)

            # Tipo y Nombre de Ubicación
            pdf.setFont("Helvetica", 8)
            pdf.drawString(5 * mm, cls.PAGE_HEIGHT - 19 * mm, f"Tipo: {loc.location_type} | {loc.name}")

            # Generar e Insertar QR Opaco
            qr_payload = WarehouseLocationQRService.generate_payload(loc.public_ref)
            qr_code = qr.QrCodeWidget(qr_payload)
            bounds = qr_code.getBounds()
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]

            drawing = Drawing(25 * mm, 25 * mm, transform=[25 * mm / width, 0, 0, 25 * mm / height, 0, 0])
            drawing.add(qr_code)
            
            # Renderizar Drawing en las coordenadas especificadas
            pdf.renderDrawing(drawing, cls.PAGE_WIDTH - 30 * mm, 5 * mm)
            
            # Pie de etiqueta
            pdf.setFont("Helvetica-Oblique", 6)
            pdf.drawString(5 * mm, 5 * mm, f"Ref: {loc.public_ref[:16]}...")
            
            # Salto de página para la siguiente etiqueta
            pdf.showPage()

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()
```

---

## Endpoints de Exportación

1. **Etiqueta Individual:** `GET /api/logistics/warehouses/{id}/locations/{loc_id}/label-pdf`
   * Devuelve `Content-Type: application/pdf` con la etiqueta de la ubicación.
2. **Lote Multipágina:** `POST /api/logistics/warehouses/{id}/locations/labels-batch-pdf`
   * Acepta un arreglo de `location_ids` (hasta 500 ubicaciones) y retorna un único documento PDF compilado listo para la cola de impresión de la planta.
