# Decisões · Energia da Porteira (Desafio 1 · Bioeconomia & Energia)

Respostas do grupo ao formulário de decisões, do problema ao MVP. A raiz que
atacamos: **não falta matéria-prima; falta o número (quanto o resíduo vale) e
falta coordenação (juntar o volume dos vizinhos).**

---

## Decisão 1 · Problema escolhido

| Pergunta | Resposta |
|---|---|
| Qual desafio você escolheria se tivesse que começar agora? | **Desafio 1 · Energia da Porteira.** |
| Qual impacto apresentado fez esse desafio parecer importante? | Energia é **7% do custo do arroz (R$ 1.124/ha)** e a água soma mais 9%, enquanto cerca de **1,5 milhão de t de casca/ano** no RS e a palha e o esterco ficam parados. |
| Que conhecimento, experiência ou habilidade você pode trazer? | Desenvolvimento web, modelagem econômica (payback), coeficientes de biomassa (Embrapa/IRGA) e mapas (geolocalização do consórcio). |

---

## Decisão 2 · Recorte do problema

| Pergunta | Resposta |
|---|---|
| Qual causa o grupo decidiu atacar? | "O produtor não sabe quanto resíduo tem nem quanto vale; as usinas exigem escala que uma propriedade não alcança; falta quem junte o volume dos vizinhos." |
| Por que esta causa foi priorizada? | **Possibilidade de agir** (é informação e coordenação, não tecnologia) somada ao **impacto** (energia cara + resíduo parado = renda perdida). |
| Qual restrição não pode ser ignorada? | A solução tem que **funcionar em pequena escala** e só com o resíduo realmente disponível (a casca fica no engenho, não na lavoura). |
| Quem é o público principal? | O **produtor** (orizicultor, pecuarista e engenho pequeno) e o técnico/sindicato que articula o consórcio. |

> **Síntese:** o produtor enfrenta energia cara e resíduo parado, e vamos atacar
> principalmente a **falta de informação (quanto vale) e de coordenação (juntar
> os vizinhos)**, respeitando que a solução precisa funcionar em pequena escala.

---

## Decisão 3 · Resultado esperado

| Pergunta | Resposta |
|---|---|
| O que o público faz hoje com dificuldade? | Paga energia cara e deixa palha, casca e esterco parados, sem saber quanto valem nem como transformá-los em energia ou renda. |
| O que deveria conseguir fazer melhor? | Saber **quanto o resíduo rende por ano** e qual rota se paga, e **juntar vizinhos** para alcançar escala. |
| Qual barreira precisa ser removida? | A falta do número (volume × valor) e a falta de quem junte o volume para chegar à escala. |
| Qual resultado percebido mostraria melhora? | **Custo / receita** — R$/ano de economia na energia ou de renda nova com o resíduo. |
| Qual condição mínima a solução precisa respeitar? | Funcionar em pequena escala, no celular, com coeficientes e preços editáveis e com fontes. |

---

## Decisão 4 · Ideia de solução

| Pergunta | Resposta |
|---|---|
| O que é a solução? | Uma ferramenta que estima o resíduo e **quanto ele vale por ano**, compara as rotas pelo **payback** e **junta os vizinhos no mapa** até atingir a escala de uma rota que se paga. |
| Para quem foi criada? | O produtor de arroz/gado e o engenho pequeno, e o técnico da Emater/Sebrae que os atende. |
| Qual decisão fica mais fácil? | **O que fazer com o resíduo** (vender, briquete, secagem própria, biodigestor) ou entrar num consórcio, com o payback na mão. |
| Por que usaria em vez da forma atual? | Hoje o produtor não tem o número nem com quem juntar; a ferramenta dá os dois em minutos. |
| O que NÃO pretende resolver agora? | Não prevê preço, não concede crédito e não constrói a usina. |

### Como funciona em 3 passos

| Passo | O que acontece? | Que valor é gerado? |
|---|---|---|
| 1 | O produtor responde 5 perguntas (área, produtividade, cabeças, manejo, engenho). | Vê **quanto resíduo gera por ano** e o potencial energético. |
| 2 | A ferramenta compara as rotas (vender, briquete, secagem, biodigestor). | Vê **qual rota se paga** e em quanto tempo (payback por rota). |
| 3 | O mapa soma o volume dos vizinhos num raio. | Vê **quando o grupo atinge a escala** de uma rota compartilhada. |

---

## Decisão 5 · Foco do MVP

| Pergunta | Resposta |
|---|---|
| O que precisamos descobrir primeiro? | Se o produtor **age sobre o número** e se os coeficientes e preços batem com a realidade da região. |
| Qual ação o usuário precisa realizar no MVP? | Rodar o inventário e ver as rotas com payback e o mapa do consórcio. |
| Qual parte precisa funcionar de verdade? | O **cálculo de toneladas e energia** e o **payback por rota**, com coeficientes editáveis. |
| O que pode ser simulado/manual? | As propriedades do mapa (fictícias), os preços de compra (a validar) e a camada de compradores/crédito. |
| O que NÃO vamos construir agora? | Backend, cadastro de compradores reais e a usina compartilhada. |

---

## Decisão 6 · Nosso MVP (teste)

| Pergunta | Resposta |
|---|---|
| Quem vai testar primeiro? | 10 a 15 produtores de Alegrete (orizicultor, pecuarista, engenho) + técnicos. |
| O que farão e em qual situação real? | Rodar o inventário com a própria propriedade e dizer se agiriam sobre o resultado. |
| Por quanto tempo / quantas vezes? | Numa oficina ou visita; cada um roda 1 a 2 cenários próprios. |
| Qual UMA medida e qual valor mínimo? | **% que diz que o número ajudaria a decidir** — sinal positivo se **≥ 60%**. |
| E a próxima decisão? | Se atingir: validar coeficientes com IRGA/Emater e formar o primeiro consórcio com um sindicato. Se não: revisar premissas e a clareza do resultado. |

---

## Decisão 8 · Impacto esperado

| Pergunta | Resposta |
|---|---|
| Qual resultado principal esperamos melhorar? | O **custo de energia** (economia) ou a **renda** com o resíduo, em R$/ano. |
| Qual indicador mostraria essa mudança? | R$/ano economizados ou gerados. No exemplo de 300 ha, cada 10% da conta de energia vale **R$ 33,7 mil/ano**. |
| Quem percebe esse ganho primeiro? | O produtor (conta menor ou renda nova) e o grupo que forma o consórcio. |
| Se o teste der sinal positivo, qual o próximo passo? | **Buscar parceiro** (sindicato/cooperativa) e validar os coeficientes com IRGA/Emater. |
