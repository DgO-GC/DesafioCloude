"""RN-008 — nota fiscal obrigatória acima de R$ 100,00 (AMB-004)."""
import unittest

from tests.apoio import codigos, despesa, itens


class TestRN008NotaFiscal(unittest.TestCase):
    def test_rn008_exatamente_100_sem_nota_e_aceito(self):
        item = itens(despesa(id="a", categoria="hospedagem", valor=100.00, tem_nota_fiscal=False))["a"]
        self.assertNotIn("SEM_NOTA_FISCAL", codigos(item))
        self.assertEqual(item["status"], "aprovado")

    def test_rn008_um_centavo_acima_sem_nota_e_recusado(self):
        item = itens(despesa(id="a", categoria="transporte_urbano", valor=100.01, tem_nota_fiscal=False))["a"]
        self.assertEqual(item["status"], "recusado")
        self.assertEqual(codigos(item), ["SEM_NOTA_FISCAL"])

    def test_rn008_sem_nota_recusa_integralmente_nao_paga_ate_100(self):
        item = itens(despesa(id="a", categoria="hospedagem", valor=690, tem_nota_fiscal=False))["a"]
        self.assertEqual(item["valor_reembolsavel"], "0.00")

    def test_rn008_com_nota_acima_de_100_segue(self):
        item = itens(despesa(id="a", categoria="hospedagem", valor=200, tem_nota_fiscal=True))["a"]
        self.assertEqual(item["status"], "aprovado")

    def test_rn008_compara_valor_arredondado(self):
        """100.004 arredonda para 100.00 (RN-002) e portanto não exige nota."""
        item = itens(despesa(id="a", categoria="hospedagem", valor=100.004, tem_nota_fiscal=False))["a"]
        self.assertNotIn("SEM_NOTA_FISCAL", codigos(item))

    def test_rn008_duplicata_sem_nota_e_recusada_como_duplicata(self):
        """Seção 8: duplicata vem antes de nota fiscal."""
        d = dict(categoria="hospedagem", fornecedor="Hotel", valor=150, tem_nota_fiscal=False)
        r = itens(despesa(id="a", **d), despesa(id="b", **d))
        self.assertEqual(codigos(r["a"]), ["SEM_NOTA_FISCAL"])
        self.assertEqual(codigos(r["b"]), ["DUPLICATA"])


if __name__ == "__main__":
    unittest.main()
