# Decisões · Ronda do Pampa (Desafio 2 · Invasores do Pampa)

Respostas do grupo ao formulário de decisões, do problema ao MVP. A raiz que
atacamos: **a invasão não respeita a cerca; quem age sozinho e tarde perde.**

---

## Decisão 1 · Problema escolhido

| Pergunta | Resposta |
|---|---|
| Qual desafio você escolheria se tivesse que começar agora? | **Desafio 2 · Invasores do Pampa** (nosso protótipo: Ronda do Pampa). |
| Qual impacto apresentado fez esse desafio parecer importante? | O capim-annoni solta **até 80 mil sementes por planta/ano** e deixa banco de sementes por **mais de 20 anos** no solo; o javali destrói lavoura e campo. E sobra pouca mão de obra para o controle. |
| Que conhecimento, experiência ou habilidade você pode trazer? | App offline (PWA), mapas/geolocalização, modelagem da nota de prioridade, FastAPI, um sensor de armadilha de baixo custo (ESP32) e avisos por WhatsApp. |

---

## Decisão 2 · Recorte do problema

| Pergunta | Resposta |
|---|---|
| Qual causa o grupo decidiu atacar? | "A invasão atravessa as cercas: quem controla sozinho perde porque a reinfestação volta do foco do vizinho, e com pouco tempo e dinheiro não se gasta onde rende mais." |
| Por que esta causa foi priorizada? | **Possibilidade de agir** e **impacto** (eliminar cedo é muito mais barato), com **aderência** (o sindicato já organiza mutirões). |
| Qual restrição não pode ser ignorada? | **Privacidade** (não expor de quem é a terra), funcionar **offline/sem sinal** e **não depender de imagem de satélite**. |
| Quem é o público principal? | O **produtor da Campanha** e a **coordenação do sindicato**, que organiza o mutirão da vizinhança. |

> **Síntese:** o produtor da Campanha enfrenta o avanço do annoni e do javali, e
> vamos atacar principalmente a **falta de coordenação e de prioridade** (agir
> cedo, junto e onde rende mais), respeitando a privacidade e o sinal fraco do campo.

---

## Decisão 3 · Resultado esperado

| Pergunta | Resposta |
|---|---|
| O que o público faz hoje com dificuldade? | Vê os focos, mas não dá conta de tudo: age tarde (quando a mancha já tomou) e sozinho, e a reinfestação volta da divisa. |
| O que deveria conseguir fazer melhor? | Saber **por onde começar** (prioridade) e **agir junto** com os vizinhos, ainda cedo. |
| Qual barreira precisa ser removida? | A falta de visão da vizinhança (cada um só vê o seu) e de um critério de prioridade dentro das horas que tem. |
| Qual resultado percebido mostraria melhora? | **Produtividade / custo** (controle mais barato) e **qualidade** (campo nativo preservado). |
| Qual condição mínima a solução precisa respeitar? | Funcionar offline no celular, respeitar a privacidade e não depender de satélite. |

---

## Decisão 4 · Ideia de solução

| Pergunta | Resposta |
|---|---|
| O que é a solução? | Um **app de vizinhança** que marca os focos no mapa, dá uma **nota de prioridade** (onde gastar primeiro) e **avisa os vizinhos** para agir junto, antes de a mancha se formar. |
| Para quem foi criada? | O produtor da Campanha e a coordenação do sindicato. |
| Qual decisão fica mais fácil? | **Qual foco atacar nesta semana** e **quando acionar os vizinhos**. |
| Por que usaria em vez da forma atual? | Hoje cada um age sozinho e tarde; o app mostra a vizinhança, prioriza e coordena o mutirão. |
| O que NÃO pretende resolver agora? | Não elimina o foco sozinho (não é máquina nem herbicida), não substitui o técnico e não faz o mutirão por ninguém. |

### Como funciona em 3 passos

| Passo | O que acontece? | Que valor é gerado? |
|---|---|---|
| 1 | O produtor registra o foco com foto e ponto no mapa, mesmo sem sinal. | O registro **não se perde** e sobe sozinho quando volta a internet. |
| 2 | Cada foco ganha uma nota de 0 a 100 e vira um plano da semana. | Mostra **onde gastar primeiro** dentro das horas disponíveis. |
| 3 | Os vizinhos num raio recebem o aviso (app e WhatsApp); a armadilha coletiva chama o responsável. | A vizinhança **age junto** e cedo. |

---

## Decisão 5 · Foco do MVP

| Pergunta | Resposta |
|---|---|
| O que precisamos descobrir primeiro? | Se a **nota de prioridade** bate com o que o técnico faria e se os vizinhos **agem a partir dos avisos**. |
| Qual ação o usuário precisa realizar no MVP? | Registrar focos e seguir o plano de prioridade e os avisos. |
| Qual parte precisa funcionar de verdade? | A **nota de prioridade** e os **avisos de vizinhança** (com as regras de privacidade). |
| O que pode ser simulado/manual? | A vizinhança fictícia (dados de exemplo), a pré-triagem da foto por IA (opcional) e o sensor (botão que simula). |
| O que NÃO vamos construir agora? | Satélite (Sentinel-2), registro completo por WhatsApp e integração com o Conta do Talhão. |

---

## Decisão 6 · Nosso MVP (teste)

| Pergunta | Resposta |
|---|---|
| Quem vai testar primeiro? | Uma vizinhança real de Alegrete: o sindicato rural + 6 a 8 propriedades. |
| O que farão e em qual situação real? | Registram focos por algumas semanas e seguem o plano de prioridade e os avisos. |
| Por quanto tempo / quantas vezes? | Algumas semanas, acompanhando ao menos um ciclo de revisita (~60 dias). |
| Qual UMA medida e qual valor mínimo? | **% dos focos prioritários atacados ainda pequenos** (ou nº de ações coordenadas a partir de avisos) — sinal positivo se a maioria do topo da lista for atendida. |
| E a próxima decisão? | Se funcionar: expandir a vizinhança e ligar o registro por WhatsApp. Se não: revisar a nota de prioridade e a frequência dos avisos. |

---

## Decisão 8 · Impacto esperado

| Pergunta | Resposta |
|---|---|
| Qual resultado principal esperamos melhorar? | Controle da invasão **mais cedo e mais barato** e **campo nativo preservado**. |
| Qual indicador mostraria essa mudança? | % de focos atacados ainda pequenos e a queda da reinfestação vinda da divisa. |
| Quem percebe esse ganho primeiro? | O produtor (pasto e lavoura protegidos) e o Pampa (campo nativo de pé). |
| Se o teste der sinal positivo, qual o próximo passo? | **Buscar parceiro** (sindicato/Emater) para expandir a vizinhança. |
