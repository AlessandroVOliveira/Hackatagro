"""API e servidor do app web (PWA).

Rodar: uvicorn ronda.api:app --host 0.0.0.0 --port 8700

Perfil: cada chamada diz quem está olhando (`perfil=<id da propriedade>` ou
`perfil=sindicato`). O produtor vê os próprios registros e os de javali no
ponto exato; o annoni dos vizinhos aparece só por quadrícula de 1 km, a não ser
que o dono tenha escolhido compartilhar o ponto ou o foco esteja na beira da
estrada. A coordenação do sindicato vê tudo.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from . import avisos, db, geo, javali, prioridade, triagem

WEB = Path(__file__).resolve().parent.parent / "web"
TIPOS_IMAGEM = {"image/jpeg", "image/png", "image/webp"}
LIMITE_IMAGEM = 8 * 1024 * 1024
SENSOR_TOKEN = os.environ.get("RONDA_SENSOR_TOKEN", "")
BEIRA_ESTRADA_KM = 0.03
QUARENTENA_DIAS = 10  # Embrapa recomenda de 8 a 10 dias em área sem annoni

app = FastAPI(title="Ronda do Pampa")
_local = threading.local()


def conexao():
    c = getattr(_local, "con", None)
    if c is None:
        c = _local.con = db.conectar()
    return c


db.semear(conexao())


def _perfil(perfil: str | None) -> int | None:
    """None = coordenação do sindicato."""
    if perfil in (None, "", "sindicato"):
        return None
    try:
        pid = int(perfil)
    except ValueError:
        raise HTTPException(400, "Perfil inválido.") from None
    if not any(p["id"] == pid for p in db.propriedades(conexao())):
        raise HTTPException(404, "Propriedade não encontrada.")
    return pid


# ------------------------------------------------------------------ base

@app.get("/api/base")
def base():
    con = conexao()
    hoje = date.today()
    disp = db.dispositivos(con)
    for d in disp:
        d["responsavel_semana"] = avisos.responsavel_semana(d, hoje)
        d["eventos"] = db.eventos(con, d["id"], 5)
    return {
        "hoje": hoje.isoformat(),
        "vizinhanca": {"nome": "Vizinhança do Arroio das Pedras", "municipio": "Alegrete/RS",
                       "lat0": geo.LAT0, "lon0": geo.LON0, "km_lat": geo.KM_LAT, "km_lon": geo.KM_LON,
                       "largura_km": geo.LARGURA_KM, "altura_km": geo.ALTURA_KM},
        "propriedades": [{k: p[k] for k in ("id", "nome", "responsavel", "atividade", "km", "compartilha_exato")}
                         for p in db.propriedades(con)],
        "feicoes": [{k: f[k] for k in ("id", "tipo", "subtipo", "nome", "km")} for f in db.feicoes(con)],
        "dispositivos": disp,
        "controladores": db.controladores(con),
        "parametros": prioridade.PARAM,
        "epoca_sementes": prioridade.epoca_de_sementes(hoje),
        "triagem_automatica": triagem.ia_disponivel(),
        "raio_km": avisos.RAIO_KM,
        "valor_ovino": round(db.VALOR_OVINO, 2),
    }


# ------------------------------------------------------------------ mapa

def _visivel_exato(oc: dict, pid: int | None, props: dict, estradas: list) -> bool:
    if pid is None or oc["tipo"] == "javali":
        return True
    if oc["propriedade_id"] in (pid, None) or oc["autor_id"] == pid:
        return True
    if props.get(oc["propriedade_id"], {}).get("compartilha_exato"):
        return True
    return any(geo.dist_linha(oc["km"], e) <= BEIRA_ESTRADA_KM for e in estradas)


def _publico(oc: dict, pid: int | None) -> dict:
    campos = ("id", "tipo", "subtipo", "km", "area_m2", "animais", "prejuizo", "status", "situacao", "observado_em",
              "eliminado_em", "obs", "foto", "triagem_ia")
    d = {k: oc.get(k) for k in campos}
    d["propria"] = pid is not None and oc["propriedade_id"] == pid
    if pid is None:
        d["propriedade_id"] = oc["propriedade_id"]
    return d


@app.get("/api/mapa")
def mapa(perfil: str | None = None):
    con = conexao()
    pid = _perfil(perfil)
    props = {p["id"]: p for p in db.propriedades(con)}
    feicoes = db.feicoes(con)
    estradas = [f["km"] for f in feicoes if f["tipo"] == "estrada"]
    todas = [o for o in db.ocorrencias(con) if pid is None or o["status"] != "descartada"]
    desde_javali = (date.today() - timedelta(days=60)).isoformat()
    ativos = [o for o in todas if o["tipo"] == "annoni" and o["situacao"] == "ativo" and o["status"] != "descartada"]
    exatos, celulas = [], {}
    for o in todas:
        if o["tipo"] == "javali" and o["observado_em"] < desde_javali:
            continue
        nota = None
        if o in ativos:
            nota = prioridade.avaliar(o, feicoes, ativos)
        if _visivel_exato(o, pid, props, estradas):
            d = _publico(o, pid)
            if nota:
                d["nota"], d["classe"] = nota["nota"], nota["classe"]
            exatos.append(d)
        elif o["situacao"] == "ativo":
            c = geo.celula(o["km"])
            cel = celulas.setdefault(c, {"celula": c, "n": 0, "maior_nota": 0, "manchas": 0})
            cel["n"] += 1
            cel["maior_nota"] = max(cel["maior_nota"], nota["nota"] if nota else 0)
            cel["manchas"] += 1 if nota and nota["mancha"] else 0
    return {"exatos": exatos, "celulas": list(celulas.values())}


@app.get("/api/resumo")
def resumo(perfil: str | None = None):
    con = conexao()
    pid = _perfil(perfil)
    hoje = date.today()
    ocs = db.ocorrencias(con)
    plano = prioridade.plano(ocs, db.feicoes(con), hoje)
    ano = (hoje - timedelta(days=365)).isoformat()
    jv = javali.resumo(ocs, db.dispositivos(con), hoje)
    nao_lidos = sum(1 for a in db.avisos(con, pid, 200) if not a["lido"])
    return {
        "focos_ativos": plano["resumo"]["focos_ativos"],
        "manchas": plano["resumo"]["manchas"], "area_manchas_ha": plano["resumo"]["area_manchas_ha"],
        "eliminados_ano": sum(1 for o in ocs if o["tipo"] == "annoni" and o["situacao"] == "eliminado"
                              and (o["eliminado_em"] or "") >= ano),
        "suspeitas": sum(1 for o in ocs if o["tipo"] == "annoni" and o["status"] == "suspeita" and o["situacao"] == "ativo"),
        "javali_registros": jv["registros"], "javali_prejuizo": jv["prejuizo"], "javali_animais": jv["animais_mortos"],
        "avisos_nao_lidos": nao_lidos,
    }


# ------------------------------------------------------------------ registrar

class NovaOcorrencia(BaseModel):
    client_id: str = Field(min_length=8, max_length=64)
    tipo: Literal["annoni", "javali"]
    subtipo: str = Field(min_length=2, max_length=30)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    area_m2: float | None = Field(None, ge=0, le=10_000_000)
    animais: int | None = Field(None, ge=0, le=10_000)
    prejuizo: float | None = Field(None, ge=0)
    obs: str | None = Field(None, max_length=500)
    observado_em: datetime | None = None
    perfil: str | None = None


SUBTIPOS = {"annoni": {"touceira", "foco", "mancha"}, "javali": set(avisos.NOMES_JAVALI)}


@app.post("/api/ocorrencias")
async def registrar(dados: str = Form(...), foto: UploadFile | None = File(None)):
    try:
        n = NovaOcorrencia.model_validate_json(dados)
    except ValidationError as e:
        raise HTTPException(422, "Dados do registro incompletos.") from e
    if n.subtipo not in SUBTIPOS[n.tipo]:
        raise HTTPException(422, f"Tipo de registro desconhecido: {n.subtipo}")
    con = conexao()
    pid = _perfil(n.perfil)
    p = geo.para_km(n.lat, n.lon)
    if not geo.no_mapa(*p):
        raise HTTPException(422, "O ponto ficou fora do mapa da vizinhança. Marque no mapa.")

    existente = con.execute("SELECT id FROM ocorrencias WHERE client_id = ?", (n.client_id,)).fetchone()
    if existente:  # reenvio da fila offline
        return {"ocorrencia": _publico(db.ocorrencia(con, existente["id"]), pid), "avisados": 0, "novo": False}

    nome_foto, triagem_ia = None, None
    if foto is not None:
        if foto.content_type not in TIPOS_IMAGEM:
            raise HTTPException(415, "Envie uma foto (JPG, PNG ou WebP).")
        conteudo = await foto.read()
        if len(conteudo) > LIMITE_IMAGEM:
            raise HTTPException(413, "A foto passou de 8 MB.")
        db.FOTOS.mkdir(parents=True, exist_ok=True)
        nome_foto = f"{uuid.uuid4().hex}.jpg"
        (db.FOTOS / nome_foto).write_bytes(conteudo)
        if n.tipo == "annoni":
            triagem_ia = triagem.triar(conteudo, foto.content_type)

    dono = next((pr["id"] for pr in db.propriedades(con) if geo.dentro(p, pr["km"])), None)
    area = n.area_m2
    if n.tipo == "annoni" and area is None:
        area = {"touceira": 1, "foco": 10, "mancha": 500}[n.subtipo]
    prejuizo = n.prejuizo
    if n.subtipo == "ataque_criacao" and prejuizo is None and n.animais:
        prejuizo = round(n.animais * db.VALOR_OVINO, 2)
    oc, novo = db.inserir_ocorrencia(con, {
        "client_id": n.client_id, "tipo": n.tipo, "subtipo": n.subtipo, "lat": n.lat, "lon": n.lon,
        "area_m2": area if n.tipo == "annoni" else None, "animais": n.animais, "prejuizo": prejuizo,
        "obs": (n.obs or "").strip() or None, "foto": nome_foto, "propriedade_id": dono, "autor_id": pid,
        # annoni de produtor espera a confirmação do técnico; javali e registro da coordenação valem na hora
        "status": "suspeita" if n.tipo == "annoni" and pid is not None else "confirmada",
        "observado_em": (n.observado_em or datetime.now()).replace(tzinfo=None).isoformat(timespec="seconds"),
    })
    if triagem_ia:
        con.execute("UPDATE ocorrencias SET triagem_ia = ? WHERE id = ?", (json.dumps(triagem_ia, ensure_ascii=False), oc["id"]))
        con.commit()
        oc = db.ocorrencia(con, oc["id"])
    avisados = avisos.ocorrencia_nova(con, oc) if novo else 0
    out = {"ocorrencia": _publico(oc, pid), "avisados": avisados, "novo": novo}
    if n.tipo == "annoni":
        ativos = [o for o in db.ocorrencias(con, "annoni") if o["situacao"] == "ativo" and o["status"] != "descartada"]
        out["prioridade"] = prioridade.avaliar(oc, db.feicoes(con), ativos)
    return out


class Triagem(BaseModel):
    status: Literal["confirmada", "descartada"]


@app.post("/api/ocorrencias/{oid}/triagem")
def triar(oid: int, t: Triagem):
    con = conexao()
    if not db.ocorrencia(con, oid):
        raise HTTPException(404, "Registro não encontrado.")
    return db.atualizar_ocorrencia(con, oid, status=t.status)


class Eliminar(BaseModel):
    custo_real: float | None = Field(None, ge=0)


@app.post("/api/ocorrencias/{oid}/eliminar")
def eliminar(oid: int, e: Eliminar):
    con = conexao()
    oc = db.ocorrencia(con, oid)
    if not oc or oc["tipo"] != "annoni":
        raise HTTPException(404, "Foco não encontrado.")
    return db.atualizar_ocorrencia(con, oid, situacao="eliminado", eliminado_em=date.today().isoformat(),
                                   revisado_em=None, custo_real=e.custo_real)


class Revisita(BaseModel):
    rebrota: bool


@app.post("/api/ocorrencias/{oid}/revisar")
def revisar(oid: int, r: Revisita):
    con = conexao()
    oc = db.ocorrencia(con, oid)
    if not oc or oc["situacao"] != "eliminado":
        raise HTTPException(404, "Foco eliminado não encontrado.")
    if r.rebrota:  # nasceu de novo do banco de sementes: volta para a lista
        return db.atualizar_ocorrencia(con, oid, situacao="ativo", revisado_em=date.today().isoformat(),
                                       observado_em=datetime.now().isoformat(timespec="seconds"))
    return db.atualizar_ocorrencia(con, oid, revisado_em=date.today().isoformat())


# ------------------------------------------------------------------ prioridades e javali

@app.get("/api/prioridades")
def prioridades(perfil: str | None = None):
    con = conexao()
    pid = _perfil(perfil)
    hoje = date.today()
    ocs = db.ocorrencias(con)
    p = prioridade.plano(ocs, db.feicoes(con), hoje, pid)
    if pid is None:
        p["triagem"] = [_publico(o, None) for o in ocs if o["tipo"] == "annoni" and o["status"] == "suspeita"
                        and o["situacao"] == "ativo"]
    pub = lambda o: {**_publico(o, pid), "prioridade": o.get("prioridade"), "revisita_em": o.get("revisita_em"),  # noqa: E731
                     "atrasada": o.get("atrasada")}
    for k in ("semana", "depois", "manchas", "revisitas"):
        p[k] = [pub(o) for o in p[k]]
    return p


@app.get("/api/javali")
def javali_resumo():
    con = conexao()
    return javali.resumo(db.ocorrencias(con, "javali"), db.dispositivos(con), date.today())


class Sensor(BaseModel):
    evento: Literal["fechou", "armada", "bateria_fraca"]


@app.post("/api/dispositivos/{did}/sensor")
def sensor(did: int, s: Sensor, request: Request):
    """Chamado pelo ESP32 da armadilha (chave magnética na porteira, por LoRa ou SMS até a sede)."""
    if SENSOR_TOKEN and request.headers.get("x-sensor-token") != SENSOR_TOKEN:
        raise HTTPException(401, "Token do sensor inválido.")
    con = conexao()
    d = db.dispositivo(con, did)
    if not d or d["tipo"] != "armadilha":
        raise HTTPException(404, "Armadilha não encontrada.")
    estado = {"fechou": "fechada", "armada": "aberta"}.get(s.evento, d["estado"])
    db.registrar_evento(con, did, s.evento, estado)
    avisados = avisos.armadilha_fechou(con, d) if s.evento == "fechou" else 0
    return {"estado": estado, "avisados": avisados}


# ------------------------------------------------------------------ avisos e prevenção

@app.get("/api/avisos")
def listar_avisos(perfil: str | None = None):
    return db.avisos(conexao(), _perfil(perfil))


@app.post("/api/avisos/lidos")
def avisos_lidos(perfil: str | None = None):
    db.marcar_lidos(conexao(), _perfil(perfil))
    return {"ok": True}


class NovoMovimento(BaseModel):
    client_id: str = Field(min_length=8, max_length=64)
    propriedade_id: int
    tipo: Literal["gado", "maquina"]
    descricao: str = Field(min_length=1, max_length=200)
    origem_id: int | None = None
    origem_texto: str | None = Field(None, max_length=120)
    chegada: date


@app.post("/api/movimentos")
def novo_movimento(m: NovoMovimento):
    con = conexao()
    props = {p["id"]: p for p in db.propriedades(con)}
    if m.propriedade_id not in props or (m.origem_id is not None and m.origem_id not in props):
        raise HTTPException(422, "Propriedade não encontrada.")
    if m.origem_id is not None:
        tem = con.execute("SELECT COUNT(*) FROM ocorrencias WHERE tipo = 'annoni' AND situacao = 'ativo' "
                          "AND status != 'descartada' AND propriedade_id = ?", (m.origem_id,)).fetchone()[0]
        risco = "alto" if tem else "baixo"
    else:
        risco = "desconhecido"  # de fora da vizinhança: trate como se tivesse annoni
    liberar = m.chegada + timedelta(days=QUARENTENA_DIAS) if m.tipo == "gado" and risco != "baixo" else None
    mov, _ = db.inserir_movimento(con, {**m.model_dump(), "chegada": m.chegada.isoformat(), "risco": risco,
                                        "liberar_em": liberar.isoformat() if liberar else None})
    return mov


@app.get("/api/movimentos")
def listar_movimentos(perfil: str | None = None):
    return db.movimentos(conexao(), _perfil(perfil))


# ------------------------------------------------------------------ app web

@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/sw.js")
def service_worker():
    return FileResponse(WEB / "sw.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/fotos/{nome}")
def ver_foto(nome: str):
    arq = (db.FOTOS / nome).resolve()
    if arq.parent != db.FOTOS.resolve() or not arq.is_file():
        raise HTTPException(404, "Foto não encontrada.")
    return FileResponse(arq, media_type="image/jpeg")


app.mount("/web", StaticFiles(directory=WEB), name="web")
