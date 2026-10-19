# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Baseado na spec:** 2.0

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
despesas.json ─► cli.py ─► entrada.py ─► regras.py ─► saida.py ─► resultado.json
                 (I/O)     (valida,       (núcleo puro:   (serializa,
                  │         arredonda,     etapas na       totais)
                  │         normaliza)     ordem da §8)
                  │                          ▲      ▲
politica-v4.json ─┼──────► politica.py ──────┘      │   (carrega/valida tabela,
cambio.json ──────┴──────► cambio.py ───────────────┘    tabela_para(cc); cotacao(moeda, data))
```

*(v1.0: `politica.py` era um módulo de constantes da v3 — ver DT-006.)*

**Fronteiras:** só `cli.py` toca disco e `sys.exit`. `entrada.py`, `regras.py` e
`saida.py` são funções puras de dados → dados, testáveis sem arquivo. `politica.py`
e `cambio.py` recebem dicionários já lidos (a CLI lê os arquivos) e devolvem objetos
validados. O motor pergunta "qual o limite desta categoria" e "qual a cotação desta
moeda nesta data", sem saber de onde vêm os números.

## 3. Modelo de dados

- `Despesa` (imutável): `id`, `data: date`, `categoria` (normalizada),
  `categoria_informada`, `descricao`, `fornecedor`, `moeda` (normalizada, RN-014),
  `valor_informado: Decimal` (cru) e `valor: Decimal` (arredondado **na moeda da despesa**,
  RN-002), `tem_nota_fiscal`.
- `Entrada`: `colaborador` e `periodo` (dicts repassados), `inicio`, `fim`, `despesas`.
- `Avaliacao` (mutável, uma por despesa, dentro do motor): `despesa`,
  `valor: Decimal|None` (em BRL; `None` até a conversão — RN-014), `taxa`, `data_cotacao`,
  `reembolsavel: Decimal`, `encerrada_como: str|None`, `pendente: bool` (RN-016),
  `motivos: list[Motivo]`.
- `Politica` (imutável): `versao`, `padrao: {categoria: Limite}`, `centros_custo`,
  `nota_fiscal_acima_de`, `acrescimo_viagem` (fração: 50% → 0,50); `tabela_para(cc)`
  devolve `(nome, {categoria: Limite})` já com a herança do padrão (RN-013).
- `Cambio` (imutável): `{date: {moeda: Decimal}}`; `cotacao(moeda, data)` → `(taxa, data)` ou `None`.
- `Contexto`: `entrada`, `politica`, `cambio`, `nome_tabela`, `limites` — o que toda etapa recebe.
  O `status` é derivado (RN-012), nunca armazenado separadamente — impossível
  ficar inconsistente com o valor.
- `Motivo` (imutável): `codigo`, `regra` (ID da RN), `mensagem`.

## 4. Como a política é representada

**v2.0:** arquivo JSON externo no formato do financeiro (spec 4.4), lido pela CLI.
Padrão: `politicas/politica-v4.json` (cópia vigente versionada no repo); outro arquivo
via `--politica`. Câmbio idem: `politicas/cambio.json` ou `--cambio`.
O único número de política que continua no código é o limiar de aprovação manual
(R$ 500,00, RN-016), porque a spec o fixa e a tabela do financeiro não o traz.

*v1.0 (substituído):* constantes em `politica.py`; arquivo externo tinha sido descartado
por não haver pedido de política variável. A troca ficou contida em `politica.py` como
previsto — ver DT-006 e o relatório para o que **não** ficou contido.

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

### DT-006 — Política como dado carregado (substitui §4 da v1.0)

**Contexto:** v4 item A: "ler a política de fora, não de dentro do código".
**Decisão:** `politica.carregar_politica(dict) -> Politica` valida a estrutura (RN-015);
etapas leem `ctx.limites[categoria]` em vez de `politica.LIMITES`.
**Alternativa descartada:** manter constantes e gerar um módulo Python a partir do JSON — o financeiro edita o arquivo sem deploy.
**Consequência:** a v3 vira só mais um arquivo; os testes de regra antigos rodam com o `padrao` da v4, que tem os mesmos números.

### DT-007 — Contexto único para as etapas

**Contexto:** etapas passaram a precisar de política, câmbio e tabela escolhida, além da entrada.
**Decisão:** `etapa(avaliacoes, ctx)`; o `ctx` é montado uma vez em `avaliar`.
**Alternativa descartada:** variáveis globais carregadas na importação — impediria testar com tabelas diferentes no mesmo processo.

### DT-008 — Busca de cotação para trás

**Decisão:** `cotacao` tenta a data da despesa e até 7 dias anteriores (`JANELA_DIAS = 7`), na ordem.
**Alternativa descartada:** índice ordenado + busca binária — a tabela tem dezenas de datas.

### DT-009 — Regressão da v3 como fixture de teste

**Decisão:** `tests/dados/politica-v3.json` (só `padrao`, sem centros de custo) reproduz a v3;
`test_aceite_exemplo.py` roda a CLI com `--politica` apontando para ele (§9.1).
**Alternativa descartada:** apagar o aceite v1.0 — perderíamos a prova de que as regras da v3 não regrediram.

## 6. Estratégia de testes

- **Nível:** ~85% unitário sobre o motor (monta a entrada em memória), um arquivo
  de integração ponta a ponta que roda a CLI de verdade sobre `exemplos/despesas-exemplo.json`.
- **Cada `RN-NNN` tem teste:** um arquivo por regra, `tests/test_rnNNN_<nome>.py`;
  a matriz de cobertura em `tasks.md` liga RN → task → teste.
- **Casos de borda da seção 7:** cada linha da tabela é um método de teste.
- **Nomenclatura:** `test_rn009_duas_refeicoes_no_mesmo_dia_dividem_o_limite` —
  o prefixo da regra fecha a rastreabilidade; AMB citadas na docstring.
- **Critérios da §9:** `tests/test_aceite_exemplo.py` (§9.1, tabela v3) e
  `tests/test_aceite_v4.py` (§9.2–9.4, tabelas vigentes), um assert por bullet.
- **Tabelas nos testes de regra:** `tests/apoio.py` usa as tabelas vigentes por padrão e aceita
  tabela/câmbio em memória para casos específicos (`politica=`, `cambio=`).

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Arredondamento com `float` escondido | média | Leitura JSON com `parse_float=Decimal`; teste de `10.005` |
| Ordem das etapas divergir da §8 | média | A lista de etapas é única e comentada com a §8; teste de duplicata sem nota |
| Mudança de requisito no Dia 2 mexer na política | alta | Política isolada em `politica.py` |
| Regex de diárias pegar número errado ("Hotel 5 estrelas 2 noites") | baixa | Só aceita número imediatamente seguido de diária/noite |
| Taxa de câmbio lida como `float` | média | Tabela de câmbio também lida com `parse_float=Decimal` |
| Arquivo de política padrão não encontrado quando a CLI roda de outra pasta | média | Caminho padrão resolvido a partir do arquivo do pacote, não do diretório atual |
