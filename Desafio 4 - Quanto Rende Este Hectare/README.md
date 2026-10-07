# Desafio 4 · Conta do Talhão

Custo e resultado por talhão e por lote, registrados com uma foto ou uma frase, mesmo com sinal fraco.

- Proposta: [Proposta - Conta do Talhao.pdf](<Proposta - Conta do Talhao.pdf>)
- Pitch: [Pitch - Conta do Talhão.pdf](<Pitch - Conta do Talhão.pdf>)

## Como rodar

```bash
# na raiz do repositório
python -m venv .venv
.venv/Scripts/activate                 # Linux/Mac: source .venv/bin/activate
pip install -r "Desafio 4 - Quanto Rende Este Hectare/requirements.txt"

cd "Desafio 4 - Quanto Rende Este Hectare"
uvicorn conta_talhao.api:app --host 0.0.0.0 --port 8600
```

Abra http://localhost:8600. Na primeira execução o banco é criado com uma propriedade fictícia (300 ha, 4 talhões de arroz, 2 lotes de gado).

Testes: `python -m pytest`

### Leitura automática de notas (opcional)

Com uma credencial da Anthropic (`ANTHROPIC_API_KEY` no ambiente ou no `whatsapp/.env`), o Claude lê a foto da nota, a conta de luz e o romaneio. Sem credencial, frases são lidas por regras simples e fotos viram um formulário para o produtor completar.

### WhatsApp (Evolution API)

```bash
cd whatsapp
python configurar.py iniciar     # cria o .env com segredos aleatórios (fora do git)
docker compose up -d             # Evolution API + Postgres + Redis em localhost:8080
cd ..
uvicorn conta_talhao.api:app --host 0.0.0.0 --port 8600 --env-file whatsapp/.env
cd whatsapp && python configurar.py conectar   # cria a instância, liga o webhook e salva qrcode.png
```

Escaneie o `qrcode.png` em WhatsApp > Aparelhos conectados. Use um número só para o bot: a Evolution não é a API oficial do WhatsApp e o número pode ser bloqueado.

Áudio só é entendido se a transcrição da própria Evolution estiver ligada; sem ela, o bot pede para escrever.

### No celular

O app é instalável e funciona sem sinal, mas o navegador só libera isso em HTTPS (ou em `localhost`). Para testar no celular, exponha a porta 8600 com um túnel HTTPS (por exemplo `cloudflared tunnel --url http://localhost:8600`).

## Como funciona

| Parte | O que faz |
|---|---|
| `web/` | App web instalável. Fotos e frases ficam numa fila no celular (IndexedDB) e são enviadas quando há sinal. O produtor confere cada leitura antes de salvar. Painel com mapa da propriedade colorido por margem, custo, energia, adubo ou defensivos por hectare. |
| `conta_talhao/extracao.py` | Lê foto ou frase e devolve um rascunho: produto, categoria, quantidade, valor e talhão citado. Claude (Opus 5.5, saída em JSON com esquema fixo) ou regras. |
| `conta_talhao/motor.py` | Rateio: lançamento no talhão ou lote vai inteiro; conta de luz da bomba é dividida entre os talhões que ela irriga, por área; gastos gerais são divididos por área. Calcula custo/ha, custo/saca, margem e alertas. |
| `conta_talhao/whatsapp.py` | Conversa no WhatsApp: lê, pergunta só o que falta ("qual o valor?", "em qual talhão?") e salva quando o produtor confirma. |
| `conta_talhao/relatorio.py` | PDF para o banco com custo e produtividade por área. |
| `conta_talhao/api.py` | API FastAPI e servidor do app. |
| `whatsapp/` | Docker Compose da Evolution API e script de configuração. |

## Alertas

- Gasto de energia, adubo ou defensivos por hectare 30% acima da média da fazenda.
- Talhão com margem negativa na safra.

## Próximos passos

- [ ] Piloto com produtores de Alegrete
- [ ] Produtividade por talhão a partir dos dados da colheitadeira
- [ ] Modo técnico: um agrônomo acompanhando vários clientes
- [ ] Integração com o Desafio 3 (Entressafra): custo real da saca na decisão de venda
