"""API e servidor do app web (PWA).

Rodar: uvicorn conta_talhao.api:app --host 0.0.0.0 --port 8600
"""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db, extracao, motor, relatorio, whatsapp

WEB = Path(__file__).resolve().parent.parent / "web"
TIPOS_IMAGEM = {"image/jpeg", "image/png", "image/webp", "image/gif"}
LIMITE_IMAGEM = 8 * 1024 * 1024

app = FastAPI(title="Conta do Talhão")
con = db.conectar()
db.semear(con)


def _cadastro():
    return db.talhoes(con), db.lotes(con), db.bombas(con)


@app.get("/api/fazenda")
def fazenda():
    t, lt, b = _cadastro()
    return {
        "talhoes": t, "lotes": lt, "bombas": b,
        "categorias_custo": motor.CATEGORIAS_CUSTO, "categorias_receita": motor.CATEGORIAS_RECEITA,
        "leitura_automatica": extracao.ia_disponivel(),
    }


@app.post("/api/extrair")
async def extrair(
    arquivo: UploadFile | None = File(None),
    texto: str | None = Form(None),
    dica: str | None = Form(None),
    client_id: str | None = Form(None),
):
    """Lê uma foto ou uma anotação e devolve um rascunho para o produtor confirmar."""
    t, lt, b = _cadastro()
    cadastro = extracao.cadastro_texto(t, lt, b)
    anexo = None
    try:
        if arquivo is not None:
            if arquivo.content_type not in TIPOS_IMAGEM:
                raise HTTPException(415, "Envie uma foto (JPG, PNG ou WebP).")
            dados = await arquivo.read()
            if len(dados) > LIMITE_IMAGEM:
                raise HTTPException(413, "A foto passou de 8 MB. Tire outra com menos zoom.")
            db.ANEXOS.mkdir(parents=True, exist_ok=True)
            nome = f"{client_id or uuid.uuid4()}{Path(arquivo.filename or '.jpg').suffix or '.jpg'}"
            (db.ANEXOS / nome).write_bytes(dados)
            anexo = nome
            rascunho = extracao.ler_imagem(dados, arquivo.content_type, cadastro, dica)
        elif texto and texto.strip():
            rascunho = extracao.ler_texto(texto, cadastro)
        else:
            raise HTTPException(400, "Mande uma foto ou escreva o que aconteceu.")
    except extracao.LeituraIndisponivel as e:
        raise HTTPException(503, str(e)) from e

    rascunho["alvo"] = extracao.resolver_alvo(rascunho, t, lt, b)
    if not rascunho["alvo"] and rascunho.get("documento") == "conta_luz" and len(b) == 1:
        rascunho["alvo"] = {"alvo_tipo": "bomba", "alvo_id": b[0]["id"]}
    rascunho["anexo"] = anexo
    return rascunho


class NovoLancamento(BaseModel):
    client_id: str = Field(min_length=8, max_length=64)
    data: date
    categoria: str
    descricao: str = Field(min_length=1, max_length=200)
    quantidade: float | None = None
    unidade: str | None = Field(None, max_length=10)
    valor: float = Field(gt=0)
    alvo_tipo: Literal["talhao", "lote", "bomba", "geral"]
    alvo_id: int | None = None
    origem: Literal["foto", "texto", "audio", "manual", "exemplo"] = "manual"
    anexo: str | None = None


@app.post("/api/lancamentos")
def salvar(itens: list[NovoLancamento]):
    t, lt, b = _cadastro()
    ids = {"talhao": {x["id"] for x in t}, "lote": {x["id"] for x in lt}, "bomba": {x["id"] for x in b}}
    gravados = []
    for it in itens:
        if it.categoria in motor.CATEGORIAS_CUSTO:
            tipo = "custo"
        elif it.categoria in motor.CATEGORIAS_RECEITA:
            tipo = "receita"
        else:
            raise HTTPException(422, f"Categoria desconhecida: {it.categoria}")
        if it.alvo_tipo == "geral":
            if tipo == "receita":
                raise HTTPException(422, "Receita precisa de um talhão ou lote.")
            alvo_id = None
        elif it.alvo_id not in ids[it.alvo_tipo]:
            raise HTTPException(422, "Escolha em qual talhão, lote ou bomba lançar.")
        else:
            alvo_id = it.alvo_id
        if it.alvo_tipo == "bomba" and it.categoria != "energia":
            raise HTTPException(422, "Na bomba só entra conta de luz (energia).")
        registro, novo = db.inserir_lancamento(con, {**it.model_dump(), "data": it.data.isoformat(),
                                                     "tipo": tipo, "alvo_id": alvo_id})
        gravados.append({**registro, "novo": novo})
    return gravados


@app.get("/api/lancamentos")
def listar(alvo_tipo: str | None = None, alvo_id: int | None = None, limite: int | None = 50):
    return db.lancamentos(con, alvo_tipo, alvo_id, limite)


@app.delete("/api/lancamentos/{lanc_id}")
def apagar(lanc_id: int):
    if not db.apagar_lancamento(con, lanc_id):
        raise HTTPException(404, "Lançamento não encontrado.")
    return {"ok": True}


@app.get("/api/painel")
def painel():
    t, lt, b = _cadastro()
    return motor.painel(t, b, lt, db.lancamentos(con))


@app.get("/api/relatorio.pdf")
def relatorio_pdf():
    t, lt, b = _cadastro()
    pdf = relatorio.gerar(motor.painel(t, b, lt, db.lancamentos(con)))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="custo-por-talhao.pdf"'})


def _responder_whatsapp(corpo: dict) -> None:
    try:
        r = whatsapp.tratar_webhook(con, corpo)
        if r:
            whatsapp.enviar(*r)
    except Exception as e:  # o webhook nunca deve derrubar o servidor
        print(f"[whatsapp] erro ao responder: {e!r}")


@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request, tarefas: BackgroundTasks):
    """Recebe eventos da Evolution API. Responde rápido e processa em segundo plano."""
    if whatsapp.WEBHOOK_TOKEN and request.headers.get("x-webhook-token") != whatsapp.WEBHOOK_TOKEN:
        raise HTTPException(401, "Token do webhook inválido.")
    tarefas.add_task(_responder_whatsapp, await request.json())
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/sw.js")
def service_worker():
    # Na raiz para controlar o app inteiro.
    return FileResponse(WEB / "sw.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


app.mount("/web", StaticFiles(directory=WEB), name="web")
