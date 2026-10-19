"""Monta o documento de saída (spec 4.2, RN-012)."""
from .dinheiro import ZERO, formatar
from .regras import IGNORADO, STATUS, Contexto

VERSAO_SCHEMA = "1.0"


def montar_saida(ctx: Contexto, avaliacoes: list) -> dict:
    entrada = ctx.entrada
    itens = [_item(a) for a in avaliacoes]
    solicitado = sum((a.valor for a in avaliacoes if a.status != IGNORADO and a.valor is not None), ZERO)
    reembolsavel = sum((a.reembolsavel for a in avaliacoes), ZERO)
    por_status = {s: 0 for s in STATUS}
    for a in avaliacoes:
        por_status[a.status] += 1
    return {
        "versao_schema": VERSAO_SCHEMA,
        "politica": ctx.politica.versao,
        "tabela_de_limites": ctx.nome_tabela,
        "colaborador": entrada.colaborador,
        "periodo": entrada.periodo,
        "itens": itens,
        "totais": {
            "valor_solicitado": formatar(solicitado),
            "valor_reembolsavel": formatar(reembolsavel),
            "valor_glosado": formatar(solicitado - reembolsavel),
            "itens_por_status": por_status,
        },
    }


def _item(a) -> dict:
    d = a.despesa
    return {
        "id": d.id,
        "data": d.data.isoformat(),
        "categoria": d.categoria,
        "moeda": d.moeda,
        "valor_informado": str(d.valor_informado),
        "taxa_cambio": None if a.taxa is None else str(a.taxa),
        "data_cotacao": None if a.data_cotacao is None else a.data_cotacao.isoformat(),
        "valor_considerado": None if a.valor is None else formatar(a.valor),
        "valor_reembolsavel": formatar(a.reembolsavel),
        "status": a.status,
        "motivos": [{"codigo": m.codigo, "regra": m.regra, "mensagem": m.mensagem} for m in a.motivos],
    }
