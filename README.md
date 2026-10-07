# HackatAgro × Sebrae RS · Alegrete/RS

Repositório da equipe para o HackatAgro. Aqui ficam as propostas e os protótipos dos três desafios que estamos trabalhando. Cada desafio tem sua própria pasta, com a proposta em PDF e, quando houver, o código.

| Desafio | Proposta | Status |
|---|---|---|
| 1 · Bioeconomia & Energia | [Energia da Porteira](#desafio-1--energia-da-porteira) | Proposta |
| 3 · Novas Cadeias | [Entressafra](#desafio-3--entressafra) | **Protótipo em desenvolvimento** |
| 4 · IA no Campo · Conectividade | [Conta do Talhão](#desafio-4--conta-do-talhão) | Proposta |

Começamos pelo Desafio 3.

---

## Desafio 1 · Energia da Porteira

> Inventário de resíduos, simulador de payback e consórcio de vizinhos para transformar biomassa em energia ou renda.

**Pergunta:** como transformar a biomassa que a propriedade já gera (casca e palha de arroz, esterco, resto de lavoura) em energia mais barata ou renda nova para o produtor?

**Problema:** a energia representa 7% do custo do arroz (R$ 1.124/ha) e a água mais 9%, enquanto palha e esterco ficam parados na propriedade. As causas são de informação e coordenação, não de tecnologia. O produtor não sabe quanto resíduo tem nem quanto ele vale, as usinas exigem uma escala que uma propriedade sozinha não alcança, e falta quem junte o volume dos vizinhos.

**Solução em três camadas:**
1. **Inventário de resíduos:** com 4 ou 5 perguntas, estima toneladas por ano de palha, casca e esterco e o potencial energético.
2. **Simulador de rotas:** compara venda do resíduo, briquete/pellet, biodigestor e queima para secagem própria, com investimento e payback de cada rota.
3. **Consórcio de vizinhos:** mapa que soma o volume num raio e avisa quando o grupo atinge a escala mínima. Pode usar a geração distribuída compartilhada (Lei 14.300/2022).

**MVP:** calculadora web, gráfico de payback por perfil e mapa do consórcio (HTML/JS ou Streamlit + Leaflet).

📄 [Proposta completa](<Desafio 1 - Energia da Porteira/Proposta - Energia da Porteira.pdf>)

---

## Desafio 3 · Entressafra

> Simulador de comercialização que mostra, em R$ por saca e por cabeça, o custo de vender por falta de caixa.

**Pergunta:** como ajudar o produtor a escolher quando e como vender o arroz e o gado, para que a falta de dinheiro deixe de decidir por ele?

**Problema:** a colheita do arroz se concentra em março e abril, quando o preço está no ponto mais baixo e as contas vencem. Sem armazém próprio e muitas vezes preso a adiantamentos, o produtor vende na pressa. No gado acontece o mesmo. Com custo perto de R$ 15 mil/ha, poucos reais por saca separam lucro de prejuízo.

**Solução:** simulador que responde três perguntas:
1. **Quanto eu perco vendendo agora?** Histórico CEPEA mostrando o pior ano, a mediana e o melhor ano.
2. **Quanto custa esperar?** Armazenagem, secagem, quebra, frete e custo do dinheiro.
3. **Como eu pago as contas enquanto espero?** EGF, CPR, CDA/WA, venda escalonada e o custo real do adiantamento.

**Protótipo:** app em Streamlit com dados reais do CEPEA e do Banco Central. Instruções em [`Desafio 3 - Vender na Hora Certa/`](<Desafio 3 - Vender na Hora Certa/README.md>).

📄 [Proposta completa](<Desafio 3 - Vender na Hora Certa/Proposta - Hora Certa.pdf>)

---

## Desafio 4 · Conta do Talhão

> Custo e resultado por talhão e por lote, registrados com uma foto ou um áudio, mesmo com sinal fraco.

**Pergunta:** como dar ao produtor, com o celular e o sinal que ele tem, quanto custa e quanto rende cada área e cada lote de animais?

**Problema:** o produtor sabe quanto colheu, mas não quanto custou cada talhão. Adubo, água e energia somam 31% do custo e variam muito entre áreas. Os dados estão espalhados em cadernos, notas e contas de luz, e qualquer solução que exija digitar planilhas fracassa.

**Solução:** o produtor manda foto da nota fiscal, áudio ("passei 200 kg de ureia no talhão 3"), conta de luz da bomba ou romaneio, e a IA transforma tudo em lançamentos de custo por talhão. Funciona offline (PWA) ou por Telegram. Gera painel por talhão, alertas ("o talhão 7 gastou 40% mais energia que a média") e relatório para o banco.

**MVP:** PWA/Telegram, extração com IA multimodal, FastAPI + SQLite, painel web.

📄 [Proposta completa](<Desafio 4 - Quanto Rende Este Hectare/Proposta - Conta do Talhao.pdf>)

---

## Como os desafios se conectam

O **Conta do Talhão** (4) calcula o custo real por saca de cada área, e esse custo pode alimentar o **Entressafra** (3) no lugar da média de R$ 15 mil/ha. Já o **Energia da Porteira** (1) ataca o maior item de custo variável da lavoura irrigada, que o Conta do Talhão ajuda a medir.
