# Motor de Cálculo de Reembolso — Desafio SDD

Solução de **Diego Castilho** para o [Desafio Prático de Spec Driven Development](https://github.com/Sassine/sdd-desafio)
(enunciado original em [`DESAFIO.md`](DESAFIO.md), rubrica em [`RUBRICA.md`](RUBRICA.md)).

CLI que lê as despesas de um colaborador em JSON e escreve um JSON com o valor
reembolsável e a justificativa de cada item, segundo a política de reembolso **v4**
(limites por centro de custo, moeda estrangeira, aprovação manual acima de R$ 500)
**com as ambiguidades resolvidas em [`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md)**.

## Requisitos

- Python **3.10 ou superior** (testado em 3.12). Nenhuma dependência externa, nada para instalar.

## Como rodar

```bash
python run.py calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

Por padrão usa as tabelas vigentes do financeiro em [`politicas/`](politicas/)
(`politica-v4.json` e `cambio.json`). Para usar outras, sem mexer no código:

```bash
python run.py calcular --input exemplos/envelope/despesas-envelope.json --output resultado.json --politica politicas/politica-v4.json --cambio politicas/cambio.json
```

Os exemplos do envelope do Dia 2 ficam em [`exemplos/envelope/`](exemplos/envelope/).
Para reproduzir o comportamento da v3: `--politica tests/dados/politica-v3.json`.

- Código de saída `0`: `resultado.json` foi escrito.
- Código `1`: entrada ou tabela inválida ou ilegível. A mensagem vai para stderr e **nenhum arquivo é gerado** (spec 4.3).
- Código `2`: uso incorreto da linha de comando.

Alternativa sem o atalho: `cd src && python -m reembolso calcular --input ../exemplos/despesas-exemplo.json --output ../resultado.json`.

## Como testar

```bash
python -m unittest discover -s tests -t .
```

Cada arquivo `tests/test_rnNNN_*.py` cobre uma regra `RN-NNN` da spec.
`tests/test_aceite_exemplo.py` (regressão v3, §9.1) e `tests/test_aceite_v4.py` (§9.2–9.5)
rodam a CLI de verdade sobre os exemplos e conferem cada critério da seção 9 da spec.

## Formato da saída (resumo)

Trecho da saída para `exemplos/envelope/despesas-envelope.json`:

```json
{
  "versao_schema": "2.0",
  "politica": "v4",
  "tabela_de_limites": "CC-COMERCIAL",
  "itens": [{"id": "e-004", "moeda": "EUR", "valor_informado": "30.00", "taxa_cambio": "5.96",
             "data_cotacao": "2026-07-17", "valor_considerado": "178.80", "valor_reembolsavel": "135.00",
             "status": "parcial",
             "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009", "mensagem": "..."}]}],
  "totais": {"valor_solicitado": "2457.52", "valor_reembolsavel": "833.72",
             "valor_pendente_aprovacao": "1200.00", "valor_glosado": "423.80",
             "itens_por_status": {"aprovado": 4, "parcial": 2, "recusado": 3, "ignorado": 0,
                                  "pendente_aprovacao": 1}}
}
```

Valores monetários são texto com 2 casas. Status possíveis: `aprovado`, `parcial`, `recusado`,
`ignorado`, `pendente_aprovacao`. O schema completo está na spec, seção 4.2.

## Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| [`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md) | O quê e o porquê: regras `RN-*`, ambiguidades `AMB-*`, casos de borda, aceite |
| [`specs/001-motor-reembolso/plan.md`](specs/001-motor-reembolso/plan.md) | O como: stack, arquitetura, decisões técnicas `DT-*` |
| [`specs/001-motor-reembolso/tasks.md`](specs/001-motor-reembolso/tasks.md) | Tasks `T-*` com rastreabilidade RN → task → teste → commit |
| [`specs/001-motor-reembolso/DECISIONS.md`](specs/001-motor-reembolso/DECISIONS.md) | Log de mudanças da spec |
| `src/reembolso/` | `cli` (I/O) → `entrada` (validação) → `regras` (motor) → `saida` (JSON); `politica` e `cambio` (tabelas) |
| `politicas/` | Tabelas vigentes do financeiro (política v4 e câmbio) — editáveis sem mexer no código |
| `tests/` | Testes nomeados pela regra que verificam |
| [`docs/RELATORIO.md`](docs/RELATORIO.md) | Relatório final (4 Ds + envelope) |
| `docs/sessions/` | Exports das sessões com o Claude Code |
