"""Tabela de política do financeiro: carga e validação (spec 4.4, RN-015; plan.md DT-006)."""
from dataclasses import dataclass
from decimal import Decimal

from .entrada import EntradaInvalida, normalizar_categoria

DIA = "dia"          # limite vale para a soma do dia (RN-009)
DIARIA = "diaria"    # limite vale por diária do item (RN-010)
PADRAO = "padrao"
APROVACAO_MANUAL_ACIMA_DE = Decimal("500.00")  # RN-016: fixo na spec, a tabela não traz


@dataclass(frozen=True)
class Limite:
    valor: Decimal
    periodicidade: str


@dataclass(frozen=True)
class Politica:
    versao: str
    padrao: dict
    centros_custo: dict
    nota_fiscal_acima_de: Decimal
    acrescimo_viagem: Decimal  # fração: 50% -> 0.50

    def tabela_para(self, centro_custo) -> tuple:
        """RN-013: (nome da tabela, {categoria: Limite}); o centro de custo substitui/acrescenta ao padrão."""
        if isinstance(centro_custo, str) and centro_custo in self.centros_custo:
            return centro_custo, {**self.padrao, **self.centros_custo[centro_custo]}
        return PADRAO, dict(self.padrao)


def carregar_politica(dados) -> Politica:
    if not isinstance(dados, dict):
        raise _erro("deve ser um objeto JSON")
    versao = dados.get("versao")
    if not isinstance(versao, str) or not versao.strip():
        raise _erro("campo 'versao' ausente ou não é texto")
    if dados.get("moeda_base") != "BRL":
        raise _erro("campo 'moeda_base' deve ser 'BRL'")
    padrao = _limites(dados.get("padrao"), "padrao")
    brutos = dados.get("centros_custo", {})
    if not isinstance(brutos, dict):
        raise _erro("campo 'centros_custo' não é um objeto")
    centros = {cc: _limites(lims, f"centros_custo.{cc}") for cc, lims in brutos.items()}
    return Politica(
        versao=versao,
        padrao=padrao,
        centros_custo=centros,
        nota_fiscal_acima_de=_valor(dados.get("nota_fiscal_obrigatoria_acima_de"),
                                    "nota_fiscal_obrigatoria_acima_de"),
        acrescimo_viagem=_valor(dados.get("acrescimo_em_viagem_percentual"),
                                "acrescimo_em_viagem_percentual") / 100,
    )


def _limites(brutos, onde: str) -> dict:
    if not isinstance(brutos, dict):
        raise _erro(f"'{onde}' ausente ou não é um objeto")
    limites = {}
    for categoria, bruto in brutos.items():
        if not isinstance(bruto, dict):
            raise _erro(f"'{onde}.{categoria}' não é um objeto")
        periodicidade = bruto.get("periodicidade")
        if periodicidade not in (DIA, DIARIA):
            raise _erro(f"'{onde}.{categoria}.periodicidade' deve ser '{DIA}' ou '{DIARIA}'")
        limites[normalizar_categoria(categoria)] = Limite(
            _valor(bruto.get("limite"), f"{onde}.{categoria}.limite"), periodicidade)
    return limites


def _valor(bruto, onde: str) -> Decimal:
    if not isinstance(bruto, Decimal) or bruto < 0:
        raise _erro(f"'{onde}' ausente, não numérico ou negativo")
    return bruto


def _erro(mensagem: str) -> EntradaInvalida:
    return EntradaInvalida(f"tabela de política: {mensagem}")
