# Relatório — Desafio SDD

**Aluno:** Diego Castilho · **Repositório:** https://github.com/DgO-GC/DesafioCloude · **Data:** 2026-10-18

> Evidências: hashes de commit (`git log`), arquivos do repo e linhas da sessão exportada
> [`docs/sessions/01-desafio-completo.md`](sessions/01-desafio-completo.md) — citadas como
> **S:L<n>** (abra com `?plain=1#L<n>` no GitHub para ir direto à linha).
>
> Trechos marcados com ✍️ são os que só eu posso responder e completei/revisei à mão
> depois de ler o trabalho do agente.

---

## Lacunas declaradas (antes de tudo)

- **Uma única sessão, num único dia.** Todo o trabalho — spec, implementação, envelope e
  relatório — foi feito numa sessão do Claude Code em 2026-10-18, entre 21:41 e ~22:30.
  O envelope do Dia 2 já estava publicado no gist e eu o entreguei ao agente junto com o
  enunciado. Não simulei os dois dias nem reescrevi datas: os timestamps do `git log` são os reais.
  A rubrica limita a faixa do relatório a 12 nesse caso; prefiro declarar a apostar que não perceberiam.
- **O `/export` não existe no app desktop** (Code tab). Segui o FAQ: converti o transcript
  `.jsonl` de `~/.claude/projects/` em markdown com um script, ocultando diretório pessoal e e-mail.
  O raciocínio interno do modelo não fica legível no transcript e não aparece no export.
- **Commits fora da convenção `T-NNN`:** `2afe83e` (estrutura inicial, pedido pelo README do
  desafio) e `c56839a` (normalização de fim de linha — ver Discernimento, caso 4). Não reescrevi o histórico.
- **Um commit vermelho:** `aae0eed` entrou com um teste falhando, corrigido em `79e917d`
  (Discernimento, caso 2).

---

## Delegação

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | Claude | Pedi que lesse a política, o exemplo e a rubrica e me apresentasse um plano antes de executar (S:L1–L335) |
| Decidir as ambiguidades | Claude propôs 14; eu aprovei em bloco (S:L339) | Achei as propostas defensáveis; o curso deixa claro que não há resposta certa, só decisão registrada |
| Escrever a spec | Claude | Gerada a partir das decisões aprovadas (`7c22173`) |
| Desenhar a arquitetura | Claude | Python stdlib, pipeline de etapas, `Decimal` (`cb42922`) |
| Implementar | Claude | Uma task por commit, testes antes do commit (`e22e2cb`..`eeb426e`) |
| Escrever testes | Claude | Mesmos commits do código |
| Absorver o envelope | Claude, na ordem spec → DECISIONS → plan → tasks → código | `1659340` → `5bb1842` → `9d07198` → `8388d52` → `59ef4f9`.. |

**Onde deleguei e me arrependi:** nas **decisões de ambiguidade**. Aprovei as 14 propostas
numa mensagem só ("Pode executar com as decisões propostas", S:L339). Isso transfere ao modelo
justamente a parte que vale 25 pontos e que o desafio diz ser minha. Ao reler a spec depois,
há decisões que eu talvez tomasse diferente (por exemplo, AMB-006: extrair o número de diárias
da descrição livre é frágil; "1 diária se não disser" pode punir quem esqueceu de escrever).
✍️ Diego: Notei bastante poder, mas ao mesmo tempo uma certa ética da IA ao ser questionada em se passar
por mim, utilizar da desosnestidade baseado no escopo do que propõe o projeto, não foi uma alternativa.
No entanto, seguindo o que foi pedido no prompt inicial, percebi que o cloude pode trabalhar 
de maneira orgânica em identificar o que poderia entrar ou não nmesse relatório final.
Acredito que se pudesse mudar alguma devisão tomada por mim, seria que, ao invés de aprovar as decisões
em um lote só para que depois pudesse analisar tudo, aprovaria em pequenos lotes, entendendo 
passo a passo nas tomadas decisões de acordo com o tema.

**Onde não deleguei e deveria ter delegado:** a revisão. Não usei um segundo agente
(subagente revisor) para ler a spec procurando ambiguidade não resolvida ou teste que testa a
coisa errada — o mesmo agente que escreveu o código escreveu os testes e conferiu os dois.

**Usei subagentes / skills / MCP / hooks?** Não. Uma sessão só, sem subagentes. O CLAUDE.md
do projeto foi preenchido (`eeb426e`, `c65825f`) com as convenções e, depois dos erros
recorrentes de teste, com um aviso específico sobre a interação RN-009/RN-011 (ver Discernimento,
caso 3). O mecanismo que mais funcionou foi um script de commit que roda a suíte e **recusa
o commit se algum teste falhar** — criado depois do caso 2 (S:L2020) e que barrou um commit
de verdade no T-018 (S:L3905).

---

## Descrição

Requisito escolhido: **política item 6 — "Colaborador em viagem tem limites ampliados em 50%."**
Teve três versões.

**Versão 0 (proposta no chat, antes da spec — S:L1–L335, tabela de decisões, linha 5):**
> ```
> O que é "em viagem"? (não há esse campo) → Em viagem = data coberta por uma
> hospedagem lançada; aí o limite sobe 50%
> ```

**Versão 1 (spec 1.0, `7c22173`, RN-011 + AMB-013):**
> ```
> Uma data é dia em viagem quando está coberta por alguma despesa de hospedagem da
> entrada com valor_considerado > 0 e data dentro do período. Uma hospedagem com data D
> e N diárias cobre os dias D até D+N, inclusive [...] mesmo que ela própria seja recusada
> [...] Em dia em viagem os limites diários de alimentacao e transporte_urbano são
> ampliados em 50% (90,00 e 120,00). O limite de hospedagem não é ampliado.
> ```

**Versão final (spec 2.0, `1659340`, RN-011 + AMB-024/AMB-025):**
> ```
> Uma data é dia em viagem quando (a) está coberta por alguma despesa de hospedagem [...]
> ou (b) há na entrada alguma despesa com valor > 0, data dentro do período e moeda
> diferente de BRL naquela data. Em dia em viagem os limites das categorias de
> periodicidade `dia` são ampliados pelo percentual da tabela [...]. Limites de
> periodicidade `diaria` (hospedagem) não são ampliados.
> ```

**O que estava ambíguo:** (1) a entrada não tem campo de viagem (dado ausente); (2) "limites"
no plural — inclui hospedagem?; (3) quais dias a hospedagem cobre (check-out?); (4) se uma
hospedagem recusada ainda prova viagem; (5) na v4, viagem internacional sem hotel lançado.

**Como percebi:**
- V0 → V1: ao escrever a regra, a proposta "o limite sobe 50%" aplicada a *todos* os limites
  criava um círculo — a hospedagem define a viagem, então toda hospedagem estaria em viagem e o
  limite de R$ 250 nunca seria aplicado. Virou a AMB-013. Foi percebido pelo agente ao redigir,
  não por mim.
- V1 → V2: o envelope trouxe o Rafael almoçando em Lisboa sem hotel lançado (e-002, e-003);
  pela V1 esses dias não seriam viagem. E trouxe `representacao` (categoria nova): a lista fixa
  "alimentação e transporte" não dizia nada sobre ela. A V2 troca a lista de nomes pelo critério
  que a tabela oferece (periodicidade).

**Commit da mudança:** `7c22173` (V1), `1659340` (V2); registro em `DECISIONS.md` D-001.

---

## Discernimento

> Honestidade primeiro: **todos os casos abaixo foram erros do agente pegos pelo próprio agente**,
> por teste falhando ou por conferência de conta, durante a execução. Eu não peguei nenhum erro
> lendo diff, porque aprovei o plano e só revisei o resultado no fim. ✍️ Diego: *(se, ao revisar
> o repositório, você encontrar algo errado, registre como Caso 0 — esse seria o caso "humano"
> que a rubrica pede).*

### Caso 1 — Total do aceite somado errado na spec

**O que ele propôs:** na §9 da spec 1.0, "solicitado 2001,84 · glosado 1186,41" para o exemplo.
**Por que estava errado:** a soma dos 13 itens não ignorados é 1861,84; glosado 1046,41.
**Como foi detectado:** o agente refez a soma item a item antes do commit (S:L418 tem o valor
errado no arquivo escrito, S:L449 a correção). O teste de aceite `test_aceite_totais` depois
confirmou 1861,84 contra o motor.
**O que foi feito:** corrigido antes do commit `7c22173`.
**Lição:** número escrito à mão na spec é tão suspeito quanto código — e o teste de aceite que
compara contra ele só ajuda se a spec estiver certa.

### Caso 2 — Teste que testava o Python, não a regra; e commit vermelho

**O que ele propôs:** o teste do exemplo literal da §4.2 montava a entrada com `json.dumps` de
um dicionário Python com `38.00`.
**Por que estava errado:** `json.dumps(38.00)` gera `38.0`, então `valor_informado` saía `"38.0"`
(S:L1993). O motor estava certo — repassa o valor como veio, como a spec manda; o teste é que
fabricava uma entrada que nenhum arquivo real teria.
**Como foi detectado:** a suíte falhou — mas o script de commit usava `| tail -1`, que engole o
código de saída, e **commitou mesmo assim** (`aae0eed`). O agente viu "FAILED" na saída.
**O que foi feito:** teste reescrito com JSON literal (`79e917d`); script endurecido para recusar
commit com teste vermelho (S:L2020). Não reescrevi o histórico.

### Caso 3 — Testes que ignoram a interação entre regras (padrão recorrente, 4 vezes)

**O que ele propôs:** expectativas de teste calculadas olhando **uma regra isolada**:
- `test_rn013_cc_comercial_transporte_150...`: esperava 150,00 para transporte de 160,00, mas a
  hospedagem no mesmo dia tornava o dia "em viagem" (RN-011) → limite 225,00 (S:L3379).
- `test_rn009_hospedagem_com_periodicidade_dia...`: esperava 50,00; a própria hospedagem faz do
  dia viagem e, sendo `dia`, ganha +50% → 175,00 (S:L3504).
- `test_rn014_tabela_de_cambio_alternativa`: conta errada, 10 GBP × 7,00 escrito como 60,00 (S:L3794).
- `test_rn011_moeda_estrangeira_torna_o_dia_viagem`: o item em EUR também era alimentação e
  consumia o saldo do dia (RN-009) → `parcial`, não `aprovado` (S:L3896).
**Por que estava errado:** nos quatro, o código seguia a spec e o teste não.
**Como foi detectado:** teste vermelho → conta à mão → conferência contra a RN. No último, o
script endurecido barrou o commit (S:L3905).
**O que foi feito:** testes corrigidos com comentário explicando a interação; aviso permanente no
`CLAUDE.md` ("hospedagem ou moeda estrangeira no mesmo dia tornam o dia em viagem...").
**Padrão que notei:** o agente erra mais **nas expectativas dos testes** do que no código,
sempre quando duas regras de agregação (saldo diário e viagem) se encontram. O risco inverso —
ajustar o código para passar num teste errado — não aconteceu porque a cada falha a pergunta foi
"o que a spec diz?" antes de "o que muda para ficar verde?".

### Caso 4 — Fim de linha CRLF gravado por edições automatizadas

**O que ele propôs:** editar arquivos com `Path.write_text` em scripts Python.
**Por que estava errado:** no Windows isso grava CRLF; parte do repo ficou com quebras mistas e o
diff da spec 2.0 apareceu como +736/−466 linhas (S:L2590) quando a mudança real era +326/−56.
**Como foi detectado:** o tamanho do diff não combinava com a edição.
**O que foi feito:** `.gitattributes` com `eol=lf` (`c56839a`), conversão da cópia de trabalho,
scripts passaram a gravar bytes; aviso no `CLAUDE.md`. Custo: o diff de `src/` medido de forma
ingênua sobre o envelope dá +556/−343; o real (ignorando CR) é +276/−63.

### Caso 5 — Commit com código morto

`7aee342` (T-006, duplicatas) já incluía a função de nota fiscal, que só foi ligada ao pipeline em
`d12d4af` (T-007). Pequena quebra de rastreabilidade: o código da RN-008 nasceu num commit de outra task.

---

## Diligência

**Procedimento de verificação (do agente, sob as regras do CLAUDE.md):** suíte inteira antes de
todo commit (forçado por script depois do caso 2); teste de aceite que roda a **CLI real** em
subprocesso sobre os arquivos de exemplo; clone limpo em pasta temporária para conferir que o
README roda sem intervenção (S: após T-013 e T-021); cálculo à mão de todos os totais da §9
**antes** de rodar o motor — 14 itens da v3, 14 da v4, 10 do envelope e 4 do CC desconhecido
bateram na primeira execução do aceite.

**Li o diff inteiro em que porcentagem das entregas?** ✍️ Diego: *(seja honesto. Fato verificável:
entre o "pode executar" (S:L339) e o push não houve nenhuma mensagem minha na sessão — a revisão,
se houve, foi depois).*

**O que aceitei sem verificar direito:** as 14 decisões de ambiguidade (aprovadas em bloco) e a
spec 2.0 com as 14 decisões novas da v4, que eu não aprovei individualmente — o agente decidiu
sozinho dentro da autorização "incluindo o envelope".

**Testes: quem escreveu, e como sei que testam a coisa certa?** O mesmo agente que escreveu o
código — o risco que o template aponta. Mitigações que existem de fato: (1) os valores esperados
do aceite foram escritos na spec antes do código; (2) cada teste cita a RN no nome; (3) os 4 casos
do Discernimento mostram testes que falharam contra código certo, ou seja, os testes não foram
escritos "para passar". O que falta: nenhuma pessoa conferiu as expectativas de forma independente.

---

## O envelope

**Quantos arquivos toquei na mão:** **0** arquivos editados por mim. Todos os arquivos foram
editados pelo agente. Da parte do agente, o diff da absorção (`c56839a..8699e0d`, ignorando CR)
ficou assim:

| Área | Arquivos | Linhas |
|---|---|---|
| `src/` | 6 (1 novo: `cambio.py`) | +276 / −63 |
| `tests/` | 12 (6 novos) | +634 / −21 |
| `specs/` | 4 | +488 / −108 |
| `politicas/`, README, CLAUDE.md | 4 | +89 / −14 |

**Quanto tempo levou:** 22:00 (envelope commitado, `1eefe15`) → 22:13 (`8699e0d`), ~13 minutos de
execução do agente; spec + DECISIONS + plan + tasks consumiram 22:00–22:05.

**Absorveu de graça:**
- **Os testes de regra da v3 continuaram passando sem edição** (todos de RN-001 a RN-011): eles usam
  um centro de custo fictício, que cai no `padrao` da v4, que tem os mesmos números da v3. Na T-014
  (troca de constantes por tabela externa) só 1 dos 94 testes caiu, e caiu por contrato (`"v3"` → `"v4"`).
- A lista `ETAPAS` (= §8 da spec) recebeu uma etapa nova (`conversao_cambial`) e uma no fim
  (`aprovacao_manual`) sem reordenar nada.
- `status` derivado (DT-002) absorveu `pendente_aprovacao` com 2 linhas.
- RN-009/RN-010 já decidiam por **periodicidade** e não por nome de categoria — `representacao`
  entrou sem código novo.

**Resistiu:**
- **A assinatura das etapas:** todas recebiam `entrada` e liam `politica.LIMITES` global; viraram
  `ctx` (DT-007). Mudança mecânica, mas tocou todas as funções de `regras.py`.
- **`valor` da despesa era, implicitamente, "em BRL".** Com moeda, o valor considerado passou a
  morar na avaliação (`Avaliacao.valor`), e toda comparação com limite/nota trocou `d.valor` por
  `a.valor`. A spec 1.0 nunca disse "valor em reais"; disse "valor em reais" só na tabela de
  entrada — que não foi lida como regra.
- **Contrato de saída:** 4 testes antigos tiveram asserts editados por mudança de schema/status
  (`test_rn012_exemplo_literal_da_secao_4_2`, `test_rn012_contagem_...` — renomeado de "quatro" para
  "cinco status" —, `test_rn010_noites_com_nota_dentro_do_limite`, `test_aceite_totais`), todos
  justificados em D-001; os 17 testes de aceite do exemplo passaram a rodar com uma tabela v3 de
  fixture (DT-009) sem mudar nenhuma expectativa de item.

**Ordem em que fiz:** spec → DECISIONS → plan → tasks → código, confirmável pelos timestamps:
`1659340` 22:04, `5bb1842` 22:04, `9d07198` 22:05, `8388d52` 22:05, primeiro código `59ef4f9` 22:07.

**Se eu tivesse escrito a spec original sabendo desta mudança:** teria escrito a RN-009/RN-010 em
termos de "tabela de limites" desde o início e declarado que todo valor é "valor na moeda da
despesa" vs "valor considerado em BRL" — a distinção que mais custou na absorção.

**O que a spec me poupou, em concreto:** a §8 (ordem das regras) respondeu sozinha onde encaixar a
conversão — depois da duplicata (que compara documentos) e antes da nota (que compara em BRL).
Sem essa seção, a pergunta "duplicata em GBP sem cotação é recusada por quê?" viraria debate.

**Medição de reexecução (bônus da rubrica):** 0 tasks antigas foram reexecutadas; 8 novas
(T-014..T-021) foram criadas e executadas a partir da spec 2.0. Dos 94 testes antigos, 90 ficaram
com as expectativas intactas e 4 tiveram asserts editados por contrato; testes novos: 89. Total final: 183.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Pelo que vi aqui: qualquer projeto com regra
de negócio ambígua e uma segunda rodada de requisito. A §8 e as AMB-* pagaram a conta já no envelope.

**Para qual não valeria?** ✍️ Diego.

**O que eu faria diferente:** decidir eu mesmo as ambiguidades, uma a uma, antes de deixar o agente
escrever a spec; e abrir uma segunda sessão (ou subagente) só para revisar testes contra a spec.

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:** ✍️ Diego. *(Sugestão de
partida, se for verdade para você: "consegui entregar um desafio sobre processo sem participar do
processo — o que mostra quanto o processo depende de eu decidir estar nele.")*
