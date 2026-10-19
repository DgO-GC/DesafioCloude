"""RN-001 — validação da entrada (spec 4.1, 4.3)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reembolso.cli import calcular
from reembolso.entrada import EntradaInvalida
from tests.apoio import despesa, entrada, rodar

RAIZ = Path(__file__).resolve().parent.parent


class TestRN001Validacao(unittest.TestCase):
    def assertInvalida(self, dados, trecho):
        with self.assertRaises(EntradaInvalida) as ctx:
            calcular(json.dumps(dados))
        self.assertIn(trecho, str(ctx.exception))

    def test_rn001_json_malformado_e_invalido(self):
        with self.assertRaises(EntradaInvalida):
            calcular("{ isto não é json")

    def test_rn001_despesa_sem_valor_cita_o_id(self):
        d = despesa(id="x-9")
        del d["valor"]
        self.assertInvalida(entrada(d), "x-9")

    def test_rn001_valor_booleano_e_invalido(self):
        self.assertInvalida(entrada(despesa(id="x-1", valor=True)), "valor")

    def test_rn001_tem_nota_fiscal_obrigatorio(self):
        d = despesa(id="x-2")
        del d["tem_nota_fiscal"]
        self.assertInvalida(entrada(d), "tem_nota_fiscal")

    def test_rn001_data_fora_do_formato(self):
        self.assertInvalida(entrada(despesa(id="x-3", data="03/07/2026")), "x-3")

    def test_rn001_inicio_posterior_ao_fim(self):
        self.assertInvalida(entrada(inicio="2026-08-01", fim="2026-07-31"), "posterior")

    def test_rn001_falta_periodo(self):
        dados = entrada()
        del dados["periodo"]
        self.assertInvalida(dados, "periodo")

    def test_rn001_descricao_e_fornecedor_sao_opcionais(self):
        d = despesa()
        del d["descricao"], d["fornecedor"]
        self.assertEqual(len(rodar(d)["itens"]), 1)

    def test_rn001_lista_vazia_e_valida(self):
        saida = rodar()
        self.assertEqual(saida["itens"], [])
        self.assertEqual(saida["totais"]["valor_reembolsavel"], "0.00")


class TestRN001Cli(unittest.TestCase):
    def _cli(self, conteudo: str):
        with tempfile.TemporaryDirectory() as pasta:
            ent, sai = Path(pasta, "e.json"), Path(pasta, "s.json")
            ent.write_text(conteudo, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(RAIZ / "run.py"), "calcular", "--input", str(ent), "--output", str(sai)],
                capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"})  # Windows: stderr em cp1252 por padrão
            return proc, (sai.read_text(encoding="utf-8") if sai.exists() else None)

    def test_rn001_entrada_invalida_nao_gera_saida_e_termina_com_erro(self):
        proc, saida = self._cli('{"colaborador": {}}')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIsNone(saida)
        self.assertIn("entrada inválida", proc.stderr)

    def test_rn001_entrada_valida_gera_arquivo(self):
        proc, saida = self._cli(json.dumps(entrada(despesa())))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(json.loads(saida)["itens"]), 1)


if __name__ == "__main__":
    unittest.main()
