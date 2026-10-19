"""Spec §9.1 — regressão da v3: exemplos/despesas-exemplo.json com a tabela v3 (plan.md DT-009), via CLI real."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "exemplos" / "despesas-exemplo.json"
POLITICA_V3 = RAIZ / "tests" / "dados" / "politica-v3.json"


def rodar_cli(arquivo: Path, *opcoes: str) -> dict:
    with tempfile.TemporaryDirectory() as pasta:
        saida = Path(pasta, "resultado.json")
        proc = subprocess.run(
            [sys.executable, str(RAIZ / "run.py"), "calcular", "--input", str(arquivo), "--output", str(saida),
             *opcoes],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        assert proc.returncode == 0, proc.stderr
        return json.loads(saida.read_text(encoding="utf-8"))


class TestAceiteExemplo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saida = rodar_cli(EXEMPLO, "--politica", str(POLITICA_V3))
        cls.itens = {i["id"]: i for i in cls.saida["itens"]}

    def assertItem(self, id_, status, reembolsavel=None, codigo=None):
        item = self.itens[id_]
        self.assertEqual(item["status"], status, id_)
        if reembolsavel is not None:
            self.assertEqual(item["valor_reembolsavel"], reembolsavel, id_)
        if codigo is not None:
            self.assertEqual([m["codigo"] for m in item["motivos"]], [codigo], id_)

    def test_aceite_d001_parcial_limite_diario(self):
        self.assertItem("d-001", "parcial", "60.00", "LIMITE_DIARIO")

    def test_aceite_d002_recusado_limite_esgotado(self):
        self.assertItem("d-002", "recusado", "0.00", "LIMITE_DIARIO")

    def test_aceite_d003_100_sem_nota_passa_e_limita_em_80(self):
        self.assertItem("d-003", "parcial", "80.00", "LIMITE_DIARIO")

    def test_aceite_d004_100_01_sem_nota_recusado(self):
        self.assertItem("d-004", "recusado", "0.00", "SEM_NOTA_FISCAL")

    def test_aceite_d005_coworking_recusado(self):
        self.assertItem("d-005", "recusado", "0.00", "CATEGORIA_NAO_REEMBOLSAVEL")

    def test_aceite_d006_aprovado(self):
        self.assertItem("d-006", "aprovado", "54.90")

    def test_aceite_d007_duplicata_de_d006(self):
        self.assertItem("d-007", "recusado", "0.00", "DUPLICATA")
        self.assertIn("d-006", self.itens["d-007"]["motivos"][0]["mensagem"])

    def test_aceite_d008_fora_da_competencia(self):
        self.assertItem("d-008", "recusado", "0.00", "FORA_DA_COMPETENCIA")

    def test_aceite_d009_estorno_ignorado(self):
        self.assertItem("d-009", "ignorado", "0.00", "VALOR_NAO_POSITIVO")

    def test_aceite_d010_hospedagem_duas_diarias(self):
        self.assertItem("d-010", "aprovado", "480.00")

    def test_aceite_d011_arredondado_em_viagem(self):
        self.assertItem("d-011", "aprovado", "33.33")
        self.assertEqual(self.itens["d-011"]["valor_informado"], "33.333")

    def test_aceite_d012_sabado_aprovado(self):
        self.assertItem("d-012", "aprovado", "47.20")

    def test_aceite_d013_hospedagem_sem_nota(self):
        self.assertItem("d-013", "recusado", "0.00", "SEM_NOTA_FISCAL")

    def test_aceite_d014_maiusculas_normalizadas_e_limitadas(self):
        self.assertItem("d-014", "parcial", "60.00", "LIMITE_DIARIO")
        self.assertEqual(self.itens["d-014"]["categoria"], "alimentacao")

    def test_aceite_totais(self):
        self.assertEqual(self.saida["totais"], {
            "valor_solicitado": "1861.84", "valor_reembolsavel": "815.43",
            "valor_pendente_aprovacao": "0.00", "valor_glosado": "1046.41",
            "itens_por_status": {"aprovado": 4, "parcial": 3, "recusado": 6, "ignorado": 1,
                                 "pendente_aprovacao": 0}})

    def test_aceite_ordem_e_duas_casas(self):
        self.assertEqual([i["id"] for i in self.saida["itens"]], [f"d-{n:03d}" for n in range(1, 15)])
        for item in self.saida["itens"]:
            for campo in ("valor_considerado", "valor_reembolsavel"):
                self.assertRegex(item[campo], r"^-?\d+\.\d{2}$")

    def test_aceite_execucao_deterministica(self):
        self.assertEqual(rodar_cli(EXEMPLO, "--politica", str(POLITICA_V3)), self.saida)


if __name__ == "__main__":
    unittest.main()
