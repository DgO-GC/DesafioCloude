"""RN-002 — arredondamento monetário (AMB-010)."""
import unittest
from decimal import Decimal

from reembolso.dinheiro import arredondar
from tests.apoio import despesa, itens


class TestRN002Arredondamento(unittest.TestCase):
    def test_rn002_tres_casas_arredonda_para_centavos(self):
        item = itens(despesa(id="a", valor=33.333))["a"]
        self.assertEqual(item["valor_informado"], "33.333")
        self.assertEqual(item["valor_considerado"], "33.33")

    def test_rn002_meio_centavo_arredonda_para_cima(self):
        self.assertEqual(arredondar(Decimal("10.005")), Decimal("10.01"))

    def test_rn002_abaixo_do_meio_arredonda_para_baixo(self):
        self.assertEqual(arredondar(Decimal("10.004")), Decimal("10.00"))

    def test_rn002_negativo_meio_centavo_afasta_do_zero(self):
        self.assertEqual(arredondar(Decimal("-0.005")), Decimal("-0.01"))

    def test_rn002_valor_sai_sempre_com_duas_casas(self):
        item = itens(despesa(id="a", valor=12))["a"]
        self.assertEqual(item["valor_considerado"], "12.00")
        self.assertEqual(item["valor_reembolsavel"], "12.00")


if __name__ == "__main__":
    unittest.main()
