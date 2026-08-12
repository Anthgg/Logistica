# Phase 040 — PDF Generator

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The PDF generator creates **DIF (Documento de Incidencia de Facturación)** documents using the `reportlab` library.

**Source**: `app/modules/logistics/inbound/reception_differences/infrastructure/pdf_generator.py`

## 2. Document Structure

```
┌─────────────────────────────────────────────────┐
│                  DIF Document                    │
├─────────────────────────────────────────────────┤
│  Header                                          │
│  ├── Company Logo                                │
│  ├── Document Title: "Documento de Incidencia"  │
│  ├── Document Number: DIF-YYYY-XXXXXX           │
│  └── Date: DD/MM/YYYY                           │
├─────────────────────────────────────────────────┤
│  Case Information                                │
│  ├── Case ID                                     │
│  ├── Reception Reference                         │
│  ├── Supplier                                    │
│  ├── Warehouse                                   │
│  ├── Category                                    │
│  └── Severity                                    │
├─────────────────────────────────────────────────┤
│  Items Table                                     │
│  ├── SKU                                         │
│  ├── Description                                 │
│  ├── Expected Qty                                │
│  ├── Received Qty                                │
│  ├── Difference                                  │
│  ├── Unit Cost                                   │
│  └── Total Impact                                │
├─────────────────────────────────────────────────┤
│  Summary                                         │
│  ├── Total Items                                 │
│  ├── Total Financial Impact                      │
│  └── Responsibility Assignment                   │
├─────────────────────────────────────────────────┤
│  Evidence References                             │
│  ├── Evidence 1: [URL]                           │
│  └── Evidence 2: [URL]                           │
├─────────────────────────────────────────────────┤
│  Approvals                                       │
│  ├── Prepared by: _______________                │
│  ├── Reviewed by: _______________                │
│  └── Approved by: _______________                │
├─────────────────────────────────────────────────┤
│  Footer                                          │
│  ├── Page number                                 │
│  ├── Generation timestamp                        │
│  └── Canonical hash                              │
└─────────────────────────────────────────────────┘
```

## 3. Implementation

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class DIFGenerator:
    """Generate DIF PDF documents."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate(
        self,
        case: CaseAggregate,
        output_path: str,
    ) -> str:
        """
        Generate DIF document PDF.
        
        Args:
            case: Case aggregate with all data
            output_path: Path to save PDF
            
        Returns:
            Path to generated PDF
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch,
        )
        
        elements = []
        
        # Header
        elements.extend(self._build_header(case))
        elements.append(Spacer(1, 0.5*inch))
        
        # Case info
        elements.extend(self._build_case_info(case))
        elements.append(Spacer(1, 0.3*inch))
        
        # Items table
        elements.extend(self._build_items_table(case))
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary
        elements.extend(self._build_summary(case))
        elements.append(Spacer(1, 0.3*inch))
        
        # Evidence
        elements.extend(self._build_evidence_section(case))
        elements.append(Spacer(1, 0.5*inch))
        
        # Approvals
        elements.extend(self._build_approvals(case))
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        elements.extend(self._build_footer(case))
        
        doc.build(elements)
        return output_path
    
    def _build_header(self, case: CaseAggregate) -> list:
        """Build document header."""
        elements = []
        elements.append(Paragraph(
            "Documento de Incidencia de Facturación",
            self.styles["Title"]
        ))
        elements.append(Paragraph(
            f"DIF-{case.created_at.year}-{case.id.hex[:6].upper()}",
            self.styles["Heading2"]
        ))
        return elements
    
    def _build_items_table(self, case: CaseAggregate) -> list:
        """Build items table."""
        headers = ["SKU", "Tipo", "Esperado", "Recibido", "Diferencia", "Costo Unit.", "Impacto"]
        data = [headers]
        
        for item in case.items:
            data.append([
                item.sku,
                item.item_type.value,
                str(item.expected_qty),
                str(item.received_qty),
                str(item.difference_qty),
                f"${item.unit_cost:,.2f}" if item.unit_cost else "-",
                f"${item.total_impact:,.2f}" if item.total_impact else "-",
            ])
        
        table = Table(data)
        table.setStyle(self.styles["TableStyle"])
        
        return [table]
```

## 4. Document Numbering

Format: `DIF-{YEAR}-{SEQUENCE}`

```python
def generate_document_number(year: int, sequence: int) -> str:
    """Generate DIF document number."""
    return f"DIF-{year}-{sequence:06d}"
```

## 5. PDF Configuration

| Setting               | Value                                    |
| --------------------- | ---------------------------------------- |
| Page Size             | Letter (8.5" x 11")                     |
| Margins               | 0.75" all sides                         |
| Font                  | Helvetica (default)                      |
| Header Font Size      | 18pt                                    |
| Body Font Size        | 10pt                                    |
| Table Font Size       | 9pt                                     |
| Output Format         | PDF 1.4                                 |

## 6. Integration Points

| Component             | Interaction                              |
| --------------------- | ---------------------------------------- |
| `DocumentService`     | Triggers PDF generation                  |
| `CaseRepository`      | Fetches case data                        |
| Storage Service       | Stores generated PDF                     |
| Notification Service  | Notifies stakeholders of document        |

---

**See also**: `24_document_service.md` for document workflow
