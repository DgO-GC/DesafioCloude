"""Spec §9.2–9.5 — aceite com as tabelas vigentes (politicas/), via CLI real."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_aceite_exemplo import EXEMPLO, RAIZ, rodar_cli

ENVELOPE = RAIZ / "exemplos" / "envelope"


class AceiteBase(unittest.TestCase):
    ARQUIVO = None

    @classmethod
    def setUpClass(cls):
        cls.saida = rodar_cli(cls.ARQUIVO)
        cls.itens = {i["id"]: i for i in cls.saida["itens"]}

    def assertItem(self, id_, status, reembolsavel=None, codigo=None):
        item = self.itens[id_]
        self.assertEqual(item["status"], status, id_)
        if reembolsavel is not None:
            self.assertEqual(item["valor_reembolsavel"], reembolsavel, id_)
        if codigo is not None:
            self.assertIn(codigo, [m["codigo"] for m in item["motivos"]], id_)

    def assertTotais(self, solicitado, reembolsavel, pendente, glosado, **status):
        t = self.saida["totais"]
        self.assertEqual((t["valor_solicitado"], t["valor_reembolsavel"], t["valor_pendente_aprovacao"],
                          t["valor_glosado"]), (solicitado, reembolsavel, pendente, glosado))
        for s, n in status.items():
            self.assertEqual(t["itens_por_status"][s], n, s)


class TestAceite92ExemploComV4(AceiteBase):
    """CC-ENG-PLATAFORMA: alimentação 75, transporte 80, hospedagem 0."""
    ARQUIVO = EXEMPLO

    def test_aceite_92_tabela(self):
        self.assertEqual((self.saida["politica"], self.saida["tabela_de_limites"]), ("v4", "CC-ENG-PLATAFORMA"))

    def test_aceite_92_d001_d002_saldo_de_75(self):
        self.assertItem("d-001", "aprovado", "72.50")
        self.assertItem("d-002", "parcial", "2.50", "LIMITE_DIARIO")

    def test_aceite_92_d003_d004(self):
        self.assertItem("d-003", "parcial", "80.00", "LIMITE_DIARIO")
        self.assertItem("d-004", "recusado", "0.00", "SEM_NOTA_FISCAL")

    def test_aceite_92_hospedagem_bloqueada(self):
        self.assertItem("d-010", "recusado", "0.00", "CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO")
        self.assertItem("d-013", "recusado", "0.00", "CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO")

    def test_aceite_92_d011_viagem_pela_hospedagem_recusada(self):
        self.assertItem("d-011", "aprovado", "33.33")

    def test_aceite_92_d014(self):
        self.assertItem("d-014", "aprovado", "61.00")

    def test_aceite_92_totais(self):
        self.assertTotais("1861.84", "351.43", "0.00", "1510.41",
                          aprovado=5, parcial=2, recusado=6, ignorado=1, pendente_aprovacao=0)


class TestAceite93Envelope(AceiteBase):
    """CC-COMERCIAL com despesas em EUR, USD e GBP."""
    ARQUIVO = ENVELOPE / "despesas-envelope.json"

    def test_aceite_93_tabela(self):
        self.assertEqual(self.saida["tabela_de_limites"], "CC-COMERCIAL")

    def test_aceite_93_e001_representacao_fora_de_viagem(self):
        self.assertItem("e-001", "parcial", "300.00", "LIMITE_DIARIO")

    def test_aceite_93_e002_eur_em_viagem(self):
        self.assertItem("e-002", "aprovado", "130.46")
        self.assertEqual(self.itens["e-002"]["taxa_cambio"], "5.93")

    def test_aceite_93_e003_sem_nota_abaixo_de_100_brl(self):
        self.assertItem("e-003", "aprovado", "85.26")

    def test_aceite_93_e004_sabado_cotacao_de_sexta(self):
        self.assertItem("e-004", "parcial", "135.00", "LIMITE_DIARIO")
        self.assertEqual((self.itens["e-004"]["data_cotacao"], self.itens["e-004"]["valor_considerado"]),
                         ("2026-07-17", "178.80"))

    def test_aceite_93_e005_usd_sem_nota_acima_de_100_brl(self):
        self.assertItem("e-005", "recusado", "0.00", "SEM_NOTA_FISCAL")

    def test_aceite_93_e006_gbp_sem_cotacao(self):
        self.assertItem("e-006", "recusado", "0.00", "MOEDA_SEM_COTACAO")

    def test_aceite_93_e007_pendente_de_aprovacao(self):
        self.assertItem("e-007", "pendente_aprovacao", "1200.00", "APROVACAO_MANUAL")

    def test_aceite_93_e008_coberto_pela_hospedagem(self):
        self.assertItem("e-008", "aprovado", "95.00")

    def test_aceite_93_e009_coworking(self):
        self.assertItem("e-009", "recusado", "0.00", "CATEGORIA_NAO_REEMBOLSAVEL")

    def test_aceite_93_e010_sem_moeda_e_brl(self):
        self.assertItem("e-010", "aprovado", "88.00")
        self.assertEqual(self.itens["e-010"]["moeda"], "BRL")

    def test_aceite_93_totais(self):
        self.assertTotais("2457.52", "833.72", "1200.00", "423.80",
                          aprovado=4, parcial=2, recusado=3, ignorado=0, pendente_aprovacao=1)


class TestAceite94CentroDeCustoDesconhecido(AceiteBase):
    ARQUIVO = ENVELOPE / "despesas-envelope-cc-desconhecido.json"

    def test_aceite_94_usa_padrao(self):
        self.assertEqual(self.saida["tabela_de_limites"], "padrao")

    def test_aceite_94_itens(self):
        self.assertItem("f-001", "aprovado", "58.00")
        self.assertItem("f-002", "parcial", "250.00", "LIMITE_HOSPEDAGEM")
        self.assertItem("f-003", "recusado", "0.00", "CATEGORIA_NAO_REEMBOLSAVEL")
        self.assertItem("f-004", "aprovado", "65.76")

    def test_aceite_94_totais(self):
        self.assertTotais("623.76", "373.76", "0.00", "250.00")


class TestAceite95TabelaInvalida(unittest.TestCase):
    def test_aceite_95_tabela_invalida_nao_gera_saida(self):
        with tempfile.TemporaryDirectory() as pasta:
            ruim, saida = Path(pasta, "pol.json"), Path(pasta, "s.json")
            ruim.write_text('{"versao": "x", "moeda_base": "USD"}', encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(RAIZ / "run.py"), "calcular", "--input", str(EXEMPLO),
                 "--output", str(saida), "--politica", str(ruim)],
                capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(saida.exists())
            self.assertIn("tabela de política", proc.stderr)

    def test_aceite_95_roda_de_outra_pasta(self):
        """Tabelas padrão são achadas a partir do pacote, não do diretório atual (plan.md §7)."""
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta, "s.json")
            proc = subprocess.run(
                [sys.executable, str(RAIZ / "run.py"), "calcular", "--input", str(EXEMPLO), "--output", str(saida)],
                cwd=pasta, capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
