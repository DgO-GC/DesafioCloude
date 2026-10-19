# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [x] **T-001** — Esqueleto: CLI `calcular`, leitura e validação da entrada, saída com itens e totais sem regras
  - **Atende:** RN-001, seção 4
  - **Aceite:** `tests/test_rn001_validacao.py` passa; `python run.py calcular --input exemplos/despesas-exemplo.json --output /tmp/x.json` gera arquivo
  - **Commit:** `e22e2cb`

- [x] **T-002** — Arredondamento monetário na entrada
  - **Atende:** RN-002, AMB-010
  - **Aceite:** `tests/test_rn002_arredondamento.py` passa
  - **Commit:** `edadc57`

- [x] **T-003** — Normalização de categoria e categorias da política
  - **Atende:** RN-003, RN-006, AMB-011, AMB-012
  - **Aceite:** `tests/test_rn003_rn006_categoria.py` passa
  - **Commit:** `ec7e08e`

## Fase 2 — Regras de elegibilidade

- [x] **T-004** — Período de competência inclusivo
  - **Atende:** RN-004, AMB-008
  - **Aceite:** `tests/test_rn004_competencia.py` passa
  - **Commit:** `c4e9d5e`

- [x] **T-005** — Valor não positivo é ignorado
  - **Atende:** RN-005, AMB-009
  - **Aceite:** `tests/test_rn005_valor_nao_positivo.py` passa
  - **Commit:** `021f619`

- [x] **T-006** — Detecção de duplicatas
  - **Atende:** RN-007, AMB-007
  - **Aceite:** `tests/test_rn007_duplicatas.py` passa
  - **Commit:** `7aee342`

- [x] **T-007** — Nota fiscal obrigatória acima de 100,00
  - **Atende:** RN-008, AMB-004
  - **Aceite:** `tests/test_rn008_nota_fiscal.py` passa
  - **Commit:** `d12d4af`

## Fase 3 — Limites

- [x] **T-008** — Limite diário com saldo compartilhado e reembolso parcial
  - **Atende:** RN-009, AMB-001, AMB-002, AMB-003, AMB-014
  - **Aceite:** `tests/test_rn009_limite_diario.py` passa
  - **Commit:** `c7d62ea`

- [x] **T-009** — Limite de hospedagem por diária
  - **Atende:** RN-010, AMB-006
  - **Aceite:** `tests/test_rn010_hospedagem.py` passa
  - **Commit:** `d3b80ca`

- [x] **T-010** — Dias em viagem ampliam limites diários
  - **Atende:** RN-011, AMB-005, AMB-013
  - **Aceite:** `tests/test_rn011_viagem.py` passa
  - **Commit:** `134b176`

## Fase 4 — Saída e aceite

- [x] **T-011** — Status, motivos, totais e ordem das regras
  - **Atende:** RN-012, AMB-015, seção 8
  - **Aceite:** `tests/test_rn012_status_totais.py` passa
  - **Commit:** `aae0eed`, `79e917d`

- [x] **T-012** — Teste de aceite ponta a ponta sobre o exemplo
  - **Atende:** seção 9 inteira
  - **Aceite:** `tests/test_aceite_exemplo.py` passa
  - **Commit:** `cacbff2`

- [x] **T-013** — README do projeto e CLAUDE.md preenchido
  - **Atende:** entrega (rubrica §5)
  - **Aceite:** seguindo só o README, rodar e testar funciona numa pasta limpa
  - **Commit:** `eeb426e`

---

## Fase 5 — Envelope (criar no Dia 2)

<Novas tasks a partir da mudança de requisito. Numeração continua de onde parou.>

---

## Cobertura

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-001 | `test_rn001_validacao` |
| RN-002 / AMB-010 | T-002 | `test_rn002_arredondamento` |
| RN-003 / AMB-011 | T-003 | `test_rn003_rn006_categoria` |
| RN-004 / AMB-008 | T-004 | `test_rn004_competencia` |
| RN-005 / AMB-009 | T-005 | `test_rn005_valor_nao_positivo` |
| RN-006 / AMB-012 | T-003 | `test_rn003_rn006_categoria` |
| RN-007 / AMB-007 | T-006 | `test_rn007_duplicatas` |
| RN-008 / AMB-004 | T-007 | `test_rn008_nota_fiscal` |
| RN-009 / AMB-001, 002, 003, 014 | T-008 | `test_rn009_limite_diario` |
| RN-010 / AMB-006 | T-009 | `test_rn010_hospedagem` |
| RN-011 / AMB-005, 013 | T-010 | `test_rn011_viagem` |
| RN-012 / AMB-015 | T-011 | `test_rn012_status_totais` |
| §9 | T-012 | `test_aceite_exemplo` |
