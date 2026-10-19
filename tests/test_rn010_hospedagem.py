"""RN-010 — limite de hospedagem por diária (AMB-006)."""
import unittest

from reembolso.regras import diarias
from tests.apoio import codigos, despesa, itens


def hosp(id_, valor, descricao, **campos):
    return despesa(id=id_, categoria="hospedagem", valor=valor, descricao=descricao, **campos)


class TestRN010Hospedagem(unittest.TestCase):
    def test_rn010_duas_diarias_tem_limite_500(self):
        r = itens(hosp("a", 480, "Hotel Rio - 2 diarias"))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("aprovado", "480.00"))

    def test_rn010_sem_numero_de_diarias_conta_uma(self):
        r = itens(hosp("a", 310, "Pousada"))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "250.00"))
        self.assertEqual(codigos(r["a"]), ["LIMITE_HOSPEDAGEM"])

    def test_rn010_noites_com_nota_dentro_do_limite(self):
        r = itens(hosp("a", 690, "Airbnb 3 noites"))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn010_acima_do_limite_de_varias_diarias_e_parcial(self):
        r = itens(hosp("a", 800, "Hotel - 3 noites"))
        self.assertEqual(r["a"]["valor_reembolsavel"], "750.00")

    def test_rn010_extracao_de_diarias(self):
        self.assertEqual(diarias("Hotel Rio - 2 diarias"), 2)
        self.assertEqual(diarias("Airbnb 3 noites"), 3)
        self.assertEqual(diarias("Pousada - 1 diária"), 1)
        self.assertEqual(diarias("HOTEL 4 DIÁRIAS"), 4)
        self.assertEqual(diarias("1 noite"), 1)
        self.assertEqual(diarias("Hotel 5 estrelas, 2 noites"), 2)
        self.assertEqual(diarias("0 diarias"), 1)
        self.assertEqual(diarias(""), 1)

    def test_rn010_hospedagens_no_mesmo_dia_nao_agregam(self):
        r = itens(hosp("a", 250, "Hotel A", fornecedor="A"), hosp("b", 250, "Hotel B", fornecedor="B"))
        self.assertEqual({i["status"] for i in r.values()}, {"aprovado"})


if __name__ == "__main__":
    unittest.main()
