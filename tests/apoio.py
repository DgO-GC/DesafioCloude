"""Monta entradas em memória para os testes de regra."""
import json

from reembolso.cli import calcular

_contador = 0


def despesa(**campos) -> dict:
    global _contador
    _contador += 1
    base = {
        "id": f"t-{_contador:03d}",
        "data": "2026-07-10",
        "categoria": "alimentacao",
        "descricao": "",
        "fornecedor": f"Fornecedor {_contador}",
        "valor": 10.00,
        "tem_nota_fiscal": True,
    }
    base.update(campos)
    return base


def entrada(*despesas, inicio="2026-07-01", fim="2026-07-31") -> dict:
    return {
        "colaborador": {"id": "c-teste", "nome": "Teste", "centro_custo": "CC-TESTE"},
        "periodo": {"competencia": inicio[:7], "inicio": inicio, "fim": fim},
        "despesas": list(despesas),
    }


def politica(centros_custo=None, **campos) -> dict:
    """Tabela de política em memória: padrão igual ao da v4, com ajustes."""
    base = {
        "versao": "teste",
        "moeda_base": "BRL",
        "padrao": {
            "alimentacao": {"limite": 60.00, "periodicidade": "dia"},
            "transporte_urbano": {"limite": 80.00, "periodicidade": "dia"},
            "hospedagem": {"limite": 250.00, "periodicidade": "diaria"},
        },
        "centros_custo": centros_custo or {},
        "nota_fiscal_obrigatoria_acima_de": 100.00,
        "acrescimo_em_viagem_percentual": 50,
    }
    base.update(campos)
    return base


def rodar(*despesas, politica=None, cambio=None, centro_custo="CC-TESTE", **periodo) -> dict:
    """Retorna a saída completa. politica/cambio=None usam as tabelas vigentes de politicas/."""
    dados = entrada(*despesas, **periodo)
    dados["colaborador"]["centro_custo"] = centro_custo
    texto_politica = None if politica is None else json.dumps(politica)
    texto_cambio = None if cambio is None else json.dumps(cambio)
    return calcular(json.dumps(dados), texto_politica, texto_cambio)


def itens(*despesas, **opcoes) -> dict:
    """Atalho: itens da saída indexados por id."""
    return {i["id"]: i for i in rodar(*despesas, **opcoes)["itens"]}


def codigos(item: dict) -> list:
    return [m["codigo"] for m in item["motivos"]]
