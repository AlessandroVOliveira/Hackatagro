# Desafio 2 · Ronda do Pampa

Vigilância de vizinhança contra o capim-annoni e o javali: ver cedo, gastar primeiro onde rende mais e agir junto com os vizinhos.

- Proposta: [Proposta - Ronda do Pampa.pdf](<Proposta - Ronda do Pampa.pdf>)
- Pitch: [Pitch - Ronda do Pampa.pdf](<Pitch - Ronda do Pampa.pdf>)

## Como rodar

```bash
# na raiz do repositório
python -m venv .venv
.venv/Scripts/activate                 # Linux/Mac: source .venv/bin/activate
pip install -r "Desafio 2 - Invasores do Pampa/requirements.txt"

cd "Desafio 2 - Invasores do Pampa"
uvicorn ronda.api:app --host 0.0.0.0 --port 8700
```

Abra http://localhost:8700. Na primeira execução o banco é criado com uma vizinhança fictícia em Alegrete: 8 propriedades, 19 registros de capim-annoni e 41 de javali, com datas contadas a partir de hoje. Para recomeçar do zero, apague a pasta `data/`.

No topo, escolha quem está usando o app: uma das propriedades ou a coordenação do sindicato. Cada perfil vê o mapa de um jeito (ver Privacidade).

Testes: `python -m pytest`

### Opcionais

- **Avisos no WhatsApp:** usa a mesma Evolution API do Conta do Talhão (`../Desafio 4 - Quanto Rende Este Hectare/whatsapp/`). Rode o servidor com `EVOLUTION_APIKEY`, `EVOLUTION_URL` e `EVOLUTION_INSTANCIA` no ambiente e cadastre o número da propriedade na coluna `whatsapp` da tabela `propriedades`. Sem a chave, os avisos aparecem só no app e no log.
- **Pré-triagem da foto:** com `ANTHROPIC_API_KEY`, o Claude sugere se a foto parece capim-annoni. É só uma sugestão para o técnico, que sempre confirma.
- **Sensor da armadilha:** `sensor/armadilha.ino` (ESP32 + chave magnética). Ele chama `POST /api/dispositivos/1/sensor` com `{"evento": "fechou"}`. Defina `RONDA_SENSOR_TOKEN` no servidor e no sensor para proteger o endpoint. Na tela do javali há um botão que simula o sensor.

### No celular

O app é instalável e funciona sem sinal, mas o navegador só libera isso em HTTPS (ou em `localhost`). Para testar no celular, exponha a porta 8700 com um túnel HTTPS (por exemplo `cloudflared tunnel --url http://localhost:8700`). O GPS só cai no mapa se você estiver dentro da área da vizinhança fictícia; fora dela, toque no mapa para marcar o ponto.

## Como funciona

| Parte | O que faz |
|---|---|
| `web/` | App web instalável. Registros vão para uma fila no celular (IndexedDB) e sobem quando há sinal, sem duplicar. Mapa da vizinhança em SVG (`mapa.js`), sem depender de imagem de satélite. |
| `ronda/prioridade.py` | Nota de 0 a 100 por foco de annoni e plano da semana dentro das horas disponíveis. Manchas vão para contenção; focos eliminados voltam para revisita. |
| `ronda/avisos.py` | Avisos para as propriedades num raio de 3 km (1,5 km para rastro e fuçada), no app e no WhatsApp. Armadilha fechada chama o responsável da semana. |
| `ronda/javali.py` | Quadrículas de 1 km com mais sinais, horário de passagem, prejuízo e onde falta câmera ou armadilha. |
| `ronda/triagem.py` | Pré-triagem opcional da foto com o Claude. |
| `ronda/api.py` | API FastAPI, regras de privacidade do mapa e servidor do app. |
| `sensor/` | Código do ESP32 da armadilha coletiva. |

## Nota de prioridade

| Fator | Pontos |
|---|---|
| Tamanho: touceira isolada 40, foco pequeno (até 10 m²) 34, foco médio (até 100 m²) 20, mancha 6 | até 40 |
| Distância até estrada, corredor, porteira, mangueira ou embarcadouro: até 50 m 25, 200 m 18, 500 m 8 | até 25 |
| Distância até campo nativo limpo: até 100 m 25, 500 m 15, 1 km 6 | até 25 |
| Foco isolado (nenhum outro a 500 m), fora as manchas | 10 |

Parâmetros em `ronda/prioridade.py`: mão de obra R$ 30/h, 12 h por semana, recuperação de 243 kg de peso vivo por hectare (método Mirapasto, Embrapa) a R$ 10/kg, revisita a cada 60 dias.

## Privacidade

- O produtor vê no ponto exato os próprios registros, todos os sinais de javali, os focos na beira da estrada e os de quem escolheu compartilhar.
- O annoni dos outros vizinhos aparece só como quadrícula de 1 km, sem o nome da propriedade.
- Os avisos dizem a distância e a referência mais próxima, nunca de quem é a terra.
- A coordenação do sindicato vê tudo, para fazer a triagem e organizar o mutirão.

## Fontes

- Capim-annoni: Embrapa Pecuária Sul (Guia prático de prevenção e controle do capim-annoni no Pampa; método Mirapasto), UFRGS. Até 80 mil sementes por planta por ano, banco de sementes de mais de 20 anos, sementes viáveis nas fezes até o quarto dia, quarentena de 8 a 10 dias.
- Javali: IN Ibama nº 3/2013 e IN nº 12/2019 (SIMAF). Caso de Sant'Ana do Livramento: dados do desafio.

## Próximos passos

- [ ] Piloto com o sindicato rural de Alegrete numa vizinhança real
- [ ] Registro direto pelo WhatsApp (foto + localização)
- [ ] Sentinel-2 para acompanhar as manchas grandes entre safras
- [ ] Integração com o Conta do Talhão (Desafio 4)
