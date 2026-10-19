"""Leitura e validação da entrada (RN-001, spec 4.1 e 4.3)."""
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .dinheiro import arredondar


class EntradaInvalida(Exception):
    pass


@dataclass(frozen=True)
class Despesa:
    id: str
    data: date
    categoria: str
    categoria_informada: str
    descricao: str
    fornecedor: str
    valor_informado: Decimal
    valor: Decimal
    tem_nota_fiscal: bool


@dataclass(frozen=True)
class Entrada:
    colaborador: dict
    periodo: dict
    inicio: date
    fim: date
    despesas: list


def carregar_json(texto: str) -> dict:
    try:
        return json.loads(texto, parse_float=Decimal, parse_int=Decimal)
    except json.JSONDecodeError as erro:
        raise EntradaInvalida(f"JSON inválido: {erro}") from erro


def ler_entrada(dados) -> Entrada:
    if not isinstance(dados, dict):
        raise EntradaInvalida("a entrada deve ser um objeto JSON")
    colaborador = _objeto(dados, "colaborador", "entrada")
    _texto(colaborador, "id", "colaborador")
    periodo = _objeto(dados, "periodo", "entrada")
    _texto(periodo, "competencia", "periodo")
    inicio = _data(periodo, "inicio", "periodo")
    fim = _data(periodo, "fim", "periodo")
    if inicio > fim:
        raise EntradaInvalida(f"periodo.inicio ({inicio}) é posterior a periodo.fim ({fim})")
    brutas = dados.get("despesas")
    if not isinstance(brutas, list):
        raise EntradaInvalida("campo 'despesas' ausente ou não é uma lista")
    despesas = [_despesa(bruta, posicao) for posicao, bruta in enumerate(brutas)]
    return Entrada(colaborador=_sem_decimal(colaborador), periodo=_sem_decimal(periodo),
                   inicio=inicio, fim=fim, despesas=despesas)


def _despesa(bruta, posicao: int) -> Despesa:
    if not isinstance(bruta, dict):
        raise EntradaInvalida(f"despesa na posição {posicao} não é um objeto")
    onde = f"despesa {bruta.get('id', f'na posição {posicao}')}"
    id_ = _texto(bruta, "id", onde)
    categoria = _texto(bruta, "categoria", onde)
    valor = bruta.get("valor")
    if not isinstance(valor, Decimal):
        raise EntradaInvalida(f"{onde}: campo 'valor' ausente ou não numérico")
    nota = bruta.get("tem_nota_fiscal")
    if not isinstance(nota, bool):
        raise EntradaInvalida(f"{onde}: campo 'tem_nota_fiscal' ausente ou não booleano")
    return Despesa(
        id=id_,
        data=_data(bruta, "data", onde),
        categoria=categoria,
        categoria_informada=categoria,
        descricao=_texto_opcional(bruta, "descricao", onde),
        fornecedor=_texto_opcional(bruta, "fornecedor", onde),
        valor_informado=valor,
        valor=arredondar(valor),
        tem_nota_fiscal=nota,
    )


def _objeto(dados: dict, campo: str, onde: str) -> dict:
    valor = dados.get(campo)
    if not isinstance(valor, dict):
        raise EntradaInvalida(f"{onde}: campo '{campo}' ausente ou não é um objeto")
    return valor


def _texto(dados: dict, campo: str, onde: str) -> str:
    valor = dados.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise EntradaInvalida(f"{onde}: campo '{campo}' ausente ou não é texto")
    return valor


def _texto_opcional(dados: dict, campo: str, onde: str) -> str:
    valor = dados.get(campo, "")
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise EntradaInvalida(f"{onde}: campo '{campo}' não é texto")
    return valor


def _data(dados: dict, campo: str, onde: str) -> date:
    valor = _texto(dados, campo, onde)
    try:
        if len(valor) != 10:
            raise ValueError
        return date.fromisoformat(valor)
    except ValueError:
        raise EntradaInvalida(f"{onde}: campo '{campo}' = '{valor}' não é data AAAA-MM-DD") from None


def _sem_decimal(valor):
    """Cópias repassadas à saída não podem carregar Decimal (não serializável)."""
    if isinstance(valor, dict):
        return {k: _sem_decimal(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_sem_decimal(v) for v in valor]
    if isinstance(valor, Decimal):
        return str(valor)
    return valor
