# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.0 (política v4 — ver `DECISIONS.md` D-001) · **Status:** aprovada para implementação · **Última alteração:** 2026-10-18

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui cita linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O financeiro confere manualmente, item por item, as despesas de cada colaborador
contra a política de reembolso do RH. O processo é lento, e como a política é
ambígua, duas pessoas chegam a valores diferentes para a mesma planilha.

## 2. Objetivo

Dado o conjunto de despesas de um colaborador em um período de competência, o
sistema calcula de forma determinística quanto é reembolsável e justifica cada
decisão item a item, aplicando a política v4 (limites por centro de custo, despesas em
moeda estrangeira e fila de aprovação manual) com as interpretações fixadas nesta spec.

## 3. Fora de escopo

- Não efetua pagamento, não integra com folha nem com sistema contábil.
- Não verifica a autenticidade da nota fiscal — confia no indicador `tem_nota_fiscal`.
- Não processa mais de um colaborador por execução.
- Não consulta despesas de outros períodos (não detecta duplicata entre períodos diferentes).
- Não busca cotação de câmbio em fonte externa: usa apenas a tabela de câmbio recebida (4.5).
- Não escolhe versão de política pela data: aplica a tabela recebida a qualquer competência (AMB-026).
- Não registra a decisão do gestor sobre itens pendentes: apenas os sinaliza (RN-016).
- Não aplica regras por dia da semana, feriado ou fim de semana.
- Não mantém histórico nem estado entre execuções: mesma entrada, mesma saída.
- Não corrige a entrada: categoria desconhecida, data fora do período etc. viram
  recusas justificadas, não "consertos".
- Não oferece workflow de aprovação nem interface gráfica.

## 4. Entrada e saída

### 4.1 Entrada

Um documento JSON no formato de `exemplos/despesas-exemplo.json`.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | texto | Identificador do colaborador | sim |
| `colaborador.nome` | texto | Nome (apenas repassado à saída) | não |
| `colaborador.centro_custo` | texto | Centro de custo; define a tabela de limites (RN-013) | não |
| `periodo.competencia` | texto `AAAA-MM` | Mês de competência (apenas repassado) | sim |
| `periodo.inicio` | data `AAAA-MM-DD` | Primeiro dia do período, inclusivo | sim |
| `periodo.fim` | data `AAAA-MM-DD` | Último dia do período, inclusivo | sim |
| `despesas[]` | lista | Despesas a avaliar (pode ser vazia) | sim |
| `despesas[].id` | texto | Identificador da despesa | sim |
| `despesas[].data` | data `AAAA-MM-DD` | Data em que a despesa ocorreu | sim |
| `despesas[].categoria` | texto | Categoria informada pelo colaborador | sim |
| `despesas[].descricao` | texto | Descrição livre | não (vazio) |
| `despesas[].fornecedor` | texto | Fornecedor | não (vazio) |
| `despesas[].valor` | número | Valor na moeda da despesa; pode ser negativo e ter mais de 2 casas | sim |
| `despesas[].moeda` | texto ISO 4217 | Moeda do valor; ausente ou vazio = `BRL` (RN-014) | não |
| `despesas[].tem_nota_fiscal` | booleano | Se há nota fiscal | sim |

Campos extras são ignorados.

### 4.2 Saída

Um documento JSON. Todo valor monetário é um **texto com exatamente duas casas
decimais e ponto como separador** (ex.: `"60.00"`, `"-45.00"`), para que nenhum
consumidor perca centavos ao ler.

| Campo | Tipo | Significado |
|---|---|---|
| `versao_schema` | texto | Versão deste formato de saída (`"2.0"`) |
| `politica` | texto | Versão da tabela de política aplicada (campo `versao` da tabela, ex. `"v4"`) |
| `tabela_de_limites` | texto | Centro de custo cuja tabela foi usada, ou `"padrao"` (RN-013) |
| `colaborador` | objeto | Cópia de `colaborador` da entrada |
| `periodo` | objeto | Cópia de `periodo` da entrada |
| `itens[]` | lista | Uma entrada por despesa, **na mesma ordem da entrada** |
| `itens[].id` | texto | Id da despesa |
| `itens[].data` | texto | Data da despesa |
| `itens[].categoria` | texto | Categoria normalizada (RN-003) |
| `itens[].moeda` | texto | Moeda normalizada (RN-014) |
| `itens[].valor_informado` | texto | Valor exatamente como veio, na moeda da despesa, sem arredondar |
| `itens[].taxa_cambio` | texto ou nulo | Cotação usada (BRL por unidade); nulo para BRL ou sem cotação |
| `itens[].data_cotacao` | texto ou nulo | Data da cotação usada; nulo para BRL ou sem cotação |
| `itens[].valor_considerado` | monetário ou nulo | Valor em BRL após arredondamento (RN-002, RN-014); nulo se não há cotação |
| `itens[].valor_reembolsavel` | monetário | Quanto será reembolsado (para `pendente_aprovacao`: quanto será pago se o gestor aprovar) |
| `itens[].status` | texto | `aprovado`, `parcial`, `recusado`, `ignorado` ou `pendente_aprovacao` (RN-012) |
| `itens[].motivos[]` | lista | Justificativas; vazia apenas quando `aprovado` sem ressalvas |
| `itens[].motivos[].codigo` | texto | Código estável do motivo (tabela da RN-012) |
| `itens[].motivos[].regra` | texto | ID da regra desta spec que gerou o motivo |
| `itens[].motivos[].mensagem` | texto | Explicação legível para o colaborador |
| `totais.valor_solicitado` | monetário | Soma de `valor_considerado` dos itens **não** ignorados e com valor em BRL conhecido |
| `totais.valor_reembolsavel` | monetário | Soma de `valor_reembolsavel` dos itens `aprovado` e `parcial` (aprovação automática) |
| `totais.valor_pendente_aprovacao` | monetário | Soma de `valor_reembolsavel` dos itens `pendente_aprovacao` |
| `totais.valor_glosado` | monetário | `valor_solicitado − valor_reembolsavel − valor_pendente_aprovacao` |
| `totais.itens_por_status` | objeto | Contagem de itens por status (os 5 status sempre presentes) |

**Exemplo** — entrada com período 2026-07-01 a 2026-07-31 e duas despesas:
`a-1` alimentação de 72,50 em 03/07 com nota, e `a-2` alimentação de 38,00 no mesmo dia.

```json
{
  "versao_schema": "2.0",
  "politica": "v4",
  "tabela_de_limites": "padrao",
  "colaborador": {"id": "c-1"},
  "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
  "itens": [
    {"id": "a-1", "data": "2026-07-03", "categoria": "alimentacao", "moeda": "BRL",
     "valor_informado": "72.50", "taxa_cambio": null, "data_cotacao": null, "valor_considerado": "72.50", "valor_reembolsavel": "60.00",
     "status": "parcial",
     "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009",
                  "mensagem": "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 60.00. Glosados R$ 12.50."}]},
    {"id": "a-2", "data": "2026-07-03", "categoria": "alimentacao", "moeda": "BRL",
     "valor_informado": "38.00", "taxa_cambio": null, "data_cotacao": null, "valor_considerado": "38.00", "valor_reembolsavel": "0.00",
     "status": "recusado",
     "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009",
                  "mensagem": "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 0.00. Glosados R$ 38.00."}]}
  ],
  "totais": {"valor_solicitado": "110.50", "valor_reembolsavel": "60.00",
             "valor_pendente_aprovacao": "0.00", "valor_glosado": "50.50",
             "itens_por_status": {"aprovado": 0, "parcial": 1, "recusado": 1, "ignorado": 0,
                                  "pendente_aprovacao": 0}}
}
```

### 4.3 Entrada inválida

Se a entrada não for JSON válido, faltar campo obrigatório, um campo tiver tipo
errado, uma data não estiver no formato `AAAA-MM-DD`, ou `periodo.inicio` for
posterior a `periodo.fim`, o sistema **não produz arquivo de saída**, informa o
problema (indicando a despesa, quando for o caso) e termina com indicação de erro.
Uma despesa ruim invalida a execução inteira — reembolso parcial de um lote
corrompido é pior que nenhum.
O mesmo vale para a tabela de política (4.4) e a tabela de câmbio (4.5): se faltar
campo, um limite for negativo ou não numérico, uma periodicidade for diferente de
`dia`/`diaria`, ou a moeda base não for `BRL`, nada é calculado (RN-015).

### 4.4 Tabela de política (fornecida pelo financeiro)

Documento separado, no formato de `exemplos/envelope/politica-v4.json`, que muda sem
aviso e por isso **não faz parte do sistema**: é recebido a cada execução; na falta de
indicação, usa-se a cópia vigente mantida junto ao sistema.

| Campo | Significado |
|---|---|
| `versao` | Nome da versão (repassado à saída) |
| `moeda_base` | Deve ser `BRL` |
| `padrao` | Limites por categoria da política padrão: `{categoria: {limite, periodicidade}}` |
| `centros_custo` | Por centro de custo, limites que **substituem** os do padrão para as categorias listadas |
| `…limite` | Valor em BRL, ≥ 0. Zero = categoria não reembolsável naquele centro de custo |
| `…periodicidade` | `dia` (limite da soma do dia, RN-009) ou `diaria` (por diária do item, RN-010) |
| `…observacao` | Texto livre, ignorado |
| `nota_fiscal_obrigatoria_acima_de` | Limiar de nota fiscal em BRL (RN-008) |
| `acrescimo_em_viagem_percentual` | Acréscimo aos limites diários em viagem, em % (RN-011) |
| `vigencia` | Informativo; não restringe datas (AMB-026) |

### 4.5 Tabela de câmbio (fornecida pelo financeiro)

Documento separado, no formato de `exemplos/envelope/cambio.json`: `moeda_base` (deve ser
`BRL`) e `taxas` = `{data: {moeda: BRL por unidade}}`. Só há cotação em dias úteis bancários.

## 5. Regras de negócio

### RN-001 — Validação da entrada

**Regra:** a entrada é validada conforme 4.1 e 4.3 antes de qualquer cálculo.
**Origem:** contrato da interface.
**Aceite:** despesa sem `valor` → nenhuma saída, erro citando o id da despesa;
`valor` igual a `true` → erro; `periodo.inicio = 2026-08-01` com `fim = 2026-07-31` → erro.

### RN-002 — Arredondamento monetário

**Regra:** o `valor` de cada despesa é arredondado para centavos (2 casas) **uma
única vez, na entrada**, pelo critério "meio para cima" (0,005 vai para 0,01; -0,005
vai para -0,01). Todas as regras seguintes usam o valor arredondado (`valor_considerado`).
**Origem:** AMB-010.
**Aceite:** `33.333` → `33.33`; `10.005` → `10.01`; `10.004` → `10.00`.

### RN-003 — Normalização da categoria

**Regra:** a categoria é comparada após remover espaços nas pontas e converter
para minúsculas. A categoria normalizada é a que aparece na saída.
**Origem:** AMB-011.
**Aceite:** `"ALIMENTACAO"`, `" Alimentacao "` e `"alimentacao"` são a mesma categoria `alimentacao`.

### RN-004 — Período de competência

**Regra:** a despesa é elegível somente se `periodo.inicio ≤ data ≤ periodo.fim`
(ambos inclusivos). Fora disso: `recusado`, motivo `FORA_DA_COMPETENCIA`.
Despesa de mês anterior lançada com atraso também é recusada.
**Origem:** política item 7; AMB-008.
**Aceite:** período 01/07–31/07: despesa de 31/07 é avaliada normalmente; de 15/04 é recusada; de 01/08 é recusada.

### RN-005 — Valor não positivo (estornos)

**Regra:** despesa com `valor_considerado ≤ 0,00` recebe status `ignorado`,
`valor_reembolsavel = 0,00` e motivo `VALOR_NAO_POSITIVO`. Ela **não abate** o
reembolso de outras despesas, **não consome** limite diário e não entra em
`totais.valor_solicitado`.
**Origem:** AMB-009.
**Aceite:** estorno de −45,00 em transporte no dia 11/07 → `ignorado`; uma corrida
de 80,00 no mesmo dia continua com 80,00 reembolsáveis.

### RN-006 — Categorias da política

**Regra:** só são reembolsáveis as categorias que têm limite na tabela aplicável ao
colaborador (RN-013), após RN-003. Categoria sem limite: `recusado`, motivo
`CATEGORIA_NAO_REEMBOLSAVEL`. Categoria com limite 0,00 na tabela aplicável:
`recusado`, motivo `CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO`.
*(v1.0: lista fixa alimentação, transporte urbano e hospedagem — D-001.)*
**Origem:** política v3 item 9; v4 item A; AMB-012, AMB-018, AMB-019.
**Aceite:** `coworking` de 89,00 com nota → `recusado`, reembolsável 0,00.
`representacao` em CC-COMERCIAL → avaliada (limite 300,00); em centro de custo sem
`representacao` na tabela → `CATEGORIA_NAO_REEMBOLSAVEL`. `hospedagem` em CC-ENG-PLATAFORMA
→ `CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO`.

### RN-007 — Duplicatas

**Regra:** duas despesas são duplicatas quando têm **a mesma data, a mesma
categoria normalizada, o mesmo fornecedor (sem diferenciar maiúsculas e espaços
nas pontas), a mesma moeda e o mesmo valor na moeda da despesa arredondado (RN-002)**. O `id` e a descrição não entram na
comparação. A primeira ocorrência na ordem da entrada é avaliada normalmente; cada
ocorrência seguinte é `recusado`, motivo `DUPLICATA`, citando o id da primeira.
Só participam da comparação despesas que passaram por RN-004, RN-005 e RN-006.
**Origem:** política item 8; AMB-007, AMB-028.
**Aceite:** d-006 e d-007 (09/07, alimentação, Bistro Central, 54,90) → d-006
aprovada, d-007 recusada citando d-006. Mesmo fornecedor e data com valores
54,90 e 54,91 → não são duplicatas.

### RN-008 — Nota fiscal obrigatória

**Regra:** despesa com `valor_considerado` (em BRL) **estritamente maior** que o
limiar da tabela de política (R$ 100,00 na v4) e `tem_nota_fiscal = false` é `recusado`
integralmente, motivo `SEM_NOTA_FISCAL`.
A comparação usa o valor do item já convertido para BRL, não a soma do dia nem o valor após limite.
Exatamente R$ 100,00 sem nota é aceito.
**Origem:** política item 5; AMB-003, AMB-004, AMB-023.
**Aceite:** 100,00 sem nota → segue para os limites; 100,01 sem nota → recusado;
hospedagem de 690,00 sem nota → recusado (não é reembolsado parcialmente até 100).
40,00 USD a 5,50 = 220,00 BRL sem nota → recusado; 14,50 EUR a 5,88 = 85,26 BRL sem nota → aceito.

### RN-009 — Limite diário de alimentação e transporte urbano

**Regra:** para toda categoria com periodicidade `dia` na tabela aplicável (na tabela
padrão v4: `alimentacao` R$ 60,00 e `transporte_urbano` R$ 80,00) o limite
vale para a **soma dos valores em BRL das despesas elegíveis da mesma categoria na mesma data**.
O limite é distribuído entre as despesas daquele dia **na ordem em que aparecem na
entrada**: cada uma recebe `mínimo(valor_considerado, saldo restante do dia)`, e o
saldo diminui do que foi concedido. Despesa que recebe menos que o seu valor é
`parcial` (ou `recusado`, se recebeu 0,00), motivo `LIMITE_DIARIO`. O excedente é
glosado; o item não é recusado por ultrapassar o limite.
Despesas recusadas/ignoradas por regras anteriores não consomem saldo.
Limites de categorias diferentes são independentes entre si.
**Origem:** política itens 1, 2 e 4; AMB-001, AMB-002.
**Aceite:** 03/07: alimentação 72,50 (1ª) e 38,00 (2ª) → 60,00 `parcial` e 0,00
`recusado`. Alimentação de 61,00 sozinha → 60,00 `parcial`. Alimentação 30,00 +
40,00 → 30,00 `aprovado` e 30,00 `parcial`.

### RN-010 — Limite de hospedagem por diária

**Regra:** categoria com periodicidade `diaria` (hospedagem; R$ 250,00 no padrão v4) tem
limite **por diária**. O número de diárias de uma despesa dessa categoria é o número inteiro que aparece na descrição seguido
das palavras "diária(s)" ou "noite(s)" (com ou sem acento, sem diferenciar
maiúsculas). Se a descrição não indicar, ou indicar zero, considera-se **1 diária**.
O limite do item é `limite × diárias`. Cada despesa de hospedagem é limitada
individualmente (não há agregação por data). Acima do limite: `parcial`, motivo `LIMITE_HOSPEDAGEM`.
**Origem:** política itens 3 e 4; AMB-006.
**Aceite:** "Hotel Rio - 2 diarias", 480,00 → limite 500,00 → `aprovado` 480,00.
"Pousada", 310,00 → 1 diária → `parcial` 250,00. "Airbnb 3 noites", 690,00 com
nota → limite 750,00 → `aprovado`.

### RN-011 — Colaborador em viagem

**Regra:** uma data é **dia em viagem** quando (a) está coberta por alguma despesa de
hospedagem da entrada com valor > 0 e data dentro do período, **ou** (b) há na entrada
alguma despesa com valor > 0, data dentro do período e moeda diferente de `BRL` naquela data
(viagem internacional — v4 item B). Uma
hospedagem com data D e N diárias (RN-010) cobre os dias **D até D+N, inclusive**
(as noites mais o dia do check-out). A hospedagem cobre os dias mesmo que ela própria
seja recusada (por exemplo, por falta de nota): a ausência de nota impede o reembolso
da diária, não desfaz o fato de que houve viagem.
Em dia em viagem os limites das categorias de periodicidade `dia` são ampliados pelo
percentual da tabela (50% na v4: 60,00 → 90,00; 80,00 → 120,00; 75,00 → 112,50), arredondado
para centavos. Limites de periodicidade `diaria` (hospedagem) **não** são ampliados.
**Origem:** política item 6; v4 item B; AMB-005, AMB-013, AMB-024, AMB-025.
**Aceite:** hospedagem em 14/07 com 2 diárias → 14, 15 e 16/07 são dias em viagem;
alimentação de 85,00 em 15/07 → `aprovado`; alimentação de 85,00 em 17/07 → 60,00 `parcial`.
Despesa em EUR em 14/07 → 14/07 é dia em viagem para todas as despesas daquele dia.

### RN-012 — Status, motivos e totais

**Regra:** cada item recebe exatamente um status:

| Status | Quando |
|---|---|
| `ignorado` | RN-005 |
| `recusado` | RN-004, RN-006, RN-007, RN-008, RN-014, ou limite que deixou 0,00 |
| `parcial` | 0,00 < reembolsável < valor considerado |
| `aprovado` | reembolsável = valor considerado |
| `pendente_aprovacao` | RN-016 (prevalece sobre `aprovado`/`parcial`) |

Códigos de motivo: `FORA_DA_COMPETENCIA` (RN-004), `VALOR_NAO_POSITIVO` (RN-005),
`CATEGORIA_NAO_REEMBOLSAVEL` e `CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO` (RN-006),
`DUPLICATA` (RN-007), `SEM_NOTA_FISCAL` (RN-008), `LIMITE_DIARIO` (RN-009),
`LIMITE_HOSPEDAGEM` (RN-010), `MOEDA_SEM_COTACAO` (RN-014), `APROVACAO_MANUAL` (RN-016).
Uma despesa encerrada por uma regra (recusada ou ignorada) não é avaliada pelas
regras seguintes — portanto tem um único motivo. Totais conforme 4.2.
**Origem:** necessidade de justificar cada decisão (seção 2).
**Aceite:** ver seção 9.

### RN-013 — Tabela de limites por centro de custo

**Regra:** a tabela aplicável ao colaborador é montada assim: parte-se dos limites
do `padrao`; se `colaborador.centro_custo` (comparado exatamente como escrito) tem entrada
em `centros_custo`, cada categoria listada nessa entrada **substitui ou acrescenta**
o limite do padrão; categorias do padrão não listadas no centro de custo continuam valendo.
Centro de custo ausente, vazio ou sem entrada na tabela → apenas o padrão; a saída
informa `tabela_de_limites: "padrao"`.
**Origem:** v4 item A; AMB-016, AMB-017.
**Aceite:** CC-COMERCIAL: alimentação 90,00, transporte 150,00, hospedagem 400,00,
representação 300,00. CC-ADM: alimentação 45,00, transporte 60,00 e hospedagem 250,00
(herdada do padrão). CC-SUPORTE-N2: padrão (60/80/250), sem representação.

### RN-014 — Moeda e conversão para BRL

**Regra:** a moeda é normalizada (sem espaços nas pontas, maiúsculas); ausente ou
vazia é `BRL`. Despesa em `BRL` não é convertida. Para outra moeda, usa-se a cotação
da **data da despesa** na tabela de câmbio; se não houver cotação nessa data, usa-se a
cotação da data mais recente **anterior**, desde que no máximo 7 dias corridos antes.
`valor_considerado = valor informado (sem arredondar) × cotação`, arredondado uma
única vez para centavos (meio para cima). Sem cotação aplicável (moeda ausente da tabela,
ou nenhuma cotação nos 7 dias anteriores): `recusado`, motivo `MOEDA_SEM_COTACAO`,
`valor_considerado` nulo. A conversão acontece depois da verificação de duplicata e antes
da nota fiscal (seção 8). Limites e limiar de nota são sempre comparados em BRL.
**Origem:** v4 item B; AMB-020, AMB-021, AMB-022, AMB-029.
**Aceite:** 22,00 EUR em 14/07 (5,93) → 130,46. 30,00 EUR em 18/07 (sábado, sem cotação)
→ cotação de 17/07 (5,96) → 178,80, `data_cotacao` 2026-07-17. 55,00 GBP → `MOEDA_SEM_COTACAO`.
Despesa em USD em 2026-07-05 (tabela começa em 13/07) → `MOEDA_SEM_COTACAO`.

### RN-015 — Validação das tabelas de política e câmbio

**Regra:** as duas tabelas são validadas conforme 4.3–4.5 antes de qualquer cálculo;
problema em qualquer uma interrompe a execução como em RN-001.
**Origem:** v4 item A ("ler a política de fora").
**Aceite:** tabela com `periodicidade: "semana"` → erro; limite `-10` → erro; câmbio com
`moeda_base: "USD"` → erro.

### RN-016 — Aprovação manual acima de R$ 500,00

**Regra:** depois de todos os limites, um item com `valor_reembolsavel` **estritamente
maior** que R$ 500,00 recebe status `pendente_aprovacao` e motivo `APROVACAO_MANUAL`;
o valor reembolsável é mantido (é o que será pago se o gestor aprovar) e é somado em
`totais.valor_pendente_aprovacao`, não em `totais.valor_reembolsavel`. O limiar é por
item e fixo nesta spec (a tabela do financeiro não o traz).
**Origem:** v4 item C; AMB-027.
**Aceite:** hospedagem de 1.200,00 com 3 noites em CC-COMERCIAL (limite 1.200,00) →
`pendente_aprovacao`, 1.200,00. Item com reembolsável de exatamente 500,00 → `aprovado`.
Hospedagem de 1.000,00 sem nº de diárias em CC-COMERCIAL → limite 400,00 → `parcial`.

---

## 6. Ambiguidades identificadas e decisões

### AMB-001 — "Por dia" é por despesa ou por dia? *(unidade de aplicação)*

**Texto original do RH:** "Alimentação tem limite de R$ 60 por dia."
**O que não está claro:** se o limite vale para cada despesa ou para a soma do dia;
e, se for a soma, dia de calendário ou janela de 24 h.
**Decisão:** soma das despesas elegíveis da mesma categoria na mesma data de calendário.
**Justificativa:** "por dia" quer dizer um teto diário; aplicar por despesa permitiria contornar o limite fracionando a conta.
**Regra afetada:** RN-009

### AMB-002 — Como distribuir o limite entre despesas do mesmo dia? *(unidade de aplicação)*

**Texto original do RH:** "Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** com 72,50 + 38,00 no mesmo dia, qual item é cortado:
proporcional, o maior, o último?
**Decisão:** ordem da entrada; cada item consome o saldo restante.
**Justificativa:** regra determinística e explicável item a item ao colaborador; o total pago é o mesmo em qualquer critério.
**Regra afetada:** RN-009

### AMB-003 — "Reembolsadas parcialmente": corta ou recusa? *(fronteira)*

**Texto original do RH:** "Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** se paga até o limite e glosa o excedente, ou se paga uma fração arbitrária.
**Decisão:** paga até o limite e glosa o excedente; nunca recusa o item por exceder.
**Justificativa:** é a leitura literal de "parcialmente" e a prática mais comum de política de despesas.
**Regra afetada:** RN-009, RN-010

### AMB-004 — "Acima de R$ 100": exatamente 100 precisa de nota? Sobre qual valor? *(fronteira)*

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** se 100,00 está incluído; se a comparação é sobre o valor
do item, a soma do dia ou o valor depois do limite; e o que acontece sem nota (recusa
total ou paga até 100).
**Decisão:** estritamente maior que 100,00, sobre o valor do item já arredondado; sem nota, recusa integral.
**Justificativa:** "acima de" exclui o próprio valor; a nota é exigência de comprovação do gasto inteiro, e pagar até 100 sem comprovante incentivaria lançar sem nota.
**Regra afetada:** RN-008

### AMB-005 — O que caracteriza "em viagem"? *(dado ausente)*

**Texto original do RH:** "Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** a entrada não tem campo de viagem nem de destino.
**Decisão:** dia em viagem é aquele coberto por uma hospedagem lançada no período (RN-011).
**Justificativa:** é a única evidência objetiva de viagem disponível nos dados; usar a descrição ("Hotel Rio") ou o fornecedor seria adivinhação.
**Regra afetada:** RN-011

### AMB-006 — Quantas diárias tem uma hospedagem? *(dado ausente)*

**Texto original do RH:** "Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** a entrada não traz número de diárias; d-010 diz "2 diarias" e d-013 "3 noites" apenas na descrição.
**Decisão:** extrair "N diária(s)/noite(s)" da descrição; ausente ou zero, 1 diária.
**Justificativa:** a informação existe nos dados e ignorá-la puniria quem a informou; o padrão de 1 diária é o mais conservador.
**Regra afetada:** RN-010, RN-011

### AMB-007 — "Duplicatas devem ser tratadas": o que é duplicata e o que fazer? *(unidade de aplicação)*

**Texto original do RH:** "Duplicatas devem ser tratadas."
**O que não está claro:** o critério de igualdade (ids diferentes? descrição?) e o tratamento (recusar todas, pagar uma, sinalizar).
**Decisão:** mesma data + categoria + fornecedor + valor; paga a primeira, recusa as demais citando a original.
**Justificativa:** ids diferentes com o resto igual (d-006/d-007) é o padrão típico de lançamento em dobro; recusar ambas puniria o gasto legítimo.
**Regra afetada:** RN-007

### AMB-008 — Período de competência: limites inclusivos e lançamento atrasado *(fronteira)*

**Texto original do RH:** "Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** "lançadas" fala da data de lançamento, que a entrada não
tem; se 31/07 está dentro; o que fazer com a despesa de abril lançada em julho (d-008).
**Decisão:** compara a **data da despesa** com o período, inclusivo nas duas pontas; fora dele, recusa.
**Justificativa:** a data da despesa é o único dado disponível; competência existe justamente para não reabrir meses fechados.
**Regra afetada:** RN-004

### AMB-009 — Valor negativo (estorno) *(dado ausente)*

**Texto original do RH:** a política não fala de estornos.
**O que não está claro:** d-009 (−45,00) deve abater do total, abater do limite do dia, ou ser ignorado?
**Decisão:** ignorado, sem abater nada; registrado com motivo.
**Justificativa:** um estorno sem vínculo com a despesa original não permite saber o que ele corrige; abater às cegas pode reduzir um reembolso legítimo.
**Regra afetada:** RN-005

### AMB-010 — Arredondamento de valores com mais de 2 casas *(fronteira)*

**Texto original do RH:** a política não fala de arredondamento; d-011 vale 33,333.
**O que não está claro:** truncar ou arredondar; em que momento; qual critério no meio.
**Decisão:** arredondar meio-para-cima para centavos, uma vez, na entrada.
**Justificativa:** é o critério que o colaborador espera de uma calculadora; arredondar só uma vez evita diferenças acumuladas.
**Regra afetada:** RN-002

### AMB-011 — Categoria escrita de forma diferente *(fronteira)*

**Texto original do RH:** "Categorias fora da política não são reembolsáveis."
**O que não está claro:** "ALIMENTACAO" (d-014) é categoria fora da política ou erro de digitação?
**Decisão:** maiúsculas/minúsculas e espaços nas pontas não diferenciam categoria; acentos e grafias diferentes, sim.
**Justificativa:** a diferença de caixa não muda o significado; aceitar grafias livres exigiria adivinhar intenção.
**Regra afetada:** RN-003

### AMB-012 — Quais categorias estão "na política"? *(unidade de aplicação)*

**Texto original do RH:** "Categorias fora da política não são reembolsáveis."
**O que não está claro:** a política nunca lista as categorias; coworking (d-005) é parecido com hospedagem?
**Decisão:** estão na política apenas as três que têm limite definido: alimentação, transporte urbano, hospedagem.
**Justificativa:** categoria sem limite não tem como ser avaliada; estender por analogia seria criar política.
**Regra afetada:** RN-006

### AMB-013 — O acréscimo de 50% vale para hospedagem? *(unidade de aplicação)*

**Texto original do RH:** "Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** "limites" inclui o de hospedagem?
**Decisão:** não; apenas alimentação e transporte urbano.
**Justificativa:** como viagem é caracterizada pela própria hospedagem (AMB-005), toda hospedagem estaria "em viagem" e o limite de 250 nunca seria aplicado.
**Regra afetada:** RN-011

### AMB-014 — Fim de semana e plantão *(unidade de aplicação)*

**Texto original do RH:** a política não fala de dia da semana; d-012 é "Almoco de sabado - plantao".
**O que não está claro:** se despesa de fim de semana tem regra diferente.
**Decisão:** sem distinção por dia da semana.
**Justificativa:** a política não restringe; inventar restrição negaria reembolso sem base.
**Regra afetada:** RN-009 (aplicação normal)

### AMB-015 — Ordem de aplicação das regras *(unidade de aplicação)*

**Texto original do RH:** a política lista as regras sem dizer qual prevalece.
**O que não está claro:** uma despesa duplicada e sem nota é recusada por qual motivo? Despesa sem nota consome limite?
**Decisão:** ordem fixa da seção 8; a primeira regra que recusa encerra a avaliação.
**Justificativa:** ordem fixa torna o resultado reproduzível e o motivo único.
**Regra afetada:** RN-012

### AMB-016 — "Aplica-se a política padrão": centro de custo sem entrada *(dado ausente)*

**Texto original do RH (v4):** "Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a política padrão."
**O que não está claro:** o que conta como "sem entrada" (campo ausente? vazio? grafia diferente?) e se o padrão é a v3 ou o bloco `padrao` da tabela.
**Decisão:** centro de custo ausente, vazio ou não encontrado **exatamente** como escrito → bloco `padrao` da tabela recebida.
**Justificativa:** o padrão da v4 é o que o financeiro mantém hoje; comparar exatamente evita "adivinhar" que `cc-comercial` é `CC-COMERCIAL`.
**Regra afetada:** RN-013

### AMB-017 — Centro de custo com entrada, mas sem a categoria *(unidade de aplicação)*

**Texto original do RH (v4):** "Cada centro de custo tem a sua tabela." (CC-ADM não lista hospedagem.)
**O que não está claro:** se a tabela do centro de custo é completa (hospedagem ausente = não reembolsa) ou é uma lista de exceções ao padrão.
**Decisão:** lista de exceções: categoria ausente no centro de custo herda o limite do padrão.
**Justificativa:** quando o financeiro quis proibir uma categoria (CC-ENG-PLATAFORMA/hospedagem) escreveu limite 0 explicitamente — logo, ausência não significa proibição.
**Regra afetada:** RN-013

### AMB-018 — Limite 0,00 *(fronteira)*

**Texto original do RH (v4):** "CC-ENG-PLATAFORMA não reembolsa hospedagem de forma alguma." (tabela: limite 0,00)
**O que não está claro:** se é um item `parcial` com 0,00 reembolsável ou recusa por categoria.
**Decisão:** recusa com motivo próprio `CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO`, avaliada junto com a categoria (antes de nota e limite).
**Justificativa:** "de forma alguma" é proibição, não glosa; o colaborador precisa entender que não adianta mandar nota.
**Regra afetada:** RN-006

### AMB-019 — Categoria nova existe só em um centro de custo *(unidade de aplicação)*

**Texto original do RH (v4):** "`CC-COMERCIAL` tem uma categoria nova, `representacao` [...]"
**O que não está claro:** se `representacao` lançada por outro centro de custo (f-003, CC-SUPORTE-N2) cai no padrão ou é recusada.
**Decisão:** recusada (`CATEGORIA_NAO_REEMBOLSAVEL`): o padrão não tem `representacao`.
**Justificativa:** a v3 item 9 continua valendo — categoria sem limite na tabela aplicável está fora da política.
**Regra afetada:** RN-006, RN-013

### AMB-020 — "Taxa da data da despesa" num dia sem cotação *(dado ausente)*

**Texto original do RH (v4):** "A conversão usa a taxa da data da despesa, não a taxa de hoje." (câmbio: "Cotacoes publicadas apenas em dias uteis bancarios")
**O que não está claro:** sábado 18/07 (e-004) e domingo não têm cotação: recusar, usar a anterior, a seguinte ou a média?
**Decisão:** última cotação anterior disponível, até 7 dias corridos antes; além disso, sem cotação.
**Justificativa:** é a prática de PTAX (vale a do último dia útil) e nunca usa informação "do futuro" em relação à despesa; 7 dias cobre feriados prolongados sem aceitar cotação velha.
**Regra afetada:** RN-014

### AMB-021 — Moeda sem cotação na tabela *(dado ausente)*

**Texto original do RH (v4):** "As taxas estão em cambio.json." (e-006 está em GBP, que não existe na tabela)
**O que não está claro:** recusar, deixar pendente, ou tratar o valor como BRL.
**Decisão:** recusar com `MOEDA_SEM_COTACAO` e `valor_considerado` nulo.
**Justificativa:** tratar 55 GBP como 55 BRL seria pagar valor errado com aparência de certo; a recusa justificada é corrigível reenviando com a cotação.
**Regra afetada:** RN-014

### AMB-022 — Arredondamento na conversão *(fronteira)*

**Texto original do RH (v4):** a política não fala de arredondamento na conversão.
**O que não está claro:** arredondar o valor estrangeiro antes de converter, a taxa, ou o produto.
**Decisão:** converter o valor informado sem arredondar e arredondar só o produto em BRL, meio para cima.
**Justificativa:** mantém a regra da AMB-010 (um único arredondamento) e o valor em BRL mais próximo do real.
**Regra afetada:** RN-014, RN-002

### AMB-023 — Limiar de nota fiscal em moeda estrangeira *(fronteira)*

**Texto original do RH (v4):** "Os limites da política são sempre em BRL."
**O que não está claro:** se "acima de R$ 100" de nota fiscal compara o valor na moeda original (14,50 EUR) ou convertido (85,26 BRL).
**Decisão:** convertido para BRL.
**Justificativa:** o limiar está em reais; 99 EUR não é "até R$ 100".
**Regra afetada:** RN-008

### AMB-024 — Viagem internacional sem hospedagem lançada *(dado ausente)*

**Texto original do RH (v4):** "Colaboradores em viagem internacional lançam despesas em moeda estrangeira."
**O que não está claro:** pela RN-011 da v1.0 só hospedagem caracteriza viagem; o Rafael (envelope) tem refeições em Lisboa sem hotel lançado.
**Decisão:** despesa em moeda estrangeira caracteriza o **seu dia** como dia em viagem (não dias vizinhos).
**Justificativa:** o próprio comunicado associa moeda estrangeira a viagem; limitar ao dia da despesa evita estender o benefício sem evidência.
**Regra afetada:** RN-011

### AMB-025 — Acréscimo de viagem para categorias novas *(unidade de aplicação)*

**Texto original do RH (v3 item 6 + v4):** "limites ampliados em 50%" + categoria nova `representacao`.
**O que não está claro:** se `representacao` em viagem tem 300 ou 450.
**Decisão:** o acréscimo vale para toda categoria de periodicidade `dia` (inclusive `representacao`); nunca para `diaria`.
**Justificativa:** generaliza AMB-013 pelo critério que a tabela oferece (periodicidade) em vez de uma lista fixa de nomes.
**Regra afetada:** RN-011

### AMB-026 — Vigência e "retroativa à competência atual" *(fronteira)*

**Texto original do RH (v4):** "Vigência imediata, retroativa à competência atual." (tabela: `vigencia: 2026-07-01`)
**O que não está claro:** se competências anteriores a julho/2026 devem usar a v3.
**Decisão:** o sistema aplica a tabela recebida a qualquer competência; escolher a versão certa é de quem executa.
**Justificativa:** o sistema não recebe tabela histórica; inventar a v3 embutida contradiria "ler a política de fora".
**Regra afetada:** RN-013 (fora de escopo declarado na seção 3)

### AMB-027 — Fila de aprovação: sobre qual valor e qual fronteira *(fronteira)*

**Texto original do RH (v4):** "Itens cujo valor reembolsável passe de R$ 500 não são mais aprovados automaticamente."
**O que não está claro:** valor informado ou reembolsável (após limites); 500,00 exato; se o total do colaborador conta.
**Decisão:** por item, sobre o reembolsável após limites, estritamente maior que 500,00.
**Justificativa:** o texto diz "valor reembolsável" e "passe de"; item, não total, porque a pendência é por item.
**Regra afetada:** RN-016

### AMB-028 — Duplicatas em moedas diferentes *(unidade de aplicação)*

**Texto original do RH:** "Duplicatas devem ser tratadas."
**O que não está claro:** 30 EUR e 178,80 BRL no mesmo fornecedor e dia são duplicata?
**Decisão:** a comparação usa moeda + valor na moeda original; moedas diferentes nunca são duplicata.
**Justificativa:** lançamento em dobro repete o mesmo documento; comparar valores convertidos dependeria da cotação.
**Regra afetada:** RN-007

### AMB-029 — `moeda` com grafia livre *(fronteira)*

**Texto original do RH (v4):** "A entrada agora pode trazer um campo moeda (ISO 4217). Quando ausente, assume-se BRL."
**O que não está claro:** `"eur"`, `" BRL "`, `""` ou `null`.
**Decisão:** sem espaços nas pontas e maiúsculas; vazio ou nulo = `BRL`.
**Justificativa:** mesmo critério da AMB-011 para categoria; vazio carrega a mesma informação que ausente.
**Regra afetada:** RN-014

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Duas refeições no mesmo dia | 72,50 + 38,00 em 03/07 | 60,00 parcial + 0,00 recusado | RN-009 |
| Exatamente no limite de nota | transporte 100,00 sem nota | passa na nota; 80,00 parcial | RN-008, RN-009 |
| Um centavo acima | transporte 100,01 sem nota | recusado `SEM_NOTA_FISCAL` | RN-008 |
| Exatamente no limite diário | alimentação 60,00 | aprovado 60,00 | RN-009 |
| Categoria fora | coworking 89,00 | recusado | RN-006 |
| Duplicata | dois 54,90 iguais, ids diferentes | 1º aprovado, 2º recusado | RN-007 |
| Mês anterior | 15/04 em competência de julho | recusado | RN-004 |
| Último dia do período | 31/07 | avaliado normalmente | RN-004 |
| Estorno | −45,00 | ignorado, não abate | RN-005 |
| Valor zero | 0,00 | ignorado | RN-005 |
| Mais de 2 casas | 33,333 | 33,33 | RN-002 |
| Meio centavo | 10,005 | 10,01 | RN-002 |
| Várias diárias | hospedagem "2 diarias" 480,00 | aprovado (limite 500,00) | RN-010 |
| Hospedagem sem nota | 690,00 sem nota | recusado integralmente | RN-008 |
| Hospedagem sem nº de diárias | 310,00 | 1 diária → 250,00 parcial | RN-010 |
| Dia em viagem | alimentação 85,00 no dia seguinte ao check-in | aprovado (limite 90,00) | RN-011 |
| Dia do check-out | hospedagem 14/07, 2 diárias; refeição 16/07 | ainda em viagem | RN-011 |
| Hospedagem recusada caracteriza viagem | hospedagem sem nota em 22/07 | 22/07+ são dias em viagem | RN-011 |
| Categoria em maiúsculas | "ALIMENTACAO" 61,00 | alimentacao, 60,00 parcial | RN-003, RN-009 |
| Sábado | alimentação 47,20 no sábado | aprovado | AMB-014 |
| Duplicata fora do período | duas cópias de 15/04 | ambas recusadas por competência | RN-004, RN-007 |
| Lista vazia | `despesas: []` | itens vazios, totais 0,00 | RN-012 |
| CC sem entrada | CC-SUPORTE-N2, hospedagem 310,00 | padrão: 250,00 parcial | RN-013 |
| CC herda categoria | CC-ADM, hospedagem 250,00 | padrão: aprovado | RN-013 |
| Categoria bloqueada | CC-ENG-PLATAFORMA, hospedagem | recusado `CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO` | RN-006 |
| Categoria só de outro CC | `representacao` em CC-SUPORTE-N2 | recusado `CATEGORIA_NAO_REEMBOLSAVEL` | RN-006 |
| Sábado em moeda estrangeira | 30 EUR em 18/07 | cotação de 17/07 | RN-014 |
| Moeda sem cotação | 55 GBP | recusado `MOEDA_SEM_COTACAO` | RN-014 |
| Cotação velha demais | USD em 05/07 (tabela começa 13/07) | recusado `MOEDA_SEM_COTACAO` | RN-014 |
| Nota sobre valor convertido | 14,50 EUR sem nota = 85,26 BRL | aceito | RN-008 |
| Moeda estrangeira = viagem | refeição em EUR | limite ampliado naquele dia | RN-011 |
| Reembolsável exatamente 500,00 | hospedagem 500,00, 2 diárias | aprovado | RN-016 |
| Reembolsável acima de 500,00 | hospedagem 1.200,00, 3 noites, CC-COMERCIAL | pendente_aprovacao | RN-016 |

## 8. Ordem de aplicação das regras

Cada despesa passa pelas regras nesta ordem. A primeira que **recusa ou ignora**
encerra a avaliação daquela despesa (motivo único). As regras de limite (passo 9)
não encerram: reduzem o valor reembolsável. A aprovação manual (passo 10) não altera valor.

1. RN-001 / RN-015 — validação da entrada e das tabelas (a execução inteira para se falhar)
2. RN-002 / RN-003 / RN-013 — arredondamento, normalização (categoria e moeda) e escolha da tabela de limites
3. RN-004 — período de competência
4. RN-005 — valor não positivo
5. RN-006 — categoria da tabela aplicável (inclusive limite 0,00)
6. RN-007 — duplicata (entre as despesas que passaram por 3–5)
7. RN-014 — conversão para BRL
8. RN-008 — nota fiscal (sobre o valor em BRL)
9. RN-009 / RN-010 com RN-011 — limites (diário com saldo compartilhado; hospedagem por item)
10. RN-016 — aprovação manual

Consequência: uma despesa recusada por falta de nota não consome o limite do dia,
uma duplicata é recusada como duplicata mesmo que também esteja sem nota ou sem cotação,
e uma hospedagem bloqueada no centro de custo é recusada pela categoria mesmo sem nota.

## 9. Critérios de aceite

### 9.1 Regressão da v3

Com uma tabela de política que contém **apenas** o padrão da v3 (alimentação 60,00/dia,
transporte 80,00/dia, hospedagem 250,00/diária, nota acima de 100,00, acréscimo de 50%,
nenhum centro de custo), `exemplos/despesas-exemplo.json` produz:

- [x] d-001 → `parcial`, 60,00 (`LIMITE_DIARIO`)
- [x] d-002 → `recusado`, 0,00 (`LIMITE_DIARIO`)
- [x] d-003 → `parcial`, 80,00 (`LIMITE_DIARIO`; nota não exigida em 100,00)
- [x] d-004 → `recusado` (`SEM_NOTA_FISCAL`)
- [x] d-005 → `recusado` (`CATEGORIA_NAO_REEMBOLSAVEL`)
- [x] d-006 → `aprovado`, 54,90
- [x] d-007 → `recusado` (`DUPLICATA` de d-006)
- [x] d-008 → `recusado` (`FORA_DA_COMPETENCIA`)
- [x] d-009 → `ignorado` (`VALOR_NAO_POSITIVO`)
- [x] d-010 → `aprovado`, 480,00 (2 diárias, limite 500,00)
- [x] d-011 → `aprovado`, 33,33 (arredondado; dia em viagem)
- [x] d-012 → `aprovado`, 47,20
- [x] d-013 → `recusado` (`SEM_NOTA_FISCAL`)
- [x] d-014 → `parcial`, 60,00, categoria `alimentacao`
- [x] totais: solicitado 1861,84 · reembolsável 815,43 · glosado 1046,41 · status 4 aprovados, 3 parciais, 6 recusados, 1 ignorado

### 9.2 Exemplo original com a tabela v4 (CC-ENG-PLATAFORMA: 75 / 80 / hospedagem 0)

- [ ] d-001 → `aprovado`, 72,50 · d-002 → `parcial`, 2,50 (saldo de 75,00)
- [ ] d-003 → `parcial`, 80,00 · d-004 → `SEM_NOTA_FISCAL`
- [ ] d-010 e d-013 → `recusado` (`CATEGORIA_BLOQUEADA_NO_CENTRO_CUSTO`)
- [ ] d-011 → `aprovado`, 33,33 (d-010 recusada ainda caracteriza viagem: limite 112,50)
- [ ] d-014 → `aprovado`, 61,00
- [ ] totais: solicitado 1861,84 · reembolsável 351,43 · pendente 0,00 · glosado 1510,41 · 5 aprovados, 2 parciais, 6 recusados, 1 ignorado

### 9.3 `exemplos/envelope/despesas-envelope.json` (CC-COMERCIAL)

- [ ] e-001 → `parcial`, 300,00 (representação; 13/07 não é viagem)
- [ ] e-002 → `aprovado`, 130,46 (22 EUR × 5,93; viagem: limite 135,00)
- [ ] e-003 → `aprovado`, 85,26 (14,50 EUR × 5,88; sem nota, abaixo de 100 BRL)
- [ ] e-004 → `parcial`, 135,00 (30 EUR × 5,96 de 17/07 = 178,80)
- [ ] e-005 → `recusado` (`SEM_NOTA_FISCAL`; 40 USD × 5,50 = 220,00)
- [ ] e-006 → `recusado` (`MOEDA_SEM_COTACAO`; GBP)
- [ ] e-007 → `pendente_aprovacao`, 1.200,00 (3 noites × 400,00)
- [ ] e-008 → `aprovado`, 95,00 (23/07 coberto pela hospedagem: limite 135,00)
- [ ] e-009 → `recusado` (`CATEGORIA_NAO_REEMBOLSAVEL`; coworking)
- [ ] e-010 → `aprovado`, 88,00 (sem moeda = BRL; limite 90,00)
- [ ] totais: solicitado 2457,52 · reembolsável 833,72 · pendente 1200,00 · glosado 423,80 · 4 aprovados, 2 parciais, 3 recusados, 1 pendente

### 9.4 `exemplos/envelope/despesas-envelope-cc-desconhecido.json` (CC-SUPORTE-N2 → padrão)

- [ ] f-001 → `aprovado`, 58,00 · f-002 → `parcial`, 250,00
- [ ] f-003 → `recusado` (`CATEGORIA_NAO_REEMBOLSAVEL`; representação fora do padrão)
- [ ] f-004 → `aprovado`, 65,76 (12 USD × 5,48; viagem: limite 120,00)
- [ ] `tabela_de_limites` = `padrao` · totais: solicitado 623,76 · reembolsável 373,76 · glosado 250,00

### 9.5 Gerais

- [x] a saída mantém a ordem da entrada e todos os valores com 2 casas
- [x] entrada inválida não gera arquivo de saída e termina com erro
- [x] executar duas vezes a mesma entrada produz saídas idênticas
- [ ] tabela de política ou de câmbio inválida não gera saída e termina com erro

## 10. O que fica em aberto

- **Ids repetidos na entrada:** não são validados; cada despesa é avaliada como item próprio (RN-007 cobre o caso de conteúdo igual). Decisão provisória por falta de exemplo.
- **Hospedagens sobrepostas** (duas hospedagens diferentes cobrindo a mesma noite): cada uma é limitada sozinha; não há agregação por noite. Ninguém do RH para dizer se isso é fraude ou troca de hotel.
- **Estornos vinculados:** se a entrada um dia trouxer referência à despesa estornada, AMB-009 deve ser revista.
- **Hospedagem antes do período cobrindo dias do período:** não caracteriza viagem (só hospedagens dentro do período contam). Conservador.
- **Cotação em data posterior à despesa** (despesa num domingo, cotação só na segunda): não usada (AMB-020). Se o financeiro preferir a próxima cotação, muda só a RN-014.
- **Viagem internacional em dias sem despesa estrangeira:** um dia em Lisboa pago só em BRL (cartão nacional) não é dia em viagem, a menos que haja hospedagem cobrindo-o.
- **Itens pendentes e duplicata/limite diário:** um item pendente consome o saldo do dia como se aprovado; se o gestor reprovar, outra despesa do mesmo dia não é recalculada.
