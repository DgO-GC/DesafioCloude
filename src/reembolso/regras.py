"""Núcleo do motor: aplica as regras da spec na ordem da seção 8 (plan.md DT-001)."""
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from . import politica
from .dinheiro import ZERO, arredondar
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


def valor_nao_positivo(avaliacoes, entrada):
    """RN-005: estorno ou zero é ignorado e não abate nada."""
    for a in elegiveis(avaliacoes):
        if a.despesa.valor <= ZERO:
            a.encerrar(IGNORADO, "VALOR_NAO_POSITIVO", "RN-005",
                       f"Valor {a.despesa.valor} não é positivo (estorno ou zero); não abate outras despesas.")


def categoria_da_politica(avaliacoes, entrada):
    """RN-006: só categorias com limite definido na política."""
    for a in elegiveis(avaliacoes):
        if a.despesa.categoria not in politica.LIMITES:
            a.encerrar(RECUSADO, "CATEGORIA_NAO_REEMBOLSAVEL", "RN-006",
                       f"Categoria '{a.despesa.categoria}' não está na política de reembolso.")


def duplicatas(avaliacoes, entrada):
    """RN-007: mesma data, categoria, fornecedor e valor; a primeira na ordem da entrada vale."""
    originais = {}
    for a in elegiveis(avaliacoes):
        d = a.despesa
        chave = (d.data, d.categoria, d.fornecedor.strip().casefold(), d.valor)
        if chave in originais:
            a.encerrar(RECUSADO, "DUPLICATA", "RN-007",
                       f"Duplicata da despesa {originais[chave]} (mesma data, categoria, fornecedor e valor).")
        else:
            originais[chave] = d.id


def nota_fiscal(avaliacoes, entrada):
    """RN-008: acima (estritamente) do limiar exige nota; sem nota, recusa integral."""
    limiar = politica.NOTA_FISCAL_ACIMA_DE
    for a in elegiveis(avaliacoes):
        if a.despesa.valor > limiar and not a.despesa.tem_nota_fiscal:
            a.encerrar(RECUSADO, "SEM_NOTA_FISCAL", "RN-008",
                       f"Valor {a.despesa.valor} acima de R$ {limiar} exige nota fiscal.")


NOMES = {"alimentacao": "alimentação", "transporte_urbano": "transporte urbano", "hospedagem": "hospedagem"}


def dias_em_viagem(avaliacoes, entrada) -> set:
    """RN-011: dias D..D+N cobertos por hospedagem positiva no período, mesmo se ela for recusada."""
    dias = set()
    for a in avaliacoes:
        d = a.despesa
        if d.categoria == "hospedagem" and d.valor > ZERO and entrada.inicio <= d.data <= entrada.fim:
            dias.update(d.data + timedelta(days=i) for i in range(diarias(d.descricao) + 1))
    return dias


def limite_diario(avaliacoes, entrada):
    """RN-009 + RN-011: limite da soma do dia por categoria, saldo consumido na ordem da entrada."""
    viagem = dias_em_viagem(avaliacoes, entrada)
    saldos = {}
    for a in elegiveis(avaliacoes):
        d = a.despesa
        limite = politica.LIMITES[d.categoria]
        if limite.periodicidade != politica.DIA:
            continue
        em_viagem = d.data in viagem
        teto = arredondar(limite.valor * (1 + politica.ACRESCIMO_VIAGEM)) if em_viagem else limite.valor
        chave = (d.data, d.categoria)
        saldo = saldos.get(chave, teto)
        concedido = min(d.valor, saldo)
        if concedido < d.valor:
            a.reembolsavel = concedido
            a.motivos.append(Motivo(
                "LIMITE_DIARIO", "RN-009",
                f"Limite diário de {NOMES.get(d.categoria, d.categoria)} em {d.data}"
                f"{' (em viagem, +50%)' if em_viagem else ''} é R$ {teto}; "
                f"restavam R$ {saldo}. Glosados R$ {d.valor - concedido}."))
        saldos[chave] = saldo - concedido


_DIARIAS = re.compile(r"(\d+)\s*(?:diarias?|noites?)\b")


def diarias(descricao: str) -> int:
    """RN-010: 'N diária(s)/noite(s)' na descrição, com ou sem acento; senão (ou zero), 1 (plan.md DT-004)."""
    sem_acento = unicodedata.normalize("NFKD", descricao).encode("ascii", "ignore").decode().lower()
    achado = _DIARIAS.search(sem_acento)
    return max(int(achado.group(1)), 1) if achado else 1


def limite_hospedagem(avaliacoes, entrada):
    """RN-010: limite por diária, cada hospedagem limitada sozinha."""
    for a in elegiveis(avaliacoes):
        d = a.despesa
        limite = politica.LIMITES[d.categoria]
        if limite.periodicidade != politica.DIARIA:
            continue
        n = diarias(d.descricao)
        teto = limite.valor * n
        if d.valor > teto:
            a.reembolsavel = teto
            a.motivos.append(Motivo(
                "LIMITE_HOSPEDAGEM", "RN-010",
                f"Limite de hospedagem é R$ {limite.valor} por diária × {n} diária(s) = R$ {teto}. "
                f"Glosados R$ {d.valor - teto}."))


# Ordem = spec seção 8. Cada etapa recebe a lista inteira (regras de agregação).
ETAPAS = [
    periodo_de_competencia,    # RN-004
    valor_nao_positivo,        # RN-005
    categoria_da_politica,     # RN-006
    duplicatas,                # RN-007
    nota_fiscal,               # RN-008
    limite_diario,             # RN-009
    limite_hospedagem,         # RN-010
]


def avaliar(entrada: Entrada) -> list:
    avaliacoes = [Avaliacao(d, d.valor) for d in entrada.despesas]
    for etapa in ETAPAS:
        etapa(avaliacoes, entrada)
    return avaliacoes
