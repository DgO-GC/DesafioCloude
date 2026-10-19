# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** aprovada para implementação · **Última alteração:** 2026-10-18

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
decisão item a item, aplicando a política v3 com as interpretações fixadas nesta spec.

## 3. Fora de escopo

- Não efetua pagamento, não integra com folha nem com sistema contábil.
- Não verifica a autenticidade da nota fiscal — confia no indicador `tem_nota_fiscal`.
- Não processa mais de um colaborador por execução.
- Não consulta despesas de outros períodos (não detecta duplicata entre períodos diferentes).
- Não converte moeda: todos os valores são tratados como reais (BRL).
- Não aplica regras por dia da semana, feriado ou fim de semana.
- Não mantém histórico nem estado entre execuções: mesma entrada, mesma saída.
- Não corrige a entrada: categoria desconhecida, data fora do período etc. viram
  recusas justificadas, não "consertos".
- Não oferece aprovação manual, workflow ou interface gráfica.

## 4. Entrada e saída

### 4.1 Entrada

Um documento JSON no formato de `exemplos/despesas-exemplo.json`.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | texto | Identificador do colaborador | sim |
| `colaborador.nome` | texto | Nome (apenas repassado à saída) | não |
| `colaborador.centro_custo` | texto | Centro de custo (apenas repassado à saída) | não |
| `periodo.competencia` | texto `AAAA-MM` | Mês de competência (apenas repassado) | sim |
| `periodo.inicio` | data `AAAA-MM-DD` | Primeiro dia do período, inclusivo | sim |
| `periodo.fim` | data `AAAA-MM-DD` | Último dia do período, inclusivo | sim |
| `despesas[]` | lista | Despesas a avaliar (pode ser vazia) | sim |
| `despesas[].id` | texto | Identificador da despesa | sim |
| `despesas[].data` | data `AAAA-MM-DD` | Data em que a despesa ocorreu | sim |
| `despesas[].categoria` | texto | Categoria informada pelo colaborador | sim |
| `despesas[].descricao` | texto | Descrição livre | não (vazio) |
| `despesas[].fornecedor` | texto | Fornecedor | não (vazio) |
| `despesas[].valor` | número | Valor em reais; pode ser negativo e ter mais de 2 casas | sim |
| `despesas[].tem_nota_fiscal` | booleano | Se há nota fiscal | sim |

Campos extras são ignorados.

### 4.2 Saída

Um documento JSON. Todo valor monetário é um **texto com exatamente duas casas
decimais e ponto como separador** (ex.: `"60.00"`, `"-45.00"`), para que nenhum
consumidor perca centavos ao ler.

| Campo | Tipo | Significado |
|---|---|---|
| `versao_schema` | texto | Versão deste formato de saída (`"1.0"`) |
| `politica` | texto | Versão da política aplicada (`"v3"`) |
| `colaborador` | objeto | Cópia de `colaborador` da entrada |
| `periodo` | objeto | Cópia de `periodo` da entrada |
| `itens[]` | lista | Uma entrada por despesa, **na mesma ordem da entrada** |
| `itens[].id` | texto | Id da despesa |
| `itens[].data` | texto | Data da despesa |
| `itens[].categoria` | texto | Categoria normalizada (RN-003) |
| `itens[].valor_informado` | texto | Valor exatamente como veio, sem arredondar |
| `itens[].valor_considerado` | monetário | Valor após arredondamento (RN-002) |
| `itens[].valor_reembolsavel` | monetário | Quanto será reembolsado |
| `itens[].status` | texto | `aprovado`, `parcial`, `recusado` ou `ignorado` (RN-012) |
| `itens[].motivos[]` | lista | Justificativas; vazia apenas quando `aprovado` sem ressalvas |
| `itens[].motivos[].codigo` | texto | Código estável do motivo (tabela da RN-012) |
| `itens[].motivos[].regra` | texto | ID da regra desta spec que gerou o motivo |
| `itens[].motivos[].mensagem` | texto | Explicação legível para o colaborador |
| `totais.valor_solicitado` | monetário | Soma de `valor_considerado` dos itens **não** ignorados |
| `totais.valor_reembolsavel` | monetário | Soma de `valor_reembolsavel` |
| `totais.valor_glosado` | monetário | `valor_solicitado − valor_reembolsavel` |
| `totais.itens_por_status` | objeto | Contagem de itens por status (os 4 status sempre presentes) |

**Exemplo** — entrada com período 2026-07-01 a 2026-07-31 e duas despesas:
`a-1` alimentação de 72,50 em 03/07 com nota, e `a-2` alimentação de 38,00 no mesmo dia.

```json
{
  "versao_schema": "1.0",
  "politica": "v3",
  "colaborador": {"id": "c-1"},
  "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
  "itens": [
    {"id": "a-1", "data": "2026-07-03", "categoria": "alimentacao",
     "valor_informado": "72.50", "valor_considerado": "72.50", "valor_reembolsavel": "60.00",
     "status": "parcial",
     "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009",
                  "mensagem": "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 60.00. Glosados R$ 12.50."}]},
    {"id": "a-2", "data": "2026-07-03", "categoria": "alimentacao",
     "valor_informado": "38.00", "valor_considerado": "38.00", "valor_reembolsavel": "0.00",
     "status": "recusado",
     "motivos": [{"codigo": "LIMITE_DIARIO", "regra": "RN-009",
                  "mensagem": "Limite diário de alimentação em 2026-07-03 é R$ 60.00; restavam R$ 0.00. Glosados R$ 38.00."}]}
  ],
  "totais": {"valor_solicitado": "110.50", "valor_reembolsavel": "60.00", "valor_glosado": "50.50",
             "itens_por_status": {"aprovado": 0, "parcial": 1, "recusado": 1, "ignorado": 0}}
}
```

### 4.3 Entrada inválida

Se a entrada não for JSON válido, faltar campo obrigatório, um campo tiver tipo
errado, uma data não estiver no formato `AAAA-MM-DD`, ou `periodo.inicio` for
posterior a `periodo.fim`, o sistema **não produz arquivo de saída**, informa o
problema (indicando a despesa, quando for o caso) e termina com indicação de erro.
Uma despesa ruim invalida a execução inteira — reembolso parcial de um lote
corrompido é pior que nenhum.

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

**Regra:** só são reembolsáveis as categorias `alimentacao`, `transporte_urbano`
e `hospedagem` (após RN-003). Qualquer outra: `recusado`, motivo `CATEGORIA_NAO_REEMBOLSAVEL`.
**Origem:** política item 9; AMB-012.
**Aceite:** `coworking` de 89,00 com nota → `recusado`, reembolsável 0,00.

### RN-007 — Duplicatas

**Regra:** duas despesas são duplicatas quando têm **a mesma data, a mesma
categoria normalizada, o mesmo fornecedor (sem diferenciar maiúsculas e espaços
nas pontas) e o mesmo `valor_considerado`**. O `id` e a descrição não entram na
comparação. A primeira ocorrência na ordem da entrada é avaliada normalmente; cada
ocorrência seguinte é `recusado`, motivo `DUPLICATA`, citando o id da primeira.
Só participam da comparação despesas que passaram por RN-004, RN-005 e RN-006.
**Origem:** política item 8; AMB-007.
**Aceite:** d-006 e d-007 (09/07, alimentação, Bistro Central, 54,90) → d-006
aprovada, d-007 recusada citando d-006. Mesmo fornecedor e data com valores
54,90 e 54,91 → não são duplicatas.

### RN-008 — Nota fiscal obrigatória

**Regra:** despesa com `valor_considerado` **estritamente maior** que R$ 100,00 e
`tem_nota_fiscal = false` é `recusado` integralmente, motivo `SEM_NOTA_FISCAL`.
A comparação usa o valor do item, não a soma do dia nem o valor após limite.
Exatamente R$ 100,00 sem nota é aceito.
**Origem:** política item 5; AMB-003, AMB-004.
**Aceite:** 100,00 sem nota → segue para os limites; 100,01 sem nota → recusado;
hospedagem de 690,00 sem nota → recusado (não é reembolsado parcialmente até 100).

### RN-009 — Limite diário de alimentação e transporte urbano

**Regra:** para `alimentacao` (R$ 60,00) e `transporte_urbano` (R$ 80,00) o limite
vale para a **soma das despesas elegíveis da mesma categoria na mesma data**.
O limite é distribuído entre as despesas daquele dia **na ordem em que aparecem na
entrada**: cada uma recebe `mínimo(valor_considerado, saldo restante do dia)`, e o
saldo diminui do que foi concedido. Despesa que recebe menos que o seu valor é
`parcial` (ou `recusado`, se recebeu 0,00), motivo `LIMITE_DIARIO`. O excedente é
glosado; o item não é recusado por ultrapassar o limite.
Despesas recusadas/ignoradas por regras anteriores não consomem saldo.
Limites de alimentação e de transporte são independentes entre si.
**Origem:** política itens 1, 2 e 4; AMB-001, AMB-002.
**Aceite:** 03/07: alimentação 72,50 (1ª) e 38,00 (2ª) → 60,00 `parcial` e 0,00
`recusado`. Alimentação de 61,00 sozinha → 60,00 `parcial`. Alimentação 30,00 +
40,00 → 30,00 `aprovado` e 30,00 `parcial`.

### RN-010 — Limite de hospedagem por diária

**Regra:** hospedagem tem limite de R$ 250,00 **por diária**. O número de diárias
de uma despesa de hospedagem é o número inteiro que aparece na descrição seguido
das palavras "diária(s)" ou "noite(s)" (com ou sem acento, sem diferenciar
maiúsculas). Se a descrição não indicar, ou indicar zero, considera-se **1 diária**.
O limite do item é `250,00 × diárias`. Cada despesa de hospedagem é limitada
individualmente (não há agregação por data). Acima do limite: `parcial`, motivo `LIMITE_HOSPEDAGEM`.
**Origem:** política itens 3 e 4; AMB-006.
**Aceite:** "Hotel Rio - 2 diarias", 480,00 → limite 500,00 → `aprovado` 480,00.
"Pousada", 310,00 → 1 diária → `parcial` 250,00. "Airbnb 3 noites", 690,00 com
nota → limite 750,00 → `aprovado`.

### RN-011 — Colaborador em viagem

**Regra:** uma data é **dia em viagem** quando está coberta por alguma despesa de
hospedagem da entrada com `valor_considerado > 0` e data dentro do período. Uma
hospedagem com data D e N diárias (RN-010) cobre os dias **D até D+N, inclusive**
(as noites mais o dia do check-out). A hospedagem cobre os dias mesmo que ela própria
seja recusada (por exemplo, por falta de nota): a ausência de nota impede o reembolso
da diária, não desfaz o fato de que houve viagem.
Em dia em viagem os limites diários de `alimentacao` e `transporte_urbano` são
ampliados em 50% (90,00 e 120,00). O limite de hospedagem **não** é ampliado.
**Origem:** política item 6; AMB-005, AMB-013.
**Aceite:** hospedagem em 14/07 com 2 diárias → 14, 15 e 16/07 são dias em viagem;
alimentação de 85,00 em 15/07 → `aprovado`; alimentação de 85,00 em 17/07 → 60,00 `parcial`.

### RN-012 — Status, motivos e totais

**Regra:** cada item recebe exatamente um status:

| Status | Quando |
|---|---|
| `ignorado` | RN-005 |
| `recusado` | RN-004, RN-006, RN-007, RN-008, ou limite que deixou 0,00 |
| `parcial` | 0,00 < reembolsável < valor considerado |
| `aprovado` | reembolsável = valor considerado |

Códigos de motivo: `FORA_DA_COMPETENCIA` (RN-004), `VALOR_NAO_POSITIVO` (RN-005),
`CATEGORIA_NAO_REEMBOLSAVEL` (RN-006), `DUPLICATA` (RN-007), `SEM_NOTA_FISCAL` (RN-008),
`LIMITE_DIARIO` (RN-009), `LIMITE_HOSPEDAGEM` (RN-010).
Uma despesa encerrada por uma regra (recusada ou ignorada) não é avaliada pelas
regras seguintes — portanto tem um único motivo. Totais conforme 4.2.
**Origem:** necessidade de justificar cada decisão (seção 2).
**Aceite:** ver seção 9.

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

## 8. Ordem de aplicação das regras

Cada despesa passa pelas regras nesta ordem. A primeira que **recusa ou ignora**
encerra a avaliação daquela despesa (motivo único). As regras de limite (7 e 8)
não encerram: reduzem o valor reembolsável.

1. RN-001 — validação (a execução inteira para se falhar)
2. RN-002 / RN-003 — arredondamento e normalização da categoria
3. RN-004 — período de competência
4. RN-005 — valor não positivo
5. RN-006 — categoria da política
6. RN-007 — duplicata (entre as despesas que passaram por 3–5)
7. RN-008 — nota fiscal
8. RN-009 / RN-010 com RN-011 — limites (diário com saldo compartilhado; hospedagem por item)

Consequência: uma despesa recusada por falta de nota não consome o limite do dia,
e uma duplicata é recusada como duplicata mesmo que também esteja sem nota.

## 9. Critérios de aceite

O sistema está pronto quando, para `exemplos/despesas-exemplo.json`:

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
- [x] a saída mantém a ordem da entrada e todos os valores com 2 casas
- [x] entrada inválida não gera arquivo de saída e termina com erro
- [x] executar duas vezes a mesma entrada produz saídas idênticas

## 10. O que fica em aberto

- **Ids repetidos na entrada:** não são validados; cada despesa é avaliada como item próprio (RN-007 cobre o caso de conteúdo igual). Decisão provisória por falta de exemplo.
- **Hospedagens sobrepostas** (duas hospedagens diferentes cobrindo a mesma noite): cada uma é limitada sozinha; não há agregação por noite. Ninguém do RH para dizer se isso é fraude ou troca de hotel.
- **Estornos vinculados:** se a entrada um dia trouxer referência à despesa estornada, AMB-009 deve ser revista.
- **Hospedagem antes do período cobrindo dias do período:** não caracteriza viagem (só hospedagens dentro do período contam). Conservador.
