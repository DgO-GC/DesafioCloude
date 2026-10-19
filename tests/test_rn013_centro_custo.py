"""RN-013 / RN-006 — tabela de limites por centro de custo (AMB-016, AMB-017, AMB-018, AMB-019).

Usa a tabela vigente (politicas/politica-v4.json).
"""
import unittest

from tests.apoio import codigos, despesa, itens, politica, rodar


def alim(valor, **c):
    return despesa(id="a", categoria="alimentacao", valor=valor, **c)


class TestRN013CentroDeCusto(unittest.TestCase):
    def test_rn013_cc_comercial_usa_a_propria_tabela(self):
        saida = rodar(alim(95), centro_custo="CC-COMERCIAL")
        self.assertEqual(saida["tabela_de_limites"], "CC-COMERCIAL")
        self.assertEqual(saida["itens"][0]["valor_reembolsavel"], "90.00")

    def test_rn013_cc_comercial_transporte_150_e_hospedagem_400(self):
        # Datas diferentes: a hospedagem tornaria o dia do transporte "em viagem" (RN-011).
        r = itens(despesa(id="t", data="2026-07-05", categoria="transporte_urbano", valor=160),
                  despesa(id="h", data="2026-07-20", categoria="hospedagem", valor=450, descricao="Hotel"),
                  centro_custo="CC-COMERCIAL")
        self.assertEqual(r["t"]["valor_reembolsavel"], "150.00")
        self.assertEqual(r["h"]["valor_reembolsavel"], "400.00")

    def test_rn013_representacao_existe_no_cc_comercial(self):
        r = itens(despesa(id="r", categoria="representacao", valor=340), centro_custo="CC-COMERCIAL")
        self.assertEqual((r["r"]["status"], r["r"]["valor_reembolsavel"]), ("parcial", "300.00"))

    def test_rn013_cc_sem_entrada_usa_padrao(self):
        """AMB-016."""
        saida = rodar(alim(95), centro_custo="CC-SUPORTE-N2")
        self.assertEqual(saida["tabela_de_limites"], "padrao")
        self.assertEqual(saida["itens"][0]["valor_reembolsavel"], "60.00")

    def test_rn013_cc_ausente_ou_vazio_usa_padrao(self):
        self.assertEqual(rodar(alim(10), centro_custo=None)["tabela_de_limites"], "padrao")
        self.assertEqual(rodar(alim(10), centro_custo="")["tabela_de_limites"], "padrao")

    def test_rn013_cc_comparado_exatamente(self):
        """AMB-016: 'cc-comercial' não é 'CC-COMERCIAL'."""
        self.assertEqual(rodar(alim(10), centro_custo="cc-comercial")["tabela_de_limites"], "padrao")

    def test_rn013_categoria_ausente_no_cc_herda_do_padrao(self):
        """AMB-017: CC-ADM não lista hospedagem → 250,00 do padrão."""
        r = itens(despesa(id="h", categoria="hospedagem", valor=300, descricao="Hotel"), centro_custo="CC-ADM")
        self.assertEqual((r["h"]["status"], r["h"]["valor_reembolsavel"]), ("parcial", "250.00"))

    def test_rn013_cc_adm_alimentacao_45(self):
        self.assertEqual(itens(alim(50), centro_custo="CC-ADM")["a"]["valor_reembolsavel"], "45.00")

    def test_rn006_limite_zero_bloqueia_categoria(self):
        """AMB-018: CC-ENG-PLATAFORMA não reembolsa hospedagem."""
        r = itens(despesa(id="h", categoria="hospedagem", valor=480, descricao="2 diarias"),
                  centro_custo="CC-ENG-PLATAFORMA")
        self.assertEqual(r["h"]["status"], "recusado")
        self.assertEqual(codigos(r["h"]), ["CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO"])

    def test_rn006_bloqueio_vem_antes_da_nota_fiscal(self):
        r = itens(despesa(id="h", categoria="hospedagem", valor=690, tem_nota_fiscal=False),
                  centro_custo="CC-ENG-PLATAFORMA")
        self.assertEqual(codigos(r["h"]), ["CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO"])

    def test_rn006_representacao_fora_do_cc_comercial_e_recusada(self):
        """AMB-019."""
        r = itens(despesa(id="r", categoria="representacao", valor=190), centro_custo="CC-SUPORTE-N2")
        self.assertEqual(codigos(r["r"]), ["CATEGORIA_NAO_REEMBOLSAVEL"])

    def test_rn013_cc_pode_acrescentar_e_substituir_em_tabela_qualquer(self):
        pol = politica(centros_custo={"CC-X": {"alimentacao": {"limite": 10, "periodicidade": "dia"},
                                               "taxi_aereo": {"limite": 999, "periodicidade": "dia"}}})
        r = itens(alim(20), despesa(id="t", categoria="taxi_aereo", valor=500), politica=pol, centro_custo="CC-X")
        self.assertEqual(r["a"]["valor_reembolsavel"], "10.00")
        self.assertEqual(r["t"]["status"], "aprovado")


if __name__ == "__main__":
    unittest.main()
