"""RN-009 — limite diário com saldo compartilhado (AMB-001, AMB-002, AMB-003, AMB-014)."""
import unittest

from tests.apoio import codigos, despesa, itens

DIA = "2026-07-03"


def alim(id_, valor, **campos):
    return despesa(id=id_, data=campos.pop("data", DIA), categoria="alimentacao", valor=valor, **campos)


def transp(id_, valor, **campos):
    return despesa(id=id_, data=campos.pop("data", DIA), categoria="transporte_urbano", valor=valor, **campos)


class TestRN009LimiteDiario(unittest.TestCase):
    def test_rn009_duas_refeicoes_no_mesmo_dia_dividem_o_limite(self):
        r = itens(alim("d-001", 72.50), alim("d-002", 38.00))
        self.assertEqual((r["d-001"]["status"], r["d-001"]["valor_reembolsavel"]), ("parcial", "60.00"))
        self.assertEqual((r["d-002"]["status"], r["d-002"]["valor_reembolsavel"]), ("recusado", "0.00"))
        self.assertEqual(codigos(r["d-002"]), ["LIMITE_DIARIO"])

    def test_rn009_mensagem_do_exemplo_da_spec(self):
        r = itens(alim("a", 72.50))
        self.assertEqual(r["a"]["motivos"][0]["mensagem"],
                         "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 60.00. Glosados R$ 12.50.")

    def test_rn009_ordem_da_entrada_define_quem_e_cortado(self):
        r = itens(alim("a", 30), alim("b", 40))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("aprovado", "30.00"))
        self.assertEqual((r["b"]["status"], r["b"]["valor_reembolsavel"]), ("parcial", "30.00"))

    def test_rn009_excedente_e_glosado_nao_recusa_item(self):
        r = itens(alim("a", 61.00))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "60.00"))

    def test_rn009_exatamente_no_limite_e_aprovado(self):
        r = itens(alim("a", 60.00))
        self.assertEqual((r["a"]["status"], codigos(r["a"])), ("aprovado", []))

    def test_rn009_transporte_limite_80(self):
        r = itens(transp("a", 100.00, tem_nota_fiscal=False))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "80.00"))

    def test_rn009_dias_diferentes_tem_limites_independentes(self):
        r = itens(alim("a", 60), alim("b", 60, data="2026-07-04"))
        self.assertEqual({i["status"] for i in r.values()}, {"aprovado"})

    def test_rn009_categorias_tem_limites_independentes(self):
        r = itens(alim("a", 60), transp("b", 80))
        self.assertEqual({i["status"] for i in r.values()}, {"aprovado"})

    def test_rn009_despesa_recusada_por_nota_nao_consome_saldo(self):
        r = itens(transp("a", 100.01, tem_nota_fiscal=False), transp("b", 80))
        self.assertEqual(codigos(r["a"]), ["SEM_NOTA_FISCAL"])
        self.assertEqual(r["b"]["status"], "aprovado")

    def test_rn009_estorno_nao_consome_nem_devolve_saldo(self):
        r = itens(transp("a", -45.00, tem_nota_fiscal=False), transp("b", 80), transp("c", 10))
        self.assertEqual(r["b"]["status"], "aprovado")
        self.assertEqual(r["c"]["valor_reembolsavel"], "0.00")

    def test_rn009_sabado_nao_tem_regra_especial(self):
        """AMB-014: 18/07/2026 é sábado."""
        r = itens(alim("a", 47.20, data="2026-07-18"))
        self.assertEqual(r["a"]["status"], "aprovado")


if __name__ == "__main__":
    unittest.main()
