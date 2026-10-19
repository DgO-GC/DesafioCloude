# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.

Ordem cronológica inversa: a mais recente primeiro.

---

## D-001 — Política v4: limites por centro de custo, moeda estrangeira e aprovação manual · `2026-10-18`

**Gatilho:** envelope lacrado do Dia 2 (`exemplos/envelope/00-ENVELOPE-LACRADO.md`).

**O que mudou na spec (1.0 → 2.0):**

| Onde | De | Para |
|---|---|---|
| §2, §3 | política v3; "não converte moeda"; "não oferece aprovação manual" | política v4; conversão por tabela de câmbio; aprovação sinalizada (sem workflow) |
| §4.1 | `centro_custo` só repassado | `centro_custo` escolhe a tabela; novo campo `moeda` |
| §4.2 | schema `1.0`, 4 status, `valor_considerado` sempre em BRL | schema `2.0`: `tabela_de_limites`, `moeda`, `taxa_cambio`, `data_cotacao`, `valor_considerado` pode ser nulo, status `pendente_aprovacao`, `totais.valor_pendente_aprovacao` |
| §4.3–4.5 | — | tabelas de política e câmbio são entradas externas validadas |
| RN-006 | lista fixa de 3 categorias | categorias da tabela aplicável; limite 0 = bloqueada |
| RN-007 | chave com `valor_considerado` | chave com moeda + valor na moeda original |
| RN-008 | R$ 100,00 fixo | limiar da tabela, comparado em BRL |
| RN-009 / RN-010 | alimentação e transporte / hospedagem por nome | por periodicidade `dia` / `diaria` da tabela |
| RN-011 | só hospedagem caracteriza viagem; +50% para alim./transp. | também moeda estrangeira; % da tabela para toda periodicidade `dia` |
| RN-012 | 4 status | 5 status e 3 códigos novos |
| novas | — | RN-013 (tabela por CC), RN-014 (câmbio), RN-015 (validação das tabelas), RN-016 (aprovação manual) |
| §6 | AMB-001..AMB-015 | + AMB-016..AMB-029 |
| §8 | 8 passos | 10 passos (conversão entre duplicata e nota; aprovação no fim) |
| §9 | aceite só do exemplo | 9.1 regressão v3, 9.2 exemplo com v4, 9.3 envelope, 9.4 CC desconhecido |

**Por quê:** a política deixa de ser única (item A), passa a aceitar moeda
estrangeira (item B) e ganha fila de aprovação (item C, opcional — implementado
porque cabia sem deixar a spec inconsistente).

**O que isso invalidou:**

- *Decisão técnica:* plan.md §4 / "constantes em `politica.py`" → política vira dado carregado de arquivo (DT-006).
- *Saída:* quem lia `versao_schema 1.0` quebra (campos novos, status novo, `valor_considerado` nulo).
- *Testes que caem por contrato* (quebra justificada, não bug):
  - `test_rn012_exemplo_literal_da_secao_4_2`, `test_rn012_contagem_tem_sempre_os_quatro_status`,
    `test_aceite_totais` — esperavam schema 1.0 e 4 status.
  - `test_rn010_noites_com_nota_dentro_do_limite` — 690,00 passa a ser `pendente_aprovacao` (RN-016).
  - `test_aceite_exemplo` inteiro — o exemplo é de CC-ENG-PLATAFORMA e a v4 muda os limites desse CC.
    Mantido como **regressão v3** (§9.1) rodando com uma tabela equivalente à v3; o novo aceite v4 é §9.2.
- *Testes que continuam valendo sem mudança:* todos os de RN-001..RN-011 que usam centro de custo
  fictício (`CC-TESTE`), porque ele cai no `padrao` da v4, que tem os mesmos números da v3.

**Tasks afetadas:**
- Refeitas: T-003 (categorias), T-007 (limiar), T-008/T-009/T-010 (limites e viagem), T-011 (saída), T-012 (aceite).
  Não reabertas — o trabalho novo está nas tasks abaixo, que citam as antigas.
- Novas: T-014..T-021 (Fase 5 do `tasks.md`).

**Custo:** ver `docs/RELATORIO.md`, seção "O envelope" (arquivos tocados e diff medidos no fim da absorção).
