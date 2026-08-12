"""Peruvian RUC syntactic validator using Modulo 11 (Phase 025)."""

import re


class PeruvianRucValidator:
    """Validates 11-digit Peruvian RUCs syntactically using Modulo 11."""

    ALLOWED_PREFIXES = ("10", "15", "16", "17", "20")
    FACTORS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

    @classmethod
    def validate(cls, ruc: str) -> bool:
        if not ruc:
            return False
        clean_ruc = re.sub(r"\D", "", ruc)
        if len(clean_ruc) != 11:
            return False
        if not clean_ruc.startswith(cls.ALLOWED_PREFIXES):
            return False

        digits = [int(c) for c in clean_ruc]
        check_digit = digits[-1]
        sum_products = sum(d * f for d, f in zip(digits[:-1], cls.FACTORS))
        remainder = sum_products % 11
        calculated_check = 11 - remainder
        if calculated_check == 10:
            calculated_check = 0
        elif calculated_check == 11:
            calculated_check = 1

        return check_digit == calculated_check

    @classmethod
    def normalize(cls, ruc: str) -> str:
        if not ruc:
            return ""
        return re.sub(r"\D", "", ruc).strip()
