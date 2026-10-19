"""Única camada que toca disco e código de saída (plan.md §2)."""
import argparse
import json
import sys
from pathlib import Path

from .entrada import EntradaInvalida, carregar_json, ler_entrada
from .politica import carregar_politica
from .regras import avaliar, montar_contexto
from .saida import montar_saida

OK, ERRO_ENTRADA = 0, 1
# Cópias vigentes versionadas no repo; resolvidas a partir do pacote, não do diretório atual.
POLITICAS = Path(__file__).resolve().parents[2] / "politicas"
POLITICA_PADRAO = POLITICAS / "politica-v4.json"


def calcular(texto_entrada: str, texto_politica: str | None = None) -> dict:
    if texto_politica is None:
        texto_politica = POLITICA_PADRAO.read_text(encoding="utf-8")
    pol = carregar_politica(carregar_json(texto_politica))
    entrada = ler_entrada(carregar_json(texto_entrada))
    ctx = montar_contexto(entrada, pol)
    return montar_saida(ctx, avaliar(ctx))


def main(argv=None) -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")  # Windows usa cp1252 em pipes e quebra acentos
    parser = argparse.ArgumentParser(prog="reembolso", description="Motor de cálculo de reembolso")
    sub = parser.add_subparsers(dest="comando", required=True)
    cmd = sub.add_parser("calcular", help="avalia um arquivo de despesas")
    cmd.add_argument("--input", required=True, type=Path, help="JSON de despesas")
    cmd.add_argument("--output", required=True, type=Path, help="JSON de resultado")
    cmd.add_argument("--politica", type=Path, default=POLITICA_PADRAO,
                     help=f"tabela de política (padrão: {POLITICA_PADRAO.name})")
    args = parser.parse_args(argv)

    try:
        texto = args.input.read_text(encoding="utf-8")
        texto_politica = args.politica.read_text(encoding="utf-8")
        resultado = calcular(texto, texto_politica)
    except OSError as erro:
        print(f"erro: não foi possível ler {erro.filename}: {erro.strerror}", file=sys.stderr)
        return ERRO_ENTRADA
    except EntradaInvalida as erro:
        print(f"erro: entrada inválida: {erro}", file=sys.stderr)
        return ERRO_ENTRADA

    args.output.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    return OK
