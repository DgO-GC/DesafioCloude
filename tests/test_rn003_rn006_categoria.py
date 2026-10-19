"""RN-003 (AMB-011) normalização de categoria e RN-006 (AMB-012) categorias da política."""
import unittest

from tests.apoio import codigos, despesa, itens


class TestRN003Normalizacao(unittest.TestCase):
    def test_rn003_maiusculas_viram_categoria_da_politica(self):
        item = itens(despesa(id="a", categoria="ALIMENTACAO", valor=20))["a"]
        self.assertEqual(item["categoria"], "alimentacao")
        self.assertEqual(item["status"], "aprovado")

    def test_rn003_espacos_nas_pontas_sao_removidos(self):
        item = itens(despesa(id="a", categoria="  Transporte_Urbano "))["a"]
        self.assertEqual(item["categoria"], "transporte_urbano")
        self.assertEqual(item["status"], "aprovado")

    def test_rn003_acento_diferencia_categoria(self):
        item = itens(despesa(id="a", categoria="alimentação"))["a"]
        self.assertEqual(codigos(item), ["CATEGORIA_NAO_REEMBOLSAVEL"])


class TestRN006CategoriasDaPolitica(unittest.TestCase):
    def test_rn006_coworking_e_recusado(self):
        item = itens(despesa(id="a", categoria="coworking", valor=89))["a"]
        self.assertEqual(item["status"], "recusado")
        self.assertEqual(item["valor_reembolsavel"], "0.00")
        self.assertEqual(codigos(item), ["CATEGORIA_NAO_REEMBOLSAVEL"])
        self.assertEqual(item["motivos"][0]["regra"], "RN-006")

    def test_rn006_tres_categorias_sao_aceitas(self):
        r = itens(despesa(id="a", categoria="alimentacao"),
                  despesa(id="b", categoria="transporte_urbano"),
                  despesa(id="c", categoria="hospedagem"))
        self.assertEqual({i["status"] for i in r.values()}, {"aprovado"})


if __name__ == "__main__":
    unittest.main()
