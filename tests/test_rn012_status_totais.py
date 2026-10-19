"""RN-012 — status, motivos, totais; seção 8 (AMB-015) e formato da seção 4.2."""
import json
import unittest

from reembolso.cli import calcular
from tests.apoio import despesa, entrada, rodar


class TestRN012StatusTotais(unittest.TestCase):
    def test_rn012_exemplo_literal_da_secao_4_2(self):
        # Texto JSON literal: json.dumps(38.00) geraria "38.0" e mudaria valor_informado.
        saida = calcular("""{
            "colaborador": {"id": "c-1"},
            "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
            "despesas": [
                {"id": "a-1", "data": "2026-07-03", "categoria": "alimentacao", "valor": 72.50, "tem_nota_fiscal": true},
                {"id": "a-2", "data": "2026-07-03", "categoria": "alimentacao", "valor": 38.00, "tem_nota_fiscal": true}
            ]}""")
        self.assertEqual(saida["versao_schema"], "1.0")
        self.assertEqual(saida["politica"], "v3")
        self.assertEqual(saida["colaborador"], {"id": "c-1"})
        self.assertEqual(saida["totais"], {
            "valor_solicitado": "110.50", "valor_reembolsavel": "60.00", "valor_glosado": "50.50",
            "itens_por_status": {"aprovado": 0, "parcial": 1, "recusado": 1, "ignorado": 0}})
        self.assertEqual(saida["itens"][1], {
            "id": "a-2", "data": "2026-07-03", "categoria": "alimentacao",
            "valor_informado": "38.00", "valor_considerado": "38.00", "valor_reembolsavel": "0.00",
            "status": "recusado",
            "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009",
                         "mensagem": "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 0.00. Glosados R$ 38.00."}]})

    def test_rn012_itens_saem_na_ordem_da_entrada(self):
        ids = [i["id"] for i in rodar(despesa(id="z"), despesa(id="a"), despesa(id="m"))["itens"]]
        self.assertEqual(ids, ["z", "a", "m"])

    def test_rn012_contagem_tem_sempre_os_quatro_status(self):
        self.assertEqual(rodar()["totais"]["itens_por_status"],
                         {"aprovado": 0, "parcial": 0, "recusado": 0, "ignorado": 0})

    def test_rn012_encerrada_tem_motivo_unico(self):
        """Fora do período, categoria inválida, sem nota: só o primeiro motivo da seção 8."""
        item = rodar(despesa(data="2026-04-01", categoria="coworking", valor=500, tem_nota_fiscal=False))["itens"][0]
        self.assertEqual([m["codigo"] for m in item["motivos"]], ["FORA_DA_COMPETENCIA"])

    def test_rn012_aprovado_sem_ressalva_tem_motivos_vazio(self):
        self.assertEqual(rodar(despesa(valor=10))["itens"][0]["motivos"], [])

    def test_rn012_glosado_e_solicitado_menos_reembolsavel(self):
        t = rodar(despesa(valor=70), despesa(categoria="coworking", valor=20), despesa(valor=-5))["totais"]
        self.assertEqual((t["valor_solicitado"], t["valor_reembolsavel"], t["valor_glosado"]),
                         ("90.00", "60.00", "30.00"))

    def test_rn012_mesma_entrada_mesma_saida(self):
        texto = json.dumps(entrada(despesa(id="a", valor=72.5), despesa(id="b", valor=38)))
        self.assertEqual(calcular(texto), calcular(texto))


if __name__ == "__main__":
    unittest.main()
