"""RN-011 — dias em viagem ampliam limites diários em 50% (AMB-005, AMB-013)."""
import unittest

from tests.apoio import codigos, despesa, itens


def hotel(data="2026-07-14", descricao="Hotel Rio - 2 diarias", **campos):
    base = dict(id="h", data=data, categoria="hospedagem", valor=480, descricao=descricao)
    base.update(campos)
    return despesa(**base)


def alim(id_, data, valor):
    return despesa(id=id_, data=data, categoria="alimentacao", valor=valor)


class TestRN011Viagem(unittest.TestCase):
    def test_rn011_dia_coberto_pela_hospedagem_amplia_alimentacao_para_90(self):
        r = itens(hotel(), alim("a", "2026-07-15", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_limite_ampliado_e_90_e_glosa_o_excedente(self):
        r = itens(hotel(), alim("a", "2026-07-15", 95))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "90.00"))
        self.assertIn("em viagem", r["a"]["motivos"][0]["mensagem"])

    def test_rn011_transporte_em_viagem_vai_para_120(self):
        r = itens(hotel(), despesa(id="t", data="2026-07-14", categoria="transporte_urbano", valor=130))
        self.assertEqual(r["t"]["valor_reembolsavel"], "120.00")

    def test_rn011_dia_do_checkout_ainda_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-16", 85))
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_dia_seguinte_ao_checkout_nao_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-17", 85))
        self.assertEqual((r["a"]["status"], r["a"]["valor_reembolsavel"]), ("parcial", "60.00"))

    def test_rn011_dia_anterior_ao_checkin_nao_e_viagem(self):
        r = itens(hotel(), alim("a", "2026-07-13", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_hospedagem_recusada_por_nota_ainda_caracteriza_viagem(self):
        r = itens(hotel(data="2026-07-22", descricao="Airbnb 3 noites", valor=690, tem_nota_fiscal=False),
                  alim("a", "2026-07-24", 85))
        self.assertEqual(codigos(r["h"]), ["SEM_NOTA_FISCAL"])
        self.assertEqual(r["a"]["status"], "aprovado")

    def test_rn011_hospedagem_fora_do_periodo_nao_caracteriza_viagem(self):
        r = itens(hotel(data="2026-06-30", descricao="3 noites"), alim("a", "2026-07-01", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")

    def test_rn011_hospedagem_nao_tem_limite_ampliado(self):
        r = itens(hotel(descricao="Pousada", valor=300))
        self.assertEqual(r["h"]["valor_reembolsavel"], "250.00")

    def test_rn011_sem_hospedagem_nao_ha_viagem(self):
        r = itens(alim("a", "2026-07-15", 85))
        self.assertEqual(r["a"]["valor_reembolsavel"], "60.00")


if __name__ == "__main__":
    unittest.main()
