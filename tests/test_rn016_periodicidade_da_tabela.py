"""RN-008..RN-011 com números da tabela (T-016; AMB-025). Prova que nada da v3 ficou fixo no código."""
import unittest

from tests.apoio import codigos, despesa, itens, politica


def hotel(data="2026-07-14", **c):
    base = dict(id="h", data=data, categoria="hospedagem", valor=200, descricao="1 diaria")
    base.update(c)
    return despesa(**base)


class TestLimitesDaTabela(unittest.TestCase):
    def test_rn010_categoria_nova_com_periodicidade_diaria_e_limitada_por_diaria(self):
        pol = politica()
        pol["padrao"]["aluguel_carro"] = {"limite": 100, "periodicidade": "diaria"}
        r = itens(despesa(id="c", categoria="aluguel_carro", valor=350, descricao="3 diarias"), politica=pol)
        self.assertEqual((r["c"]["valor_reembolsavel"], codigos(r["c"])), ("300.00", ["LIMITE_HOSPEDAGEM"]))

    def test_rn009_categoria_nova_com_periodicidade_dia_agrega_o_dia(self):
        pol = politica()
        pol["padrao"]["estacionamento"] = {"limite": 30, "periodicidade": "dia"}
        r = itens(despesa(id="a", categoria="estacionamento", valor=20),
                  despesa(id="b", categoria="estacionamento", valor=20), politica=pol)
        self.assertEqual(r["b"]["valor_reembolsavel"], "10.00")

    def test_rn009_hospedagem_com_periodicidade_dia_passa_a_agregar(self):
        pol = politica()
        pol["padrao"]["hospedagem"] = {"limite": 250, "periodicidade": "dia"}
        r = itens(hotel(id="a", fornecedor="A"), hotel(id="b", fornecedor="B"), politica=pol)
        # A própria hospedagem faz de 14/07 dia em viagem e, sendo 'dia', ganha +50% (AMB-025): 375 − 200.
        self.assertEqual(r["b"]["valor_reembolsavel"], "175.00")

    def test_rn008_limiar_de_nota_vem_da_tabela(self):
        r = itens(despesa(id="a", valor=55, tem_nota_fiscal=False),
                  politica=politica(nota_fiscal_obrigatoria_acima_de=50))
        self.assertEqual(codigos(r["a"]), ["SEM_NOTA_FISCAL"])

    def test_rn011_percentual_de_acrescimo_vem_da_tabela(self):
        r = itens(hotel(), despesa(id="a", data="2026-07-14", valor=130),
                  politica=politica(acrescimo_em_viagem_percentual=100))
        self.assertEqual(r["a"]["valor_reembolsavel"], "120.00")
        self.assertIn("+100%", r["a"]["motivos"][0]["mensagem"])

    def test_rn011_acrescimo_vale_para_representacao_em_viagem(self):
        """AMB-025: representação é 'dia' → 300 × 1,5 = 450 em viagem."""
        r = itens(hotel(valor=300), despesa(id="r", data="2026-07-14", categoria="representacao", valor=440),
                  centro_custo="CC-COMERCIAL")
        self.assertEqual(r["r"]["status"], "aprovado")

    def test_rn011_acrescimo_sobre_limite_do_cc_arredonda_em_centavos(self):
        """CC-ENG-PLATAFORMA: 75 × 1,5 = 112,50. Hospedagem bloqueada ainda caracteriza viagem."""
        r = itens(hotel(), despesa(id="a", data="2026-07-14", valor=120), centro_custo="CC-ENG-PLATAFORMA")
        self.assertEqual(codigos(r["h"]), ["CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO"])
        self.assertEqual(r["a"]["valor_reembolsavel"], "112.50")

    def test_rn011_acrescimo_nao_vale_para_periodicidade_diaria(self):
        r = itens(hotel(valor=300), politica=politica(acrescimo_em_viagem_percentual=100))
        self.assertEqual(r["h"]["valor_reembolsavel"], "250.00")


if __name__ == "__main__":
    unittest.main()
