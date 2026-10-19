"""Única camada que toca disco e código de saída (plan.md §2)."""
import argparse
import json
import sys
from pathlib import Path

from .entrada import EntradaInvalida, carregar_json, ler_entrada
from .regras import avaliar
from .saida import montar_saida

OK, ERRO_ENTRADA = 0, 1


def calcular(texto_entrada: str) -> dict:
    entrada = ler_entrada(carregar_json(texto_entrada))
    return montar_saida(entrada, avaliar(entrada))


def main(argv=None) -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")  # Windows usa cp1252 em pipes e quebra acentos
    parser = argparse.ArgumentParser(prog="reembolso", description="Motor de cálculo de reembolso")
    sub = parser.add_subparsers(dest="comando", required=True)
    cmd = sub.add_parser("calcular", help="avalia um arquivo de despesas")
    cmd.add_argument("--input", required=True, type=Path, help="JSON de despesas")
    cmd.add_argument("--output", required=True, type=Path, help="JSON de resultado")
    args = parser.parse_args(argv)

    try:
        texto = args.input.read_text(encoding="utf-8")
        resultado = calcular(texto)
    except OSError as erro:
        print(f"erro: não foi possível ler {args.input}: {erro}", file=sys.stderr)
        return ERRO_ENTRADA
    except EntradaInvalida as erro:
        print(f"erro: entrada inválida: {erro}", file=sys.stderr)
        return ERRO_ENTRADA

    args.output.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return OK
