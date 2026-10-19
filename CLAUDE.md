# CLAUDE.md

## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit referencia uma task: `feat(T-003): <descrição>`.
  Mudanças de documentação: `docs(spec):`, `docs(plan):`, `docs(tasks):`.
- Nenhuma regra de negócio entra sem teste. Não commitar com teste vermelho.
- A spec não cita linguagem, biblioteca nem arquivo — isso vai no `plan.md`.

## Stack e comandos

- Linguagem: Python 3.10+ só com biblioteca padrão (nada de `pip install`)
- Rodar: `python run.py calcular --input exemplos/despesas-exemplo.json --output resultado.json`
- Testes: `python -m unittest discover -s tests -t .`
- Lint/format: não há ferramenta; seguir PEP 8, linhas até ~110 colunas

## Convenções de código

- Pipeline em `src/reembolso/regras.py`: a lista `ETAPAS` é a seção 8 da spec, na mesma ordem.
  Toda etapa tem docstring que começa com o ID da regra (`"""RN-009: ...`).
- Todo motivo carrega `codigo` estável + `regra` (ID da RN). Código novo → tabela da RN-012.
- Números de política só nas tabelas de `politicas/*.json` (o financeiro edita). Única exceção:
  o limiar de aprovação manual (R$ 500, RN-016) em `politica.py`, porque a spec o fixa.
- Testes de regra usam as tabelas vigentes por padrão; tabela/câmbio específicos via
  `tests/apoio.politica(...)` e `rodar(..., politica=, cambio=)`. A v3 vive em `tests/dados/politica-v3.json`.
- Cuidado ao escrever teste: hospedagem ou moeda estrangeira no mesmo dia tornam o dia "em viagem"
  (RN-011) e mudam o limite; outra despesa da mesma categoria no mesmo dia consome o saldo (RN-009).
- Erro de entrada → `EntradaInvalida` com o id da despesa; só `cli.py` decide código de saída.
- Testes: `tests/test_rnNNN_<nome>.py`, métodos `test_rnNNN_<comportamento>`; montar entrada com `tests/apoio.py`.
- Valores monetários: `decimal.Decimal`, JSON lido com `parse_float=Decimal`; **nunca `float`**.
  Arredondamento uma única vez: na entrada (BRL) ou no produto da conversão (moeda estrangeira);
  saída sempre texto com 2 casas.
- Arquivos: gravar sempre com LF (`.gitattributes`); no Windows, `Path.write_text` grava CRLF —
  usar `newline="\n"` ou `write_bytes`.

## Fora de escopo

- Pagamento, integração com folha/contábil, autenticidade de nota fiscal.
- Vários colaboradores por execução; duplicatas entre períodos; estado entre execuções.
- Interface gráfica, API HTTP, banco de dados.
