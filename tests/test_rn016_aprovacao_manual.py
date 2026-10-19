"""RN-016 — aprovação manual acima de R$ 500,00 (AMB-027)."""
import unittest

from tests.apoio import codigos, despesa, itens, rodar


def hosp(valor, descricao, **c):
    return despesa(id="h", categoria="hospedagem", valor=valor, descricao=descricao, **c)


class TestRN016AprovacaoManual(unittest.TestCase):
    def test_rn016_acima_de_500_fica_pendente_com_valor_mantido(self):
        r = itens(hosp(1200, "Hotel Londres - 3 noites"), centro_custo="CC-COMERCIAL")
        self.assertEqual((r["h"]["status"], r["h"]["valor_reembolsavel"]), ("pendente_aprovacao", "1200.00"))
        self.assertEqual(codigos(r["h"]), ["APROVACAO_MANUAL"])
        self.assertEqual(r["h"]["motivos"][0]["regra"], "RN-016")

    def test_rn016_exatamente_500_e_aprovado(self):
        r = itens(hosp(500, "2 diarias"))
        self.assertEqual((r["h"]["status"], codigos(r["h"])), ("aprovado", []))

    def test_rn016_um_centavo_acima_fica_pendente(self):
        self.assertEqual(itens(hosp(500.01, "3 diarias"))["h"]["status"], "pendente_aprovacao")

    def test_rn016_compara_valor_apos_limites(self):
        """1.000,00 sem nº de diárias → limite 400,00 → parcial, não pendente."""
        r = itens(hosp(1000, "Hotel"), centro_custo="CC-COMERCIAL")
        self.assertEqual((r["h"]["status"], r["h"]["valor_reembolsavel"]), ("parcial", "400.00"))

    def test_rn016_pendente_com_glosa_mantem_os_dois_motivos(self):
        r = itens(hosp(1300, "3 noites"), centro_custo="CC-COMERCIAL")
        self.assertEqual(r["h"]["valor_reembolsavel"], "1200.00")
        self.assertEqual(codigos(r["h"]), ["LIMITE_HOSPEDAGEM", "APROVACAO_MANUAL"])

    def test_rn016_item_recusado_nunca_fica_pendente(self):
        r = itens(hosp(1200, "3 noites", tem_nota_fiscal=False), centro_custo="CC-COMERCIAL")
        self.assertEqual(codigos(r["h"]), ["SEM_NOTA_FISCAL"])

    def test_rn016_totais_separam_pendente_do_reembolsavel(self):
        t = rodar(hosp(1200, "3 noites"), despesa(id="a", valor=50), centro_custo="CC-COMERCIAL")["totais"]
        self.assertEqual((t["valor_solicitado"], t["valor_reembolsavel"], t["valor_pendente_aprovacao"],
                          t["valor_glosado"]), ("1250.00", "50.00", "1200.00", "0.00"))
        self.assertEqual(t["itens_por_status"]["pendente_aprovacao"], 1)

    def test_rn016_e_por_item_nao_pelo_total(self):
        r = itens(hosp(400, "2 diarias"), despesa(id="b", categoria="hospedagem", valor=400, descricao="2 noites"))
        self.assertEqual({i["status"] for i in r.values()}, {"aprovado"})


if __name__ == "__main__":
    unittest.main()
