"""Núcleo do motor: aplica as regras da spec na ordem da seção 8 (plan.md DT-001)."""
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from . import cambio, politica
from .dinheiro import ZERO, arredondar
from .cambio import BRL, Cambio
from .entrada import Despesa, Entrada
from .politica import Politica

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
    valor: Decimal | None       # valor considerado em BRL; None = sem cotação (RN-014)
    reembolsavel: Decimal
    taxa: Decimal | None = None
    data_cotacao: object = None
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
        if self.reembolsavel == self.valor:
            return APROVADO
        if self.reembolsavel == ZERO:
            return RECUSADO
        return PARCIAL


@dataclass(frozen=True)
class Contexto:
    """O que toda etapa enxerga (plan.md DT-007)."""
    entrada: Entrada
    politica: Politica
    cambio: Cambio
    nome_tabela: str
    limites: dict


def montar_contexto(entrada: Entrada, pol: Politica, cambio: Cambio) -> Contexto:
    nome, limites = pol.tabela_para(entrada.colaborador.get("centro_custo"))
    return Contexto(entrada, pol, cambio, nome, limites)


def avaliacao_inicial(d: Despesa, cambio: Cambio) -> Avaliacao:
    """RN-014: BRL não converte; demais moedas convertem já aqui para que o valor apareça na saída
    mesmo se uma regra anterior recusar o item. A recusa por falta de cotação é a etapa da seção 8."""
    if d.moeda == BRL:
        return Avaliacao(d, d.valor, d.valor)
    cotacao = cambio.cotacao(d.moeda, d.data)
    if cotacao is None:
        return Avaliacao(d, None, ZERO)
    taxa, dia = cotacao
    valor = arredondar(d.valor_informado * taxa)  # AMB-022: arredonda só o produto
    return Avaliacao(d, valor, valor, taxa, dia)


def elegiveis(avaliacoes):
    return [a for a in avaliacoes if a.elegivel]


def periodo_de_competencia(avaliacoes, ctx):
    """RN-004: data da despesa dentro de [inicio, fim], inclusivo."""
    e = ctx.entrada
    for a in elegiveis(avaliacoes):
        if not e.inicio <= a.despesa.data <= e.fim:
            a.encerrar(RECUSADO, "FORA_DA_COMPETENCIA", "RN-004",
                       f"Data {a.despesa.data} fora do período {e.inicio} a {e.fim}.")


def valor_nao_positivo(avaliacoes, ctx):
    """RN-005: estorno ou zero é ignorado e não abate nada."""
    for a in elegiveis(avaliacoes):
        if a.despesa.valor <= ZERO:
            a.encerrar(IGNORADO, "VALOR_NAO_POSITIVO", "RN-005",
                       f"Valor {a.despesa.valor} não é positivo (estorno ou zero); não abate outras despesas.")


def categoria_da_politica(avaliacoes, ctx):
    """RN-006: só categorias com limite na tabela aplicável."""
    for a in elegiveis(avaliacoes):
        categoria = a.despesa.categoria
        if categoria not in ctx.limites:
            a.encerrar(RECUSADO, "CATEGORIA_NAO_REEMBOLSAVEL", "RN-006",
                       f"Categoria '{categoria}' não está na política de reembolso (tabela {ctx.nome_tabela}).")
        elif ctx.limites[categoria].valor == ZERO:
            a.encerrar(RECUSADO, "CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO", "RN-006",
                       f"Categoria '{categoria}' não é reembolsável na tabela {ctx.nome_tabela} (limite 0,00).")


def duplicatas(avaliacoes, ctx):
    """RN-007: mesma data, categoria, fornecedor e valor; a primeira na ordem da entrada vale."""
    originais = {}
    for a in elegiveis(avaliacoes):
        d = a.despesa
        chave = (d.data, d.categoria, d.fornecedor.strip().casefold(), d.moeda, d.valor)  # AMB-028
        if chave in originais:
            a.encerrar(RECUSADO, "DUPLICATA", "RN-007",
                       f"Duplicata da despesa {originais[chave]} (mesma data, categoria, fornecedor e valor).")
        else:
            originais[chave] = d.id


def conversao_cambial(avaliacoes, ctx):
    """RN-014: sem cotação aplicável, recusa."""
    for a in elegiveis(avaliacoes):
        if a.valor is None:
            a.encerrar(RECUSADO, "MOEDA_SEM_COTACAO", "RN-014",
                       f"Sem cotação de {a.despesa.moeda} em {a.despesa.data} nem nos "
                       f"{cambio.JANELA_DIAS} dias anteriores.")


def nota_fiscal(avaliacoes, ctx):
    """RN-008: acima (estritamente) do limiar da tabela, em BRL, exige nota; sem nota, recusa integral."""
    limiar = ctx.politica.nota_fiscal_acima_de
    for a in elegiveis(avaliacoes):
        if a.valor > limiar and not a.despesa.tem_nota_fiscal:
            a.encerrar(RECUSADO, "SEM_NOTA_FISCAL", "RN-008",
                       f"Valor R$ {a.valor} acima de R$ {limiar} exige nota fiscal.")


NOMES = {"alimentacao": "alimentação", "transporte_urbano": "transporte urbano", "hospedagem": "hospedagem"}


def dias_em_viagem(avaliacoes, ctx) -> set:
    """RN-011: dias D..D+N cobertos por hospedagem positiva no período, mesmo se ela for recusada."""
    entrada = ctx.entrada
    dias = set()
    for a in avaliacoes:
        d = a.despesa
        if d.categoria == "hospedagem" and d.valor > ZERO and entrada.inicio <= d.data <= entrada.fim:
            dias.update(d.data + timedelta(days=i) for i in range(diarias(d.descricao) + 1))
    return dias


def limite_diario(avaliacoes, ctx):
    """RN-009 + RN-011: limite da soma do dia por categoria, saldo consumido na ordem da entrada."""
    viagem = dias_em_viagem(avaliacoes, ctx)
    acrescimo = ctx.politica.acrescimo_viagem
    saldos = {}
    for a in elegiveis(avaliacoes):
        d = a.despesa
        limite = ctx.limites[d.categoria]
        if limite.periodicidade != politica.DIA:
            continue
        em_viagem = d.data in viagem
        teto = arredondar(limite.valor * (1 + acrescimo)) if em_viagem else limite.valor
        chave = (d.data, d.categoria)
        saldo = saldos.get(chave, teto)
        concedido = min(a.valor, saldo)
        if concedido < a.valor:
            a.reembolsavel = concedido
            a.motivos.append(Motivo(
                "LIMITE_DIARIO", "RN-009",
                f"Limite diário de {NOMES.get(d.categoria, d.categoria)} em {d.data}"
                f"{f' (em viagem, +{acrescimo * 100:g}%)' if em_viagem else ''} é R$ {teto}; "
                f"restavam R$ {saldo}. Glosados R$ {a.valor - concedido}."))
        saldos[chave] = saldo - concedido


_DIARIAS = re.compile(r"(\d+)\s*(?:diarias?|noites?)\b")


def diarias(descricao: str) -> int:
    """RN-010: 'N diária(s)/noite(s)' na descrição, com ou sem acento; senão (ou zero), 1 (plan.md DT-004)."""
    sem_acento = unicodedata.normalize("NFKD", descricao).encode("ascii", "ignore").decode().lower()
    achado = _DIARIAS.search(sem_acento)
    return max(int(achado.group(1)), 1) if achado else 1


def limite_hospedagem(avaliacoes, ctx):
    """RN-010: limite por diária, cada hospedagem limitada sozinha."""
    for a in elegiveis(avaliacoes):
        d = a.despesa
        limite = ctx.limites[d.categoria]
        if limite.periodicidade != politica.DIARIA:
            continue
        n = diarias(d.descricao)
        teto = limite.valor * n
        if a.valor > teto:
            a.reembolsavel = teto
            a.motivos.append(Motivo(
                "LIMITE_HOSPEDAGEM", "RN-010",
                f"Limite de hospedagem é R$ {limite.valor} por diária × {n} diária(s) = R$ {teto}. "
                f"Glosados R$ {a.valor - teto}."))


# Ordem = spec seção 8. Cada etapa recebe a lista inteira (regras de agregação).
ETAPAS = [
    periodo_de_competencia,    # RN-004
    valor_nao_positivo,        # RN-005
    categoria_da_politica,     # RN-006
    duplicatas,                # RN-007
    conversao_cambial,         # RN-014
    nota_fiscal,               # RN-008
    limite_diario,             # RN-009
    limite_hospedagem,         # RN-010
]


def avaliar(ctx: Contexto) -> list:
    avaliacoes = [avaliacao_inicial(d, ctx.cambio) for d in ctx.entrada.despesas]
    for etapa in ETAPAS:
        etapa(avaliacoes, ctx)
    return avaliacoes
