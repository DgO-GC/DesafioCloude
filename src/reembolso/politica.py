"""Política v3 — único lugar com números de política (plan.md §4)."""
from dataclasses import dataclass
from decimal import Decimal

DIA = "dia"          # limite vale para a soma do dia (RN-009)
DIARIA = "diaria"    # limite vale por diária do item (RN-010)


@dataclass(frozen=True)
class Limite:
    valor: Decimal
    periodicidade: str


LIMITES = {
    "alimentacao": Limite(Decimal("60.00"), DIA),
    "transporte_urbano": Limite(Decimal("80.00"), DIA),
    "hospedagem": Limite(Decimal("250.00"), DIARIA),
}
NOTA_FISCAL_ACIMA_DE = Decimal("100.00")
ACRESCIMO_VIAGEM = Decimal("0.50")
