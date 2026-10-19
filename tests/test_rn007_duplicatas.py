"""RN-007 — duplicatas (AMB-007)."""
import unittest

from tests.apoio import codigos, despesa, itens


def almoco(id_, **campos):
    base = dict(id=id_, data="2026-07-09", categoria="alimentacao", fornecedor="Bistro Central", valor=54.90)
    base.update(campos)
    return despesa(**base)


class TestRN007Duplicatas(unittest.TestCase):
    def test_rn007_segunda_ocorrencia_e_recusada_citando_a_primeira(self):
        r = itens(almoco("d-006"), almoco("d-007"))
        self.assertEqual(r["d-006"]["status"], "aprovado")
        self.assertEqual(r["d-007"]["status"], "recusado")
        self.assertEqual(codigos(r["d-007"]), ["DUPLICATA"])
        self.assertIn("d-006", r["d-007"]["motivos"][0]["mensagem"])

    def test_rn007_terceira_copia_tambem_cita_a_primeira(self):
        r = itens(almoco("a"), almoco("b"), almoco("c"))
        self.assertIn("despesa a ", r["c"]["motivos"][0]["mensagem"])

    def test_rn007_um_centavo_de_diferenca_nao_e_duplicata(self):
        r = itens(almoco("a", valor=24.90), almoco("b", valor=24.91))
        self.assertEqual(codigos(r["b"]), [])

    def test_rn007_data_diferente_nao_e_duplicata(self):
        r = itens(almoco("a", valor=20), almoco("b", valor=20, data="2026-07-10"))
        self.assertEqual(codigos(r["b"]), [])

    def test_rn007_fornecedor_compara_sem_caixa_e_espacos(self):
        r = itens(almoco("a"), almoco("b", fornecedor=" BISTRO central "))
        self.assertEqual(codigos(r["b"]), ["DUPLICATA"])

    def test_rn007_descricao_diferente_ainda_e_duplicata(self):
        r = itens(almoco("a", descricao="Almoco"), almoco("b", descricao="Almoço equipe"))
        self.assertEqual(codigos(r["b"]), ["DUPLICATA"])

    def test_rn007_duplicata_fora_do_periodo_recusa_ambas_por_competencia(self):
        r = itens(almoco("a", data="2026-04-15"), almoco("b", data="2026-04-15"))
        self.assertEqual(codigos(r["a"]), ["FORA_DA_COMPETENCIA"])
        self.assertEqual(codigos(r["b"]), ["FORA_DA_COMPETENCIA"])

    def test_rn007_original_fora_da_politica_nao_torna_a_copia_duplicata(self):
        r = itens(almoco("a", categoria="coworking"), almoco("b", categoria="coworking"))
        self.assertEqual(codigos(r["b"]), ["CATEGORIA_NAO_REEMBOLSAVEL"])


if __name__ == "__main__":
    unittest.main()
