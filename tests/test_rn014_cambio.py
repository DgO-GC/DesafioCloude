"""RN-014 — moeda e conversão para BRL (AMB-020, AMB-021, AMB-022, AMB-023, AMB-028, AMB-029).

Usa a tabela de câmbio vigente (politicas/cambio.json): cotações de 13/07 a 28/07/2026, só dias úteis.
"""
import unittest
from datetime import date
from decimal import Decimal

from reembolso.cambio import carregar_cambio
from tests.apoio import codigos, despesa, itens, rodar


def em(moeda, valor, data, **c):
    base = dict(id="x", data=data, categoria="alimentacao", valor=valor, moeda=moeda)
    base.update(c)
    return despesa(**base)


class TestRN014Conversao(unittest.TestCase):
    def test_rn014_eur_usa_a_cotacao_da_data(self):
        item = itens(em("EUR", 22.00, "2026-07-14"), centro_custo="CC-COMERCIAL")["x"]
        self.assertEqual((item["moeda"], item["taxa_cambio"], item["data_cotacao"]), ("EUR", "5.93", "2026-07-14"))
        self.assertEqual(item["valor_considerado"], "130.46")

    def test_rn014_sabado_usa_a_cotacao_anterior(self):
        """AMB-020: 18/07 é sábado → cotação de sexta 17/07 (5,96)."""
        item = itens(em("EUR", 30.00, "2026-07-18"))["x"]
        self.assertEqual((item["data_cotacao"], item["valor_considerado"]), ("2026-07-17", "178.80"))

    def test_rn014_domingo_tambem_volta_para_sexta(self):
        self.assertEqual(itens(em("USD", 10, "2026-07-19"))["x"]["data_cotacao"], "2026-07-17")

    def test_rn014_moeda_sem_cotacao_e_recusada(self):
        """AMB-021: GBP não está na tabela."""
        item = itens(em("GBP", 55.00, "2026-07-21"))["x"]
        self.assertEqual((item["status"], codigos(item)), ("recusado", ["MOEDA_SEM_COTACAO"]))
        self.assertIsNone(item["valor_considerado"])
        self.assertIsNone(item["taxa_cambio"])

    def test_rn014_cotacao_mais_velha_que_7_dias_nao_vale(self):
        self.assertEqual(codigos(itens(em("USD", 10, "2026-07-05"))["x"]), ["MOEDA_SEM_COTACAO"])

    def test_rn014_janela_de_7_dias_e_inclusiva(self):
        """28/07 é a última cotação; 04/08 está a exatamente 7 dias."""
        r = itens(em("USD", 10, "2026-08-04"), inicio="2026-08-01", fim="2026-08-31")
        self.assertEqual(r["x"]["data_cotacao"], "2026-07-28")
        r = itens(em("USD", 10, "2026-08-05"), inicio="2026-08-01", fim="2026-08-31")
        self.assertEqual(codigos(r["x"]), ["MOEDA_SEM_COTACAO"])

    def test_rn014_arredonda_so_o_produto(self):
        """AMB-022: 10,005 USD × 5,42 = 54,2271 → 54,23 (arredondar antes daria 10,01 × 5,42 = 54,25)."""
        self.assertEqual(itens(em("USD", 10.005, "2026-07-13"))["x"]["valor_considerado"], "54.23")

    def test_rn014_moeda_ausente_ou_vazia_e_brl(self):
        """AMB-029."""
        r = itens(despesa(id="a", valor=10), despesa(id="b", valor=10, moeda=""), despesa(id="c", valor=10, moeda=None))
        self.assertEqual({i["moeda"] for i in r.values()}, {"BRL"})
        self.assertEqual({i["taxa_cambio"] for i in r.values()}, {None})

    def test_rn014_moeda_normalizada(self):
        self.assertEqual(itens(em(" eur ", 10, "2026-07-14"))["x"]["moeda"], "EUR")

    def test_rn014_brl_explicito_nao_converte(self):
        item = itens(em("BRL", 95.00, "2026-07-23"))["x"]
        self.assertEqual((item["valor_considerado"], item["taxa_cambio"]), ("95.00", None))

    def test_rn008_nota_fiscal_compara_valor_convertido(self):
        """AMB-023: 14,50 EUR = 85,26 BRL sem nota → aceito; 40 USD = 220 BRL sem nota → recusado."""
        r = itens(em("EUR", 14.50, "2026-07-15", id="a", tem_nota_fiscal=False),
                  em("USD", 40.00, "2026-07-20", id="b", categoria="transporte_urbano", tem_nota_fiscal=False))
        self.assertEqual(r["a"]["valor_considerado"], "85.26")
        self.assertNotIn("SEM_NOTA_FISCAL", codigos(r["a"]))
        self.assertEqual(codigos(r["b"]), ["SEM_NOTA_FISCAL"])

    def test_rn007_moeda_diferente_nao_e_duplicata(self):
        """AMB-028."""
        r = itens(em("EUR", 30, "2026-07-14", id="a", fornecedor="F"), em("USD", 30, "2026-07-14", id="b", fornecedor="F"))
        self.assertNotIn("DUPLICATA", codigos(r["b"]))

    def test_rn007_duplicata_em_moeda_estrangeira(self):
        r = itens(em("EUR", 30, "2026-07-14", id="a", fornecedor="F"), em("EUR", 30, "2026-07-14", id="b", fornecedor="F"))
        self.assertEqual(codigos(r["b"]), ["DUPLICATA"])

    def test_rn014_duplicata_vem_antes_da_falta_de_cotacao(self):
        r = itens(em("GBP", 5, "2026-07-14", id="a", fornecedor="F"), em("GBP", 5, "2026-07-14", id="b", fornecedor="F"))
        self.assertEqual((codigos(r["a"]), codigos(r["b"])), (["MOEDA_SEM_COTACAO"], ["DUPLICATA"]))

    def test_rn014_item_recusado_antes_mostra_valor_convertido(self):
        item = itens(em("EUR", 10, "2026-07-14", categoria="coworking"))["x"]
        self.assertEqual((codigos(item), item["valor_considerado"]), (["CATEGORIA_NAO_REEMBOLSAVEL"], "59.30"))

    def test_rn014_sem_cotacao_nao_entra_no_solicitado(self):
        t = rodar(em("GBP", 55, "2026-07-21", id="a"), despesa(id="b", valor=10))["totais"]
        self.assertEqual(t["valor_solicitado"], "10.00")

    def test_rn014_tabela_de_cambio_alternativa(self):
        cambio = {"moeda_base": "BRL", "taxas": {"2026-07-10": {"GBP": 7.00}}}
        item = itens(em("GBP", 10, "2026-07-10"), cambio=cambio)["x"]
        self.assertEqual(item["valor_considerado"], "70.00")


class TestCotacao(unittest.TestCase):
    def test_cotacao_le_taxas_como_decimal(self):
        c = carregar_cambio({"moeda_base": "BRL", "taxas": {"2026-07-13": {"USD": Decimal("5.42")}}})
        self.assertEqual(c.cotacao("USD", date(2026, 7, 13)), (Decimal("5.42"), date(2026, 7, 13)))


if __name__ == "__main__":
    unittest.main()
