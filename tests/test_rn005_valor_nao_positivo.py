"""RN-005 — valor não positivo / estorno (AMB-009)."""
import unittest

from tests.apoio import codigos, despesa, rodar


class TestRN005ValorNaoPositivo(unittest.TestCase):
    def test_rn005_estorno_e_ignorado(self):
        item = rodar(despesa(id="a", valor=-45.00, categoria="transporte_urbano"))["itens"][0]
        self.assertEqual(item["status"], "ignorado")
        self.assertEqual(item["valor_considerado"], "-45.00")
        self.assertEqual(item["valor_reembolsavel"], "0.00")
        self.assertEqual(codigos(item), ["VALOR_NAO_POSITIVO"])

    def test_rn005_valor_zero_e_ignorado(self):
        self.assertEqual(rodar(despesa(valor=0))["itens"][0]["status"], "ignorado")

    def test_rn005_estorno_nao_abate_do_total_nem_entra_no_solicitado(self):
        saida = rodar(despesa(valor=-45.00), despesa(valor=50))
        self.assertEqual(saida["totais"]["valor_solicitado"], "50.00")
        self.assertEqual(saida["totais"]["valor_reembolsavel"], "50.00")
        self.assertEqual(saida["totais"]["valor_glosado"], "0.00")


if __name__ == "__main__":
    unittest.main()
