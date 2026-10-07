# Desafio 3 · Hora Certa

Simulador de comercialização que mostra, em R$ por saca e por cabeça, quanto custa vender por falta de caixa. Proposta completa: [Proposta - Hora Certa.pdf](<Proposta - Hora Certa.pdf>).

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Os dados já vêm na pasta `data/`, então o app funciona sem internet. Para atualizar:

```bash
python scripts/atualizar_dados.py
```

Testes: `python -m pytest`

## O que o app faz

| Aba | Pergunta que responde |
|---|---|
| **Arroz** | Quanto eu perco vendendo tudo na colheita? Compara 4 cenários (vender tudo na colheita, armazenar, financiar a estocagem, venda escalonada) e mostra qual mês costuma compensar. |
| **Gado** | Vale segurar o lote N meses? Ganho de peso × preço histórico − custo de manutenção − juros. |
| **Como pagar as contas** | Quanto de juros está embutido no adiantamento do comprador, comparado com o financiamento de estocagem e com o CDI, e quais alternativas de crédito existem. |

## Como a conta é feita

Para cada ano do histórico calculamos a razão **preço do mês ÷ preço médio de mar/abr do mesmo ano**. Essa razão é aplicada ao preço de colheita do produtor, o que gera um resultado por ano. O app mostra o pior ano, a mediana e o melhor ano, nunca uma previsão única.

Resultado líquido de guardar até o mês *k*, em R$/saca:

```
preço_colheita × razão_k × (1 − quebra × k)
  − armazenagem × k − recepção/secagem − frete
  − custo do dinheiro (juros do financiamento na parte financiada, CDI no resto)
```

Como o custo do dinheiro já está descontado, o valor é comparável direto com o preço recebido na colheita.

O cenário recomendado é o de maior ganho mediano **entre os que pagam as contas da colheita**, e só se esperar tiver ganhado na maioria dos anos. Caso contrário, o app recomenda vender na colheita.

## Fontes de dados

| Dado | Fonte | Arquivo |
|---|---|---|
| Arroz em casca RS (R$/saca 50 kg, diário desde 2005) | Indicador CEPEA/IRGA-RS | `data/arroz_cepea.csv` |
| Boi gordo (R$/@, diário desde 1997) | Indicador CEPEA/ESALQ (SP), usado só para a sazonalidade | `data/boi_cepea.csv` |
| Selic e CDI | API SGS do Banco Central (séries 432 e 4389) | `data/juros.json` |

## Premissas a validar

Os valores padrão abaixo são referências para a demonstração. Ainda precisam ser confirmados com cooperativas, armazéns e bancos de Alegrete. O resultado é **sensível** a eles:

- Armazenagem de terceiros: R$ 1,00/saca/mês
- Recepção e secagem: R$ 3,00/saca (só o que excede a venda direta)
- Quebra técnica: 0,3% ao mês
- Juros do financiamento de estocagem: 12% a.a.; banco financia até 70% do estoque
- Gado: rendimento de carcaça de 50%, ganho de 0,5 kg/dia, custo de R$ 60/cabeça/mês

## Estrutura

```
app.py                  interface Streamlit
hora_certa/ui.py        estilos e componentes visuais (responsivo para celular)
hora_certa/dados.py     download e leitura das séries (CEPEA, BCB)
hora_certa/sazonalidade.py  razões mês/colheita por ano
hora_certa/cenarios.py  conta líquida de cada cenário (arroz e gado)
scripts/atualizar_dados.py
tests/
data/
```

## Próximos passos

- [ ] Validar os custos de armazenagem e as taxas de crédito em Alegrete
- [ ] Série de preços de boi e terneiro do RS (NESPRO/UFRGS ou Emater)
- [ ] Contas a pagar com datas (fluxo de caixa mês a mês)
- [ ] Bot no Telegram: "quanto perco vendendo hoje?"
- [ ] Mapa de armazéns (base Conab) com frete
