# Phase 040 — Quantity Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The quantity service handles all quantity difference calculations and validations.

## 2. Operations

| Operation                   | Method                          | Description                    |
| --------------------------- | ------------------------------- | ------------------------------ |
| Calculate difference        | `calculate_difference()`        | Compute qty difference         |
| Calculate financial impact  | `calculate_financial_impact()`  | Compute monetary impact        |
| Validate quantities         | `validate_quantities()`         | Validate qty values            |
| Batch calculate             | `batch_calculate()`             | Calculate for multiple items   |

## 3. Implementation

```python
class QuantityService:
    """Quantity difference calculations."""
    
    def calculate_difference(
        self,
        expected: Quantity,
        received: Quantity,
    ) -> Quantity:
        """
        Calculate quantity difference.
        
        Args:
            expected: Expected quantity
            received: Received quantity
            
        Returns:
            Difference (expected - received)
        """
        return strict_decimal_diff(expected, received)[0]
    
    def calculate_financial_impact(
        self,
        difference: Quantity,
        unit_cost: MonetaryAmount,
    ) -> MonetaryAmount:
        """
        Calculate financial impact.
        
        Args:
            difference: Quantity difference
            unit_cost: Unit cost
            
        Returns:
            Total financial impact
        """
        return MonetaryAmount(
            value=difference * unit_cost.value,
            currency=unit_cost.currency,
        )
    
    def validate_quantities(
        self,
        expected: Quantity,
        received: Quantity,
    ) -> List[str]:
        """
        Validate quantity values.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if expected <= 0:
            errors.append("Expected quantity must be positive")
        
        if received < 0:
            errors.append("Received quantity cannot be negative")
        
        return errors
    
    def batch_calculate(
        self,
        items: List[Tuple[Quantity, Quantity, MonetaryAmount]],
    ) -> List[Tuple[Quantity, MonetaryAmount]]:
        """
        Calculate differences for multiple items.
        
        Args:
            items: List of (expected, received, unit_cost) tuples
            
        Returns:
            List of (difference, financial_impact) tuples
        """
        results = []
        
        for expected, received, unit_cost in items:
            difference = self.calculate_difference(expected, received)
            impact = self.calculate_financial_impact(difference, unit_cost)
            results.append((difference, impact))
        
        return results
```

## 4. Calculation Examples

| Expected | Received | Difference | Unit Cost | Financial Impact |
| -------- | -------- | ---------- | --------- | ---------------- |
| 100      | 95       | 5          | $10.00    | $50.00           |
| 50       | 55       | -5         | $20.00    | -$100.00         |
| 200      | 200      | 0          | $5.00     | $0.00            |
| 10       | 0        | 10         | $100.00   | $1,000.00        |

## 5. Precision Rules

| Operation     | Precision  | Rounding     |
| ------------- | ---------- | ------------ |
| Quantity      | 3 decimals | Floor        |
| Monetary      | 2 decimals | Half-up      |
| Percentage    | 2 decimals | Half-up      |

---

**See also**: `06_severity_policy.md` for impact-based severity
