"""Aritmética monetária. Nenhum valor passa por float (plan.md §1)."""
from decimal import Decimal

ZERO = Decimal("0.00")


def formatar(valor: Decimal) -> str:
    """Spec 4.2: texto com exatamente duas casas decimais."""
    return f"{valor:.2f}"
