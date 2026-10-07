"""Avisos para os vizinhos. Quando aparece um foco de annoni ou sinal de javali,
as propriedades dentro do raio recebem um aviso no app e, se tiverem número
cadastrado, no WhatsApp (Evolution API, a mesma do Conta do Talhão).

O aviso para o vizinho nunca diz de quem é a propriedade onde o foco apareceu:
só a distância e a referência mais próxima (porteira, estrada, arroio).
"""

from __future__ import annotations

import os
from datetime import date, datetime

import httpx

from . import db, geo, prioridade

RAIO_KM = {"annoni": 3.0, "javali": 3.0}
RAIO_RASTRO_KM = 1.5  # rastro e fuçada só avisam quem está bem perto

EVOLUTION_URL = os.environ.get("EVOLUTION_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_APIKEY = os.environ.get("EVOLUTION_APIKEY", "")
EVOLUTION_INSTANCIA = os.environ.get("EVOLUTION_INSTANCIA", "ronda-do-pampa")

NOMES_JAVALI = {
    "rastro": "Rastro de javali", "fucada": "Campo fuçado por javali", "avistamento": "Javali avistado",
    "lavoura": "Javali estragou lavoura", "ataque_criacao": "Javali atacou criação",
}


def enviar_whatsapp(numero: str, texto: str) -> None:
    if not EVOLUTION_APIKEY:
        print(f"[whatsapp sem EVOLUTION_APIKEY] para {numero}:\n{texto}\n")
        return
    try:
        httpx.post(f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCIA}", headers={"apikey": EVOLUTION_APIKEY},
                   json={"number": numero, "text": texto}, timeout=20).raise_for_status()
    except httpx.HTTPError as e:  # aviso perdido não pode derrubar o registro
        print(f"[whatsapp] falhou para {numero}: {e!r}")


def periodo(iso: str) -> str:
    h = datetime.fromisoformat(iso).hour
    return "de madrugada" if h < 6 else "de manhã" if h < 12 else "de tarde" if h < 18 else "à noite"


def quando(iso: str, hoje: date | None = None) -> str:
    d = (hoje or date.today()) - datetime.fromisoformat(iso).date()
    dia = "hoje" if d.days <= 0 else "ontem" if d.days == 1 else f"há {d.days} dias"
    return f"{dia} {periodo(iso)}"


def _km_txt(d: float) -> str:
    if d < 0.5:
        return "menos de 500 m"
    v = round(d * 2) / 2
    return f"{v:.0f} km" if v == int(v) else f"{v:.1f} km".replace(".", ",")


def referencia(p, feicoes) -> str:
    """Ponto de referência mais próximo, para o vizinho saber onde olhar."""
    cands = []
    for f in feicoes:
        if f["tipo"] == "vetor":
            cands.append((geo.dist(p, f["km"]), f["nome"]))
        elif f["tipo"] in ("estrada", "arroio", "corredor"):
            cands.append((geo.dist_linha(p, f["km"]), ("na beira da " if f["tipo"] == "estrada" else "perto do ") + f["nome"]))
    d, nome = min(cands)
    if nome.startswith(("na beira", "perto")):
        return nome
    return ("perto da " if nome.split()[0] in ("Porteira", "Mangueira") else "perto do ") + nome


def _texto_vizinho(oc: dict, dist_km: float, ref: str) -> str:
    longe = "dentro da sua divisa" if dist_km == 0 else f"a {_km_txt(dist_km)} da sua divisa"
    if oc["tipo"] == "annoni":
        tam = prioridade.classe(oc.get("area_m2"))[0]
        conf = " (a confirmar)" if oc["status"] == "suspeita" else ""
        return (f"Capim-annoni: {tam}{conf} {longe}, {ref}. "
                "Confira porteiras e corredores e deixe em quarentena o gado que vier daquele lado.")
    nome = NOMES_JAVALI.get(oc["subtipo"], "Sinal de javali")
    extra = ""
    if oc["subtipo"] == "ataque_criacao" and oc.get("animais"):
        extra = f" ({oc['animais']} animais)"
    elif oc["subtipo"] == "avistamento" and oc.get("animais"):
        extra = f" (bando de {oc['animais']})"
    dica = " Recolha as ovelhas perto das casas à noite." if oc["subtipo"] == "ataque_criacao" else ""
    return f"{nome}{extra} {longe}, {ref}, {periodo(oc['observado_em'])}.{dica}"


def ocorrencia_nova(con, oc: dict, enviar: bool = True, criado_em: str | None = None) -> int:
    """Gera os avisos de uma ocorrência nova. Devolve quantas propriedades foram avisadas."""
    if oc["status"] == "descartada":
        return 0
    feicoes = db.feicoes(con)
    ref = referencia(oc["km"], feicoes)
    raio = RAIO_KM[oc["tipo"]]
    if oc["tipo"] == "javali" and oc["subtipo"] in ("rastro", "fucada"):
        raio = RAIO_RASTRO_KM
    n = 0
    for pr in db.propriedades(con):
        d = geo.dist_poligono(oc["km"], pr["km"])
        if pr["id"] == oc["propriedade_id"]:
            if oc.get("autor_id") == pr["id"]:
                continue  # foi o próprio dono que registrou
            texto = (f"Alguém da vizinhança registrou {('um possível foco de capim-annoni' if oc['tipo'] == 'annoni' else NOMES_JAVALI.get(oc['subtipo'], 'sinal de javali').lower())} "
                     f"dentro da sua propriedade, {ref}. Veja no mapa e confirme quando puder.")
        elif d <= raio:
            texto = _texto_vizinho(oc, d, ref)
        else:
            continue
        db.inserir_aviso(con, pr["id"], oc["tipo"], texto, ocorrencia_id=oc["id"], criado_em=criado_em)
        n += 1
        if enviar and pr.get("whatsapp"):
            enviar_whatsapp(pr["whatsapp"], f"*Ronda do Pampa*\n{texto}")
    # coordenação: suspeitas para confirmar e danos
    if oc["status"] == "suspeita":
        db.inserir_aviso(con, None, "triagem", f"Nova suspeita de capim-annoni para confirmar, {ref}.",
                         ocorrencia_id=oc["id"], criado_em=criado_em)
    elif oc["tipo"] == "javali" and oc["subtipo"] in ("ataque_criacao", "lavoura"):
        db.inserir_aviso(con, None, "javali", _texto_vizinho(oc, 0, ref).replace("dentro da sua divisa", "na vizinhança"),
                         ocorrencia_id=oc["id"], criado_em=criado_em)
    con.commit()
    return n


def responsavel_semana(disp: dict, hoje: date | None = None) -> int | None:
    rod = disp.get("rodizio") or []
    if not rod:
        return None
    semana = (hoje or date.today()).isocalendar().week
    return rod[semana % len(rod)]


def armadilha_fechou(con, disp: dict) -> int:
    """O sensor da porteira avisou que a armadilha fechou: chama o responsável da semana e a coordenação."""
    resp = responsavel_semana(disp)
    props = {p["id"]: p for p in db.propriedades(con)}
    hora = datetime.now().strftime("%H:%M")
    quem = props[resp]["nome"] if resp in props else "a coordenação"
    texto = (f"A armadilha {disp['nome']} fechou às {hora}. Responsável desta semana: {quem}. "
             "Chame um controlador cadastrado no Ibama para o manejo; não abra a armadilha sozinho.")
    avisados = 0
    for pid in [resp, None] if resp else [None]:
        db.inserir_aviso(con, pid, "armadilha", texto, dispositivo_id=disp["id"])
        avisados += 1
        if pid and props[pid].get("whatsapp"):
            enviar_whatsapp(props[pid]["whatsapp"], f"*Ronda do Pampa*\n{texto}")
    con.commit()
    return avisados
