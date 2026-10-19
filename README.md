# Motor de Cálculo de Reembolso — Desafio SDD

Solução de **Diego Castilho** para o [Desafio Prático de Spec Driven Development](https://github.com/Sassine/sdd-desafio)
(enunciado original em [`DESAFIO.md`](DESAFIO.md), rubrica em [`RUBRICA.md`](RUBRICA.md)).

CLI que lê as despesas de um colaborador em JSON e escreve um JSON com o valor
reembolsável e a justificativa de cada item, segundo a política de reembolso
**com as ambiguidades resolvidas em [`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md)**.

## Requisitos

- Python **3.10 ou superior** (testado em 3.12). Nenhuma dependência externa, nada para instalar.

## Como rodar

```bash
python run.py calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

- Código de saída `0`: `resultado.json` foi escrito.
- Código `1`: entrada inválida ou ilegível. A mensagem vai para stderr e **nenhum arquivo é gerado** (spec 4.3).
- Código `2`: uso incorreto da linha de comando.

Alternativa sem o atalho: `cd src && python -m reembolso calcular --input ../exemplos/despesas-exemplo.json --output ../resultado.json`.

## Como testar

```bash
python -m unittest discover -s tests -t .
```

Cada arquivo `tests/test_rnNNN_*.py` cobre uma regra `RN-NNN` da spec.
`tests/test_aceite_exemplo.py` roda a CLI de verdade sobre o exemplo e confere
cada critério da seção 9 da spec.

## Formato da saída (resumo)

```json
{
  "versao_schema": "1.0",
  "politica": "v3",
  "itens": [{"id": "d-001", "status": "parcial", "valor_considerado": "72.50",
             "valor_reembolsavel": "60.00",
             "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009", "mensagem": "..."}]}],
  "totais": {"valor_solicitado": "1861.84", "valor_reembolsavel": "815.43", "valor_glosado": "1046.41",
             "itens_por_status": {"aprovado": 4, "parcial": 3, "recusado": 6, "ignorado": 1}}
}
```

Valores monetários são texto com 2 casas. O schema completo está na spec, seção 4.2.

## Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| [`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md) | O quê e o porquê: regras `RN-*`, ambiguidades `AMB-*`, casos de borda, aceite |
| [`specs/001-motor-reembolso/plan.md`](specs/001-motor-reembolso/plan.md) | O como: stack, arquitetura, decisões técnicas `DT-*` |
| [`specs/001-motor-reembolso/tasks.md`](specs/001-motor-reembolso/tasks.md) | Tasks `T-*` com rastreabilidade RN → task → teste → commit |
| [`specs/001-motor-reembolso/DECISIONS.md`](specs/001-motor-reembolso/DECISIONS.md) | Log de mudanças da spec |
| `src/reembolso/` | `cli` (I/O) → `entrada` (validação) → `regras` (motor) → `saida` (JSON); `politica` (limites) |
| `tests/` | Testes nomeados pela regra que verificam |
| [`docs/RELATORIO.md`](docs/RELATORIO.md) | Relatório final (4 Ds + envelope) |
| `docs/sessions/` | Exports das sessões com o Claude Code |
