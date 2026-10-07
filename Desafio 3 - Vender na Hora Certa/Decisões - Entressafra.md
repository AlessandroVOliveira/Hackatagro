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
| Qual barreira precisa ser removida? | A falta de um número claro do **custo da pressa** e o desconhecimento do crédito de estocagem (FEE/EGF, CPR, CDA/WA). |
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
| 3 | Abre as opções de crédito (FEE/EGF, CPR, CDA/WA, custo do adiantamento). | Vê **como pagar as contas** enquanto espera, e decide. |

---

## Decisão 5 · Foco do MVP

| Pergunta | Resposta |
|---|---|
| Qual hipótese queremos testar? | Mostrar o **custo líquido de esperar** junto com o **crédito de estocagem (FEE/EGF)** faz o produtor mudar a decisão de venda em relação ao que faria sem o app — não é só "ele confia no número", é a combinação conta + crédito que muda o comportamento. |
| Qual função central precisa funcionar de verdade? | O **cálculo do resultado líquido por saca/cabeça** com dados reais (CEPEA arroz e boi + juros do Banco Central), pior/mediana/melhor ano e a recomendação entre os cenários. Já está pronto e testado (14 testes automatizados). |
| O que pode ser simulado/manual agora? | Custos locais (armazenagem, secagem, frete — valores padrão **editáveis**); crédito (FEE/EGF, CPR, CDA/WA — lista informativa, sem integração bancária); validação da hipótese (feita em oficina/entrevista, sem telemetria no app); preço do boi no RS (usa CEPEA/ESALQ-SP como proxy até existir série NESPRO/UFRGS). |
| O que NÃO entra agora? | Previsão de preço futuro, concessão/integração de crédito real, app nativo, armazenagem como restrição física (só citada na narrativa), custo sazonal do gado no inverno, simulação de Pronamp/Pronaf por porte. |

---

## Decisão 6 · Nosso MVP (teste)

| Pergunta | Resposta |
|---|---|
| Quem será o primeiro usuário? | 5 a 10 orizicultores de Alegrete + 2 técnicos (Emater/Sebrae), e agora também **1 a 2 pecuaristas** — a aba Gado ganhou gatilho de caixa (vender parte do lote para cobrir contas) e precisa ser validada, não só o arroz. |
| O que farão e em qual situação real? | Rodar a simulação com a própria safra/lote na janela de colheita (mar/abr) e dizer se mudariam a decisão de venda. |
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
