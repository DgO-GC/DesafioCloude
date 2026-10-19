"""Aritmética monetária. Nenhum valor passa por float (plan.md §1)."""
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")


def formatar(valor: Decimal) -> str:
    """Spec 4.2: texto com exatamente duas casas decimais."""
    return f"{valor:.2f}"


def arredondar(valor: Decimal) -> Decimal:
    """RN-002: centavos, meio para cima (afastando do zero), uma única vez na entrada."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
