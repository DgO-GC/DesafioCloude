# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.0

> Aqui mora o COMO. Este arquivo pode e deve falar de linguagem, biblioteca e
> arquitetura. O que ele **não** pode é introduzir regra de negócio nova — se
> apareceu uma, ela pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.10+ (testado em 3.12) | Já instalado na máquina; legível para correção | Node/TS: exigiria `npm install` e build |
| Testes | `unittest` (biblioteca padrão) | Zero dependência: o projeto roda pelo README sem instalar nada | `pytest`: melhor ergonomia, mas exigiria `pip install` e quebraria o "roda sem intervenção" |
| Parsing/validação | `json` + validação manual em `entrada.py` | Schema pequeno; mensagens de erro em português citando o id da despesa | `jsonschema`/`pydantic`: dependência externa para ~15 campos |
| Aritmética monetária | `decimal.Decimal`, JSON lido com `parse_float=Decimal` | O valor nunca passa por `float`: `33.333` chega exato e é arredondado com `ROUND_HALF_UP` (RN-002) | `float`: `0.1+0.2≠0.3`. Centavos em `int`: exigiria converter na leitura, e o arredondamento de `33.333` já precisaria de `Decimal` de qualquer jeito |
| CLI | `argparse` com subcomando `calcular` | Interface fixa do desafio; biblioteca padrão | `click`/`typer`: dependência externa |

## 2. Arquitetura

```
arquivo JSON ─► cli.py ─► entrada.py ─► regras.py ─► saida.py ─► arquivo JSON
                (I/O)     (valida,       (núcleo puro:   (serializa,
                           arredonda,     etapas na       totais)
                           normaliza)     ordem da §8)
                                 ▲
                           politica.py (limites e constantes da v3)
```

**Fronteiras:** só `cli.py` toca disco e `sys.exit`. `entrada.py`, `regras.py` e
`saida.py` são funções puras de dados → dados, testáveis sem arquivo. A política
fica isolada em `politica.py`: o motor pergunta "qual o limite desta categoria",
não sabe de onde vem o número.

## 3. Modelo de dados

- `Despesa` (imutável): `id`, `data: date`, `categoria` (normalizada),
  `categoria_informada`, `descricao`, `fornecedor`, `valor_informado: Decimal`
  (cru) e `valor: Decimal` (arredondado, RN-002), `tem_nota_fiscal`.
- `Entrada`: `colaborador` e `periodo` (dicts repassados), `inicio`, `fim`, `despesas`.
- `Avaliacao` (mutável, uma por despesa, dentro do motor): `despesa`,
  `reembolsavel: Decimal`, `encerrada_como: str|None`, `motivos: list[Motivo]`.
  O `status` é derivado (RN-012), nunca armazenado separadamente — impossível
  ficar inconsistente com o valor.
- `Motivo` (imutável): `codigo`, `regra` (ID da RN), `mensagem`.

## 4. Como a política é representada

Constantes num único módulo `politica.py` (limites por categoria com
periodicidade `dia`/`diaria`, limiar de nota fiscal, acréscimo de viagem).
Nenhum outro módulo contém número de política.

Descartado: arquivo de configuração externo. A spec 1.0 não pede política
variável, e o FAQ alerta contra arquitetura genérica no lugar errado. Se a política
virar dado externo, só `politica.py` muda de "constante" para "carregado".

## 5. Decisões técnicas

### DT-001 — Pipeline de etapas sobre a lista inteira

**Contexto:** RN-007 (duplicata), RN-009 (saldo diário) e RN-011 (viagem) precisam
enxergar outras despesas, não só a atual.
**Decisão:** o motor é uma lista ordenada de etapas `etapa(avaliacoes, entrada)`,
cada uma com acesso à lista toda; a ordem da lista É a seção 8 da spec.
**Alternativa descartada:** avaliar despesa por despesa com função pura por item —
quebra para regras de agregação.
**Consequência:** fácil inserir/reordenar regra; cada etapa precisa pular itens já encerrados.

### DT-002 — Status derivado

**Contexto:** RN-012 define status a partir de valor e encerramento.
**Decisão:** `status` é propriedade calculada de `Avaliacao`.
**Alternativa descartada:** campo de status atribuído por cada etapa — risco de
`aprovado` com valor glosado.

### DT-003 — Monetário como texto na saída

**Contexto:** spec 4.2 exige 2 casas exatas.
**Decisão:** `saida.py` formata `Decimal` com `f"{v:.2f}"`.
**Alternativa descartada:** número JSON via `float` — `60.0` em vez de `60.00` e risco de binário.

### DT-004 — Diárias por expressão regular na descrição

**Contexto:** RN-010.
**Decisão:** remover acentos (`unicodedata`), minúsculas, regex `(\d+)\s*(diarias?|noites?)`; primeira ocorrência.
**Alternativa descartada:** campo novo na entrada — o formato de entrada é fixo.

### DT-005 — Execução sem instalação

**Decisão:** `run.py` na raiz adiciona `src/` ao `sys.path`; `tests/__init__.py` faz o mesmo.
**Alternativa descartada:** `pyproject.toml` + `pip install -e .` — um passo a mais para quem corrige.

## 6. Estratégia de testes

- **Nível:** ~85% unitário sobre o motor (monta a entrada em memória), um arquivo
  de integração ponta a ponta que roda a CLI de verdade sobre `exemplos/despesas-exemplo.json`.
- **Cada `RN-NNN` tem teste:** um arquivo por regra, `tests/test_rnNNN_<nome>.py`;
  a matriz de cobertura em `tasks.md` liga RN → task → teste.
- **Casos de borda da seção 7:** cada linha da tabela é um método de teste.
- **Nomenclatura:** `test_rn009_duas_refeicoes_no_mesmo_dia_dividem_o_limite` —
  o prefixo da regra fecha a rastreabilidade; AMB citadas na docstring.
- **Critérios da §9:** `tests/test_aceite_exemplo.py`, um assert por bullet.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Arredondamento com `float` escondido | média | Leitura JSON com `parse_float=Decimal`; teste de `10.005` |
| Ordem das etapas divergir da §8 | média | A lista de etapas é única e comentada com a §8; teste de duplicata sem nota |
| Mudança de requisito no Dia 2 mexer na política | alta | Política isolada em `politica.py` |
| Regex de diárias pegar número errado ("Hotel 5 estrelas 2 noites") | baixa | Só aceita número imediatamente seguido de diária/noite |
