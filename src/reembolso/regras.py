"""Núcleo do motor: aplica as regras da spec na ordem da seção 8 (plan.md DT-001)."""
from dataclasses import dataclass, field
from decimal import Decimal

from .dinheiro import ZERO
from .entrada import Despesa, Entrada

APROVADO = "aprovado"
PARCIAL = "parcial"
RECUSADO = "recusado"
IGNORADO = "ignorado"
STATUS = (APROVADO, PARCIAL, RECUSADO, IGNORADO)


@dataclass(frozen=True)
class Motivo:
    codigo: str
    regra: str
    mensagem: str


@dataclass
class Avaliacao:
    despesa: Despesa
    reembolsavel: Decimal
    encerrada_como: str | None = None
    motivos: list = field(default_factory=list)

    @property
    def elegivel(self) -> bool:
        return self.encerrada_como is None

    def encerrar(self, status: str, codigo: str, regra: str, mensagem: str) -> None:
        self.encerrada_como = status
        self.reembolsavel = ZERO
        self.motivos.append(Motivo(codigo, regra, mensagem))

    @property
    def status(self) -> str:
        """RN-012: status derivado do encerramento e do valor (plan.md DT-002)."""
        if self.encerrada_como:
            return self.encerrada_como
        if self.reembolsavel == self.despesa.valor:
            return APROVADO
        if self.reembolsavel == ZERO:
            return RECUSADO
        return PARCIAL


def elegiveis(avaliacoes):
    return [a for a in avaliacoes if a.elegivel]


# Ordem = spec seção 8. Cada etapa recebe a lista inteira (regras de agregação).
ETAPAS = []


def avaliar(entrada: Entrada) -> list:
    avaliacoes = [Avaliacao(d, d.valor) for d in entrada.despesas]
    for etapa in ETAPAS:
        etapa(avaliacoes, entrada)
    return avaliacoes
