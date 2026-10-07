# HackatAgro × Sebrae RS · Alegrete/RS

Repositório da equipe para o HackatAgro. Avaliamos três desafios e escolhemos o **Desafio 3: Vender na Hora Certa**.

## Proposta escolhida: Hora Certa

> Simulador de comercialização que mostra, em R$ por saca e por cabeça, o custo de vender por falta de caixa.

**Pergunta do desafio:** como podemos ajudar o produtor a escolher quando e como vender o arroz e o gado, para que a falta de dinheiro deixe de decidir por ele?

### O problema

A colheita do arroz se concentra em março e abril, justamente quando o preço está no ponto mais baixo do ano e as contas vencem. Sem secador nem armazém próprio, e muitas vezes preso a adiantamentos, o produtor vende na pressa. No gado acontece o mesmo: ele vende quando falta dinheiro, não quando o preço está bom.

O produtor não enxerga quanto custa vender na pressa. Com custo de produção perto de R$ 15 mil/ha (cerca de R$ 88/saca), poucos reais por saca separam lucro de prejuízo.

### A solução

Um simulador simples (página web ou bot de mensagens) que responde três perguntas:

1. **Quanto eu perco vendendo agora?** Compara o preço da colheita com o histórico dos meses seguintes (indicador CEPEA/Esalq do arroz em casca no RS) e mostra o melhor, o médio e o pior cenário.
2. **Quanto custa esperar?** Desconta armazenagem e secagem de terceiros, quebra técnica, frete e custo do dinheiro (juros ou CDI perdido).
3. **Como eu pago as contas enquanto espero?** Mostra as alternativas de caixa: EGF do Plano Safra, CPR, CDA/WA e venda parcelada.

O resultado é um plano de venda em R$/saca, por exemplo: *"venda 40% agora para cobrir as contas de abril, financie a estocagem dos outros 60% e venda entre julho e setembro"*.

### Cenários comparados

| Cenário | Como é calculado |
|---|---|
| Vender tudo na colheita | Preço médio histórico de mar/abr (referência) |
| Armazenar e vender na entressafra | Preço do mês-alvo − armazenagem − quebra − juros |
| Financiar a estocagem | Ganho sazonal − juros do financiamento; mostra o caixa liberado na colheita |
| Venda escalonada (ex.: 30/30/40) | Média ponderada dos cenários, reduz o risco de errar o mês |
| Gado: vender agora × segurar N meses | Ganho de peso × preço futuro histórico − custo de manutenção |

### MVP para o dia

- **Dados:** série CEPEA do arroz em casca no RS; preços de boi e terneiro do RS (NESPRO/UFRGS ou Emater); Selic/CDI pela API do Banco Central.
- **Motor de cálculo:** Python + pandas, com sazonalidade mensal (média, mínimo e máximo) e conta líquida de cada cenário.
- **Interface:** Streamlit ou página web com 5 campos (sacas, custo/ha, contas e datas, acesso a armazém, taxa de juros) e gráfico de barras em R$/saca por cenário.
- **Extra:** bot no Telegram que responde "quanto perco vendendo hoje?".

### Riscos

| Risco | Como tratamos |
|---|---|
| Passado não garante preço futuro | Mostrar faixas (melhor, médio, pior ano), nunca uma previsão única |
| Produtor preso a adiantamento | Calcular o custo implícito do adiantamento e comparar com crédito formal |
| Falta de armazém na região | Mapa de armazéns (base Conab) com cálculo de frete |
| Parecer "só uma calculadora" | Pitch focado na decisão e no valor em R$ na safra do produtor |

**Pitch:** vender na colheita tem um preço, e o produtor nunca viu esse número. O Hora Certa mostra quanto vale esperar, em R$ por saca, e como pagar as contas enquanto espera.

Proposta completa: [Proposta - Hora Certa.pdf](<Desafio 3 - Vender na Hora Certa/Proposta - Hora Certa.pdf>)

## Outras propostas avaliadas

| Desafio | Proposta | Resumo |
|---|---|---|
| 1 · Bioeconomia & Energia | [Energia da Porteira](<Desafio 1 - Energia da Porteira/Proposta - Energia da Porteira.pdf>) | Inventário de resíduos, simulador de payback e consórcio de vizinhos para transformar biomassa em energia ou renda |
| 4 · IA no Campo · Conectividade | [Conta do Talhão](<Desafio 4 - Quanto Rende Este Hectare/Proposta - Conta do Talhao.pdf>) | Custo e resultado por talhão e por lote, registrados com foto ou áudio, mesmo com sinal fraco |

O Conta do Talhão (Desafio 4) pode ser integrado ao Hora Certa no futuro, para usar o custo real por saca de cada talhão em vez da média de R$ 15 mil/ha.
