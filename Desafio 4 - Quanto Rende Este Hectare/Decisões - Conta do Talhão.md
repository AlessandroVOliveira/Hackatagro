# Decisões · Conta do Talhão (Desafio 4 · IA no Campo e Conectividade)

Respostas do grupo ao formulário de decisões, do problema ao MVP. A raiz que
atacamos: **o custo por talhão já existe (notas, áudios, contas de luz); o que
falta não é o dado, é a captura, porque digitar planilha no campo não acontece.**

---

## Decisão 1 · Problema escolhido

| Pergunta | Resposta |
|---|---|
| Qual desafio você escolheria se tivesse que começar agora? | **Desafio 4 · Quanto Rende Este Hectare** (nosso protótipo: Conta do Talhão). |
| Qual impacto apresentado fez esse desafio parecer importante? | Adubo, água e energia somam **31% do custo** e variam muito entre as áreas; o produtor sabe o total colhido, mas **não o custo nem a margem de cada talhão**. |
| Que conhecimento, experiência ou habilidade você pode trazer? | IA multimodal (leitura de nota, foto e áudio), FastAPI + SQLite, app offline (PWA) e integração com WhatsApp (Evolution API). |

---

## Decisão 2 · Recorte do problema

| Pergunta | Resposta |
|---|---|
| Qual causa o grupo decidiu atacar? | "O produtor não sabe o custo por talhão porque os dados estão espalhados (notas, áudios, contas de luz) e qualquer solução que exija digitar planilha fracassa." |
| Por que esta causa foi priorizada? | **Possibilidade de agir** (o dado já existe; falta capturar) somada ao **impacto** (adubo/água/energia são 31% e variam entre áreas). |
| Qual restrição não pode ser ignorada? | Funcionar com **sinal fraco/offline**, **não exigir digitar planilha** e deixar o **produtor confirmar** cada leitura (a IA só sugere). |
| Quem é o público principal? | O **produtor** que hoje não lança nada por falta de tempo, e o **técnico/agrônomo** que o acompanha. |

> **Síntese:** o produtor enfrenta não saber o custo por talhão, e vamos atacar
> principalmente a **barreira da captura** (ter que digitar planilha),
> respeitando o sinal fraco do campo e deixando o produtor confirmar cada leitura.

---

## Decisão 3 · Resultado esperado

| Pergunta | Resposta |
|---|---|
| O que o público faz hoje com dificuldade? | Não lança nada por falta de tempo: sabe só o total, não qual área dá lucro, e não tem relatório para o banco. |
| O que deveria conseguir fazer melhor? | Saber o **custo e a margem por talhão** e corrigir onde gastou demais, com relatório para o banco na mão. |
| Qual barreira precisa ser removida? | A **captura sem digitar**: registrar por foto ou frase em vez de planilha. |
| Qual resultado percebido mostraria melhora? | **Custo / produtividade** por talhão e uma decisão mais clara sobre cada área. |
| Qual condição mínima a solução precisa respeitar? | Funcionar offline e por WhatsApp (sinal fraco) e deixar o produtor confirmar cada lançamento. |

---

## Decisão 4 · Ideia de solução

| Pergunta | Resposta |
|---|---|
| O que é a solução? | Manda uma **foto da nota** ou uma **frase** e a IA transforma em **custo por talhão**; o produtor confere e salva. Sem planilha. |
| Para quem foi criada? | O produtor que não lança nada hoje e o técnico/agrônomo que o acompanha. |
| Qual decisão fica mais fácil? | **Lançar o custo** (sem planilha) e enxergar o **resultado por talhão**. |
| Por que usaria em vez da forma atual? | Hoje não lança nada; aqui o esforço é tirar uma foto ou mandar um áudio, do jeito que o produtor já se comunica. |
| O que NÃO pretende resolver agora? | Não substitui o contador/ERP, não decide pelo produtor e não puxa a produtividade da colheitadeira ainda. |

### Como funciona em 3 passos

| Passo | O que acontece? | Que valor é gerado? |
|---|---|---|
| 1 | O produtor manda foto da nota, uma frase, a conta de luz ou o romaneio (app offline ou WhatsApp). | O gasto é **capturado sem digitar planilha**, mesmo sem sinal. |
| 2 | A IA lê e rateia por talhão (a conta da bomba é dividida por área); o produtor confere. | Cada gasto vira **custo no talhão certo**, com o humano no controle. |
| 3 | O painel mostra custo, margem e alertas por área, e gera o relatório. | O produtor **vê onde perde** e tem relatório para o banco. |

---

## Decisão 5 · Foco do MVP

| Pergunta | Resposta |
|---|---|
| O que precisamos descobrir primeiro? | Se o produtor **registra sem desistir** e se a **IA acerta a leitura** da nota/frase. |
| Qual ação o usuário precisa realizar no MVP? | Registrar gastos por foto/frase e ver o custo por talhão. |
| Qual parte precisa funcionar de verdade? | A **extração** (foto/frase → rascunho), o **rateio por talhão** e a confirmação do produtor. |
| O que pode ser simulado/manual? | A leitura por IA tem fallback por regras sem credencial; o WhatsApp é opcional; a produtividade entra manual. |
| O que NÃO vamos construir agora? | Produtividade pela colheitadeira, modo técnico multi-cliente e integrações completas. |

---

## Decisão 6 · Nosso MVP (teste)

| Pergunta | Resposta |
|---|---|
| Quem vai testar primeiro? | 5 a 10 produtores de Alegrete + 1 ou 2 agrônomos. |
| O que farão e em qual situação real? | Registram os gastos de uma safra por foto/frase/WhatsApp, sem planilha. |
| Por quanto tempo / quantas vezes? | Ao longo de uma safra ou de algumas semanas de gastos reais. |
| Qual UMA medida e qual valor mínimo? | **% que continua registrando sem desistir** (apoiada na taxa de acerto da leitura) — sinal positivo se a maioria mantém o hábito. |
| E a próxima decisão? | Se funcionar: modo técnico (um agrônomo com vários clientes) e produtividade pela colheitadeira. Se não: simplificar ainda mais o registro. |

---

## Decisão 8 · Impacto esperado

| Pergunta | Resposta |
|---|---|
| Qual resultado principal esperamos melhorar? | A **decisão por talhão** (corrigir onde gastou demais) e o **acesso a crédito** (relatório por área para o banco). |
| Qual indicador mostraria essa mudança? | Nº de talhões com custo e margem conhecidos, e a redução do gasto no talhão que disparou alerta. |
| Quem percebe esse ganho primeiro? | O produtor (vê onde perde) e o banco/técnico que o acompanha. |
| Se o teste der sinal positivo, qual o próximo passo? | **Medir impacto** e **buscar parceiro**; e conectar ao Entressafra (Desafio 3), levando o custo real da saca para a decisão de venda. |
