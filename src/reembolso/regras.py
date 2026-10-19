"""Núcleo do motor: aplica as regras da spec na ordem da seção 8 (plan.md DT-001)."""
from dataclasses import dataclass, field
from decimal import Decimal

from . import politica
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


def periodo_de_competencia(avaliacoes, entrada):
    """RN-004: data da despesa dentro de [inicio, fim], inclusivo."""
    for a in elegiveis(avaliacoes):
        if not entrada.inicio <= a.despesa.data <= entrada.fim:
            a.encerrar(RECUSADO, "FORA_DA_COMPETENCIA", "RN-004",
                       f"Data {a.despesa.data} fora do período {entrada.inicio} a {entrada.fim}.")


def categoria_da_politica(avaliacoes, entrada):
    """RN-006: só categorias com limite definido na política."""
    for a in elegiveis(avaliacoes):
        if a.despesa.categoria not in politica.LIMITES:
            a.encerrar(RECUSADO, "CATEGORIA_NAO_REEMBOLSAVEL", "RN-006",
                       f"Categoria '{a.despesa.categoria}' não está na política de reembolso.")


# Ordem = spec seção 8. Cada etapa recebe a lista inteira (regras de agregação).
ETAPAS = [
    periodo_de_competencia,    # RN-004
    categoria_da_politica,     # RN-006
]


def avaliar(entrada: Entrada) -> list:
    avaliacoes = [Avaliacao(d, d.valor) for d in entrada.despesas]
    for etapa in ETAPAS:
        etapa(avaliacoes, entrada)
    return avaliacoes
