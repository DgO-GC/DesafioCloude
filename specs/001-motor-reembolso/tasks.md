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

## Fase 5 — Envelope v4 (D-001)

- [x] **T-014** — Política lida de tabela externa validada; CLI `--politica`; saída informa versão e tabela
  - **Atende:** RN-015 (política), §4.4, §4.2 (`politica`, `tabela_de_limites`); refaz parte de T-003, T-007
  - **Aceite:** `tests/test_rn015_tabelas.py` (casos de política) passa; testes T-001..T-013 continuam passando
  - **Commit:** `59ef4f9`

- [x] **T-015** — Tabela de limites por centro de custo com herança do padrão e limite 0
  - **Atende:** RN-013, RN-006, AMB-016, AMB-017, AMB-018, AMB-019; refaz T-003
  - **Aceite:** `tests/test_rn013_centro_custo.py` passa
  - **Commit:** `f5bc542`

- [x] **T-016** — Limites, limiar de nota e acréscimo vindos da tabela, por periodicidade
  - **Atende:** RN-008, RN-009, RN-010, RN-011 (acréscimo), AMB-025; refaz T-007..T-010
  - **Aceite:** `tests/test_rn016_periodicidade_da_tabela.py` passa
  - **Commit:** `dcaa4a5`

- [x] **T-017** — Campo `moeda`, tabela de câmbio e conversão para BRL pela cotação da data
  - **Atende:** RN-014, RN-015 (câmbio), RN-007 (chave com moeda), AMB-020..AMB-023, AMB-028, AMB-029
  - **Aceite:** `tests/test_rn014_cambio.py` e casos de câmbio de `test_rn015_tabelas.py` passam
  - **Commit:** `7211927`

- [x] **T-018** — Despesa em moeda estrangeira caracteriza dia em viagem
  - **Atende:** RN-011, AMB-024; refaz T-010
  - **Aceite:** casos `test_rn011_moeda_*` em `tests/test_rn011_viagem.py` passam
  - **Commit:** `58a2b91`

- [x] **T-019** — Aprovação manual acima de R$ 500,00 e schema de saída 2.0
  - **Atende:** RN-016, RN-012, §4.2, AMB-027; refaz T-011
  - **Aceite:** `tests/test_rn016_aprovacao_manual.py` passa; `test_rn012_status_totais.py` atualizado para o schema 2.0 passa
  - **Commit:** `8cc3e55`

- [x] **T-020** — Aceite ponta a ponta: regressão v3 e exemplos do envelope
  - **Atende:** §9.1–9.5; refaz T-012
  - **Aceite:** `tests/test_aceite_exemplo.py` (com tabela v3) e `tests/test_aceite_v4.py` passam
  - **Commit:** `16c121b`

- [x] **T-021** — README e CLAUDE.md para a v4
  - **Atende:** entrega
  - **Aceite:** README mostra como rodar com tabela/câmbio padrão e alternativos; comandos conferidos numa pasta limpa
  - **Commit:** `c65825f`

## Fase 6 — Fechamento

- [x] **T-022** — Relatório final e sessões exportadas
  - **Atende:** entrega (`docs/RELATORIO.md`, `docs/sessions/`)
  - **Aceite:** os 5 blocos do relatório citam commits/arquivos; `docs/sessions/` tem o export da sessão
  - **Commit:** `ec2c167`

## Fase 7 — Revisão (D-002)

- [ ] **T-023** — Despesa recusada por falta de nota ou duplicata não caracteriza viagem
  - **Atende:** RN-011, AMB-005, D-002; refaz T-010 e T-018
  - **Aceite:** `tests/test_rn011_viagem.py` passa, incluindo `test_rn011_hospedagem_sem_nota_nao_caracteriza_viagem` e `test_rn011_brecha_hospedagem_falsa_30_noites`
  - **Commit:**

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
| §9 (v1.0) / §9.1 | T-012, T-020 | `test_aceite_exemplo` |
| RN-013 / AMB-016..019 | T-015 | `test_rn013_centro_custo` |
| RN-014 / AMB-020..023, 028, 029 | T-017 | `test_rn014_cambio` |
| RN-015 | T-014, T-017 | `test_rn015_tabelas` |
| RN-008..011 via tabela / AMB-025 | T-016 | `test_rn016_periodicidade_da_tabela` |
| RN-011 / AMB-024 | T-018 | `test_rn011_viagem` (`test_rn011_moeda_*`) |
| RN-016 / AMB-027 | T-019 | `test_rn016_aprovacao_manual` |
| RN-012 (schema 2.0) | T-019 | `test_rn012_status_totais` |
| §9.2–9.4 | T-020 | `test_aceite_v4` |
| RN-011 / AMB-005 (D-002) | T-023 | `test_rn011_viagem` |
