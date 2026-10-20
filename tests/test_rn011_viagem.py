"""RN-011 — dias em viagem ampliam limites diários em 50% (AMB-005, AMB-013)."""
import unittest

from tests.apoio import codigos, despesa, itens


def hotel(data="2026-07-14", descricao="Hotel Rio - 2 diarias", **campos):
    base = dict(id="h", data=data, categoria="hospedagem", valor=480, descricao=descricao)
    base.update(campos)
    return despesa(**base)


def alim(id_, data, valor):
    return despesa(id=id_, data=data, categoria="alimentacao", valor=valor)


class TestRN011Viagem(unittest.TestCase):
    def test_rn011_dia_coberto_pela_hospedagem_amplia_alimentacao_para_90(self):
        r = itens(hotel(), alim("a", "2026-07-15", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_limite_ampliado_e_90_e_glosa_o_excedente(self):
        r = itens(hotel(), alim("a", "2026-07-15", 95))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "90.00"))
        self.assertIn("em viagem", r["a"]["motivos"][0]["mensagem"])

    def test_rn011_transporte_em_viagem_vai_para_120(self):
        r = itens(hotel(), despesa(id="t", data="2026-07-14", categoria="transporte_urbano", valor=130))
        self.assertEqual(r["t"]["valor_reembolsavel"], "120.00")

    def test_rn011_dia_do_checkout_ainda_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-16", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_dia_seguinte_ao_checkout_nao_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-17", 85))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "60.00"))

    def test_rn011_dia_anterior_ao_checkin_nao_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-13", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_hospedagem_sem_nota_nao_caracteriza_viagem(self):
        """D-002: invertido. Antes (v2.0) a refeição saía aprovada com limite 90."""
        r = itens(hotel(data="2026-07-22", descricao="Airbnb 3 noites", valor=690, tem_nota_fiscal=False),
                  alim("a", "2026-07-24", 85))
        self.assertEqual(codigos(r["h"]), ["SEM_NOTA_FISCAL"])
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_brecha_hospedagem_falsa_30_noites(self):
        """D-002: hospedagem sem nota com '30 noites' não amplia os limites do mês."""
        r = itens(hotel(data="2026-07-01", descricao="Pousada 30 noites", valor=150, tem_nota_fiscal=False),
                  alim("a", "2026-07-15", 90),
                  despesa(id="t", data="2026-07-29", categoria="transporte_urbano", valor=100))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")
        self.assertEqual(r["t"]["valor_reembolsavel"], "80.00")

    def test_rn011_hospedagem_duplicada_sozinha_nao_estende_viagem(self):
        """D-002: a original (com nota) caracteriza; a cópia não acrescenta nada."""
        r = itens(hotel(id="h1", fornecedor="H", descricao="1 noite"), hotel(id="h2", fornecedor="H", descricao="1 noite"),
                  alim("a", "2026-07-15", 85))
        self.assertEqual(codigos(r["h2"]), ["DUPLICATA"])
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_hospedagem_fora_do_periodo_nao_caracteriza_viagem(self):
        r = itens(hotel(data="2026-06-30", descricao="3 noites"), alim("a", "2026-07-01", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_hospedagem_nao_tem_limite_ampliado(self):
        r = itens(hotel(descricao="Pousada", valor=300))
        self.assertEqual(r["h"]["valor_reembolsavel"], "250.00")

    def test_rn011_moeda_estrangeira_torna_o_dia_viagem(self):
        """AMB-024: táxi em EUR em 14/07 → refeição em BRL no mesmo dia tem limite 90.
        (Categoria diferente de propósito: outra alimentação consumiria o saldo do dia.)"""
        r = itens(despesa(id="e", data="2026-07-14", valor=5, moeda="EUR", categoria="transporte_urbano"),
                  alim("a", "2026-07-14", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_moeda_estrangeira_nao_estende_para_dias_vizinhos(self):
        r = itens(despesa(id="e", data="2026-07-14", valor=5, moeda="EUR"), alim("a", "2026-07-15", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_moeda_limite_compara_valor_convertido_em_viagem(self):
        """30 EUR em 17/07 = 178,80 BRL; o próprio item faz do dia viagem: CC-COMERCIAL 90 × 1,5 = 135."""
        r = itens(despesa(id="e", data="2026-07-17", valor=30, moeda="EUR"), centro_custo="CC-COMERCIAL")
        self.assertEqual(r["e"]["valor_reembolsavel"], "135.00")

    def test_rn011_moeda_estrangeira_sem_cotacao_ainda_caracteriza_viagem(self):
        r = itens(despesa(id="g", data="2026-07-21", valor=55, moeda="GBP"), alim("a", "2026-07-21", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_moeda_estorno_nao_caracteriza_viagem(self):
        r = itens(despesa(id="e", data="2026-07-14", valor=-5, moeda="EUR"), alim("a", "2026-07-14", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_sem_hospedagem_nao_ha_viagem(self):
        r = itens(alim("a", "2026-07-15", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")


if __name__ == "__main__":
    unittest.main()
