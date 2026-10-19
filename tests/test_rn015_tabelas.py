"""RN-015 — validação das tabelas de política e câmbio (spec 4.3–4.5)."""
import copy
import json
import unittest

from reembolso.cli import calcular
from reembolso.entrada import EntradaInvalida
from tests.apoio import despesa, entrada, politica, rodar


def calcular_com(pol: dict):
    return calcular(json.dumps(entrada(despesa())), json.dumps(pol))


class TestRN015Politica(unittest.TestCase):
    def assertInvalida(self, pol, trecho):
        with self.assertRaises(EntradaInvalida) as ctx:
            calcular_com(pol)
        self.assertIn("tabela de política", str(ctx.exception))
        self.assertIn(trecho, str(ctx.exception))

    def test_rn015_tabela_valida_e_aceita_e_versao_vai_para_a_saida(self):
        self.assertEqual(rodar(despesa(), politica=politica(versao="v9"))["politica"], "v9")

    def test_rn015_tabela_vigente_padrao_e_v4(self):
        self.assertEqual(rodar(despesa())["politica"], "v4")

    def test_rn015_periodicidade_desconhecida_e_invalida(self):
        pol = politica()
        pol["padrao"]["alimentacao"]["periodicidade"] = "semana"
        self.assertInvalida(pol, "periodicidade")

    def test_rn015_limite_negativo_e_invalido(self):
        pol = politica()
        pol["padrao"]["alimentacao"]["limite"] = -10
        self.assertInvalida(pol, "alimentacao.limite")

    def test_rn015_limite_nao_numerico_e_invalido(self):
        pol = politica()
        pol["padrao"]["hospedagem"]["limite"] = "250"
        self.assertInvalida(pol, "hospedagem.limite")

    def test_rn015_moeda_base_diferente_de_brl_e_invalida(self):
        self.assertInvalida(politica(moeda_base="USD"), "moeda_base")

    def test_rn015_falta_limiar_de_nota_e_invalido(self):
        pol = politica()
        del pol["nota_fiscal_obrigatoria_acima_de"]
        self.assertInvalida(pol, "nota_fiscal")

    def test_rn015_falta_padrao_e_invalido(self):
        pol = politica()
        del pol["padrao"]
        self.assertInvalida(pol, "padrao")

    def test_rn015_centro_de_custo_invalido_e_invalido(self):
        self.assertInvalida(politica(centros_custo={"CC-X": {"alimentacao": {"limite": 1}}}), "CC-X")

    def test_rn015_observacao_e_ignorada(self):
        pol = politica()
        pol["padrao"]["hospedagem"]["observacao"] = "qualquer texto"
        self.assertEqual(len(calcular_com(copy.deepcopy(pol))["itens"]), 1)


if __name__ == "__main__":
    unittest.main()
