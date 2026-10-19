"""Tabela de câmbio do financeiro: carga, validação e busca de cotação (spec 4.5, RN-014, RN-015)."""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .entrada import EntradaInvalida

BRL = "BRL"
JANELA_DIAS = 7  # RN-014: cotação de até 7 dias corridos antes da despesa (plan.md DT-008)


@dataclass(frozen=True)
class Cambio:
    taxas: dict  # {date: {moeda: Decimal}}

    def cotacao(self, moeda: str, dia: date):
        """(taxa, data da cotação) da própria data ou da mais recente anterior dentro da janela; senão None."""
        for atras in range(JANELA_DIAS + 1):
            candidata = dia - timedelta(days=atras)
            taxa = self.taxas.get(candidata, {}).get(moeda)
            if taxa is not None:
                return taxa, candidata
        return None


def carregar_cambio(dados) -> Cambio:
    if not isinstance(dados, dict):
        raise _erro("deve ser um objeto JSON")
    if dados.get("moeda_base") != BRL:
        raise _erro("campo 'moeda_base' deve ser 'BRL'")
    brutas = dados.get("taxas")
    if not isinstance(brutas, dict):
        raise _erro("campo 'taxas' ausente ou não é um objeto")
    taxas = {}
    for texto_data, por_moeda in brutas.items():
        try:
            dia = date.fromisoformat(texto_data)
        except (TypeError, ValueError):
            raise _erro(f"data '{texto_data}' não é AAAA-MM-DD") from None
        if not isinstance(por_moeda, dict):
            raise _erro(f"taxas de {texto_data} não são um objeto")
        taxas[dia] = {}
        for moeda, taxa in por_moeda.items():
            if not isinstance(taxa, Decimal) or taxa <= 0:
                raise _erro(f"taxa {moeda} em {texto_data} ausente, não numérica ou não positiva")
            taxas[dia][moeda.strip().upper()] = taxa
    return Cambio(taxas)


def _erro(mensagem: str) -> EntradaInvalida:
    return EntradaInvalida(f"tabela de câmbio: {mensagem}")
