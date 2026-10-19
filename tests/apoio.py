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


def rodar(*despesas, **periodo) -> dict:
    """Retorna a saída completa. Valores com casas decimais são passados como texto JSON."""
    return calcular(json.dumps(entrada(*despesas, **periodo)))


def itens(*despesas, **periodo) -> dict:
    """Atalho: itens da saída indexados por id."""
    return {i["id"]: i for i in rodar(*despesas, **periodo)["itens"]}


def codigos(item: dict) -> list:
    return [m["codigo"] for m in item["motivos"]]
