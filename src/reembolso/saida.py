"""Monta o documento de saída (spec 4.2, RN-012)."""
from .dinheiro import ZERO, formatar
from .regras import IGNORADO, STATUS, Contexto

VERSAO_SCHEMA = "1.0"


def montar_saida(ctx: Contexto, avaliacoes: list) -> dict:
    entrada = ctx.entrada
    itens = [_item(a) for a in avaliacoes]
    solicitado = sum((a.despesa.valor for a in avaliacoes if a.status != IGNORADO), ZERO)
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
        "valor_informado": str(d.valor_informado),
        "valor_considerado": formatar(d.valor),
        "valor_reembolsavel": formatar(a.reembolsavel),
        "status": a.status,
        "motivos": [{"codigo": m.codigo, "regra": m.regra, "mensagem": m.mensagem} for m in a.motivos],
    }
