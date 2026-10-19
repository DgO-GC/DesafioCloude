"""RN-004 — período de competência inclusivo (AMB-008)."""
import unittest

from tests.apoio import codigos, despesa, itens


class TestRN004Competencia(unittest.TestCase):
    def test_rn004_ultimo_dia_do_periodo_e_avaliado(self):
        self.assertEqual(itens(despesa(id="a", data="2026-07-31"))["a"]["status"], "aprovado")

    def test_rn004_primeiro_dia_do_periodo_e_avaliado(self):
        self.assertEqual(itens(despesa(id="a", data="2026-07-01"))["a"]["status"], "aprovado")

    def test_rn004_mes_anterior_lancado_com_atraso_e_recusado(self):
        item = itens(despesa(id="a", data="2026-04-15", valor=41))["a"]
        self.assertEqual(item["status"], "recusado")
        self.assertEqual(item["valor_reembolsavel"], "0.00")
        self.assertEqual(codigos(item), ["FORA_DA_COMPETENCIA"])

    def test_rn004_dia_seguinte_ao_fim_e_recusado(self):
        self.assertEqual(codigos(itens(despesa(id="a", data="2026-08-01"))["a"]), ["FORA_DA_COMPETENCIA"])

    def test_rn004_competencia_vem_antes_da_categoria(self):
        item = itens(despesa(id="a", data="2026-06-30", categoria="coworking"))["a"]
        self.assertEqual(codigos(item), ["FORA_DA_COMPETENCIA"])


if __name__ == "__main__":
    unittest.main()
