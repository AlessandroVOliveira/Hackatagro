# Decisões · Entressafra (Desafio 3 · Novas Cadeias)

Respostas do grupo ao formulário de decisões, do problema ao MVP. A raiz que
atacamos: **na colheita, é a falta de caixa que decide a hora de vender, não o
preço.**

---

## Decisão 1 · Problema escolhido

| Pergunta | Resposta |
|---|---|
| Qual desafio você escolheria se tivesse que começar agora? | **Desafio 3 · Vender na Hora Certa** (nosso protótipo: Entressafra). |
| Qual impacto apresentado fez esse desafio parecer importante? | Com custo perto de **R$ 15 mil/ha**, poucos reais por saca separam lucro de prejuízo. A colheita do arroz se concentra em **março e abril**, quando o preço está no piso e as contas vencem. |
| Que conhecimento, experiência ou habilidade você pode trazer? | Análise de séries de preço (CEPEA) e de juros (Banco Central), desenvolvimento do simulador e leitura da realidade do produtor da Campanha gaúcha. |

---

## Decisão 2 · Recorte do problema

| Pergunta | Resposta |
|---|---|
| Qual causa o grupo decidiu atacar? | "A colheita se concentra em março e abril, quando o preço está no ponto mais baixo e as contas vencem; sem armazém e preso a adiantamentos, o produtor vende na pressa." |
| Por que esta causa foi priorizada? | **Possibilidade de agir** (resolve-se com informação + crédito já existente, sem mudar a produção) somada ao **impacto** (poucos reais/saca = lucro ou prejuízo). |
| Qual restrição não pode ser ignorada? | **As contas da colheita precisam ser pagas.** Não adianta só "esperar": a solução tem que mostrar como pagar enquanto espera. |
| Quem é o público principal? | O **produtor de arroz** (e de gado) que vende na colheita por falta de caixa, e quem o aconselha (técnico Emater/Sebrae, cooperativa). |

> **Síntese:** o produtor de arroz enfrenta a venda na pressa durante a colheita
> e vamos atacar principalmente a **falta de caixa que o obriga a vender no pior
> preço**, respeitando que as contas da colheita precisam ser pagas.

---

## Decisão 3 · Resultado esperado

| Pergunta | Resposta |
|---|---|
| O que o público faz hoje com dificuldade? | Vende tudo na colheita, no pior preço, para pagar as contas, sem saber quanto perde nem se vale esperar. |
| O que deveria conseguir fazer melhor? | **Decidir quando e como vender** com base em números: quanto perde vendendo agora, quanto custa esperar e como pagar as contas enquanto espera. |
| Qual barreira precisa ser removida? | A falta de um número claro do **custo da pressa** e o desconhecimento do crédito de estocagem (EGF, CPR, CDA/WA). |
| Qual resultado percebido mostraria melhora? | **Receita / custo** — R$ por saca ganho (ou deixado na mesa) ao escolher a janela de venda. |
| Qual condição mínima a solução precisa respeitar? | Usar **dados reais** (CEPEA/Banco Central), funcionar no celular e sem internet, responder em minutos e ter premissas editáveis. |

---

## Decisão 4 · Ideia de solução

| Pergunta | Resposta |
|---|---|
| O que é a solução? | Um simulador que mostra, **em R$ por saca**, quanto o produtor perde vendendo na colheita e quanto pode ganhar esperando, já descontados custos e juros, e lista como pagar as contas enquanto espera. |
| Para quem foi criada? | O produtor de arroz/gado que vende na colheita por falta de caixa (e seu técnico/cooperativa). |
| Qual decisão fica mais fácil? | **Quando e como vender** a safra, com histórico real no lugar do achismo e da pressão do comprador. |
| Por que usaria em vez da forma atual? | Hoje decide na pressão do adiantamento; o Entressafra mostra o **custo real da pressa** e as alternativas de crédito, em minutos. |
| O que NÃO pretende resolver agora? | Não prevê o preço futuro, não concede crédito e não substitui o banco ou a cooperativa. |

### Como funciona em 3 passos

| Passo | O que acontece? | Que valor é gerado? |
|---|---|---|
| 1 | O produtor informa a safra (área, produtividade, preço de colheita e contas que vencem). | Vê **quanto perde** vendendo tudo agora, em R$ por saca e na safra inteira. |
| 2 | Compara os cenários (vender na colheita, armazenar, financiar a estocagem, venda escalonada) com pior/mediana/melhor ano do histórico. | Vê **quanto custa esperar** e em que mês costuma compensar. |
| 3 | Abre as opções de crédito (EGF, CPR, CDA/WA, custo do adiantamento). | Vê **como pagar as contas** enquanto espera, e decide. |

---

## Decisão 5 · Foco do MVP

| Pergunta | Resposta |
|---|---|
| O que precisamos descobrir primeiro? | Se o produtor **confia no número e muda a decisão** de venda, e se os custos/premissas batem com a realidade local. |
| Qual ação o usuário precisa realizar no MVP? | Informar a safra e ver os três cenários com o veredito (quanto perde / vale esperar / como pagar). |
| Qual parte precisa funcionar de verdade? | O **cálculo do resultado líquido por saca** com dados reais (CEPEA + juros do Banco Central). |
| O que pode ser simulado/manual? | Os custos locais (valores padrão editáveis), a parte de crédito (lista informativa) e o gado (sazonalidade de referência). |
| O que NÃO vamos construir agora? | Previsão de preço, integração com banco/cooperativa e app nativo. |

---

## Decisão 6 · Nosso MVP (teste)

| Pergunta | Resposta |
|---|---|
| Quem vai testar primeiro? | 5 a 10 orizicultores de Alegrete + 2 técnicos (Emater/Sebrae). |
| O que farão e em qual situação real? | Rodar a simulação com a própria safra na janela de colheita (mar/abr) e dizer se mudariam a decisão de venda. |
| Por quanto tempo / quantas vezes? | Em uma oficina ou durante a colheita; cada um roda 1 a 2 cenários próprios. |
| Qual UMA medida e qual valor mínimo? | **% que diz que o número mudaria ou ajudaria a decisão** — sinal positivo se **≥ 60%** (ao menos 6 de 10). |
| E a próxima decisão? | Se atingir: buscar parceria (cooperativa/sindicato) e validar custos. Se não: revisar premissas e a clareza do resultado. |

---

## Decisão 8 · Impacto esperado

| Pergunta | Resposta |
|---|---|
| Qual resultado principal esperamos melhorar? | A **receita do produtor (R$/saca)**, evitando vender no pior momento por falta de caixa. |
| Qual indicador mostraria essa mudança? | R$ por saca ganho ao escolher a melhor janela vs. vender tudo na colheita (no histórico CEPEA, o melhor mês pagou, na mediana, **+18%** sobre mar/abr). |
| Quem percebe esse ganho primeiro? | O **produtor** (mais R$ por saca) e a cooperativa/técnico (melhor comercialização). |
| Se o teste der sinal positivo, qual o próximo passo? | **Buscar parceiro** (cooperativa/sindicato) e testar com mais produtores. |
