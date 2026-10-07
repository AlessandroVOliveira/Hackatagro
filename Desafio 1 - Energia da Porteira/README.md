# Desafio 1 · Energia da Porteira

Inventário de resíduos, simulador de payback e consórcio de vizinhos para
transformar a biomassa da propriedade (palha, casca e esterco) em energia mais
barata ou renda nova. Proposta completa:
[Proposta - Energia da Porteira.pdf](<Proposta - Energia da Porteira.pdf>).

## Como abrir

É uma página só, sem backend e sem instalação. Duas formas:

1. **Duplo-clique no `index.html`** — abre direto no navegador.
2. Ou, servindo a pasta (recomendado, o mapa carrega melhor):

   ```bash
   python -m http.server 8000
   # abra http://localhost:8000
   ```

O mapa (Leaflet) e os blocos do mapa vêm da internet. Sem internet, o inventário
e as rotas funcionam normalmente; só o mapa fica indisponível, e a soma do
consórcio continua sendo calculada.

## O que o protótipo faz (as três camadas da proposta)

| Seção | Pergunta que responde |
|---|---|
| **1 · Inventário** | Quanto resíduo eu gero por ano (palha, casca, esterco) e qual o potencial energético? 5 perguntas, com 3 perfis prontos. |
| **2 · Rotas e payback** | O que fazer com o resíduo? Compara vender, briquete/pellet, queima para secagem própria e biodigestor, com investimento, R$/ano e **payback**, ordenados do que se paga mais rápido ao mais lento. |
| **3 · Consórcio** | Se nenhuma rota fecha sozinha, quanto os vizinhos somam? Mapa de Alegrete que soma o volume num raio ajustável e avisa quando o grupo atinge a escala de uma rota compartilhada (Lei 14.300/2022). |

## Como a conta é feita

Tudo é cálculo transparente sobre coeficientes **editáveis na própria tela**
(cada seção tem um bloco "premissas" com faixa mín/méd/máx e fonte). Nada é
previsão.

```
palha recolhível (t/ano) = área × produtividade × (palha/grão) × fração recolhível
casca (t/ano)            = área × produtividade × 20%        (só quem tem engenho)
esterco recolhível       = cabeças × kg/cab/dia × 365 × fração do manejo
biogás (m³/ano)          = esterco × rendimento de biogás

payback de cada rota = investimento ÷ (economia + receita − custo de operação)
```

A ficha mostra a melhor rota em R$/ano e a que se paga mais rápido. O cartão do
**teto de investimento** parte do custo de energia da irrigação (R$ 1.124/ha do
desafio): cada 10% de redução na conta vira o teto que um investimento em energia
própria precisa caber para se pagar.

## Coeficientes e fontes (todos a validar)

Os valores padrão são **referências da literatura** para a demonstração e
precisam ser confirmados com IRGA, Emater e compradores da região. O resultado é
sensível a eles — por isso ficam editáveis.

| Coeficiente | Padrão (faixa) | Base |
|---|---|---|
| Produtividade do arroz | 8,5 (7–10) t/ha | IRGA — média RS |
| Casca | 20% do peso do grão | desafio; Embrapa |
| Palha/grão × recolhível | 1,0 × 40% | literatura |
| Poder calorífico casca / palha | 3,75 / 3,5 kWh/kg | ~13,5 / ~12,6 MJ/kg |
| Esterco bovino | 10 kg/cab/dia | Embrapa |
| Fração recolhível do esterco | 5% / 30% / 70% | extensivo / mangueira / confinamento |
| Biogás | 30 m³/t esterco; 2,0 kWh elétricos/m³ | biodigestão de esterco bovino |
| Preços (casca/palha/briquete) | R$ 50 / 70 / 550 por t | a validar na região |
| Tarifa de energia | R$ 0,60/kWh | tarifa rural/irrigação |

Preços de equipamento (enfardadeira, briquetadeira, biodigestor, secador) também
são faixas editáveis em "premissas".

## Estrutura

```
index.html                página única (3 seções + critérios)
assets/
  css/styles.css          identidade visual (mesma paleta do Hora Certa, Desafio 3)
  js/
    formato.js            formatação pt-BR e atalhos de DOM
    dados.js              coeficientes (faixa + fonte) e ~12 propriedades de Alegrete
    inventario.js         camada 1 — inventário (toneladas + energia)
    rotas.js              camada 2 — rotas e payback
    consorcio.js          camada 3 — mapa e soma por raio
    app.js                parâmetros editáveis, perfis e ligação dos eventos
```

Os scripts são carregados em ordem (`formato → dados → camadas → app`) como
scripts clássicos, sem módulos ES, justamente para o `index.html` abrir com um
duplo-clique, sem servidor.

As propriedades do mapa são fictícias, só para demonstrar o consórcio.

## Próximos passos

- [ ] Validar coeficientes e preços de resíduo com IRGA, Emater e compradores.
- [ ] Cadastrar compradores reais (cerâmicas, termelétricas a casca, avicultura) no mapa.
- [ ] Piloto com um sindicato rural de Alegrete para formar o primeiro consórcio.
- [ ] Puxar a área e o custo por talhão do *Conta do Talhão* (Desafio 4).
