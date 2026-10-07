"""Canal WhatsApp via Evolution API.

O produtor manda foto da nota, conta de luz, romaneio ou uma frase. O bot lê,
pergunta só o que falta ("em qual talhão?", "qual o valor?") e salva quando o
produtor confirma. O estado de cada conversa fica no SQLite.

Evolution API (v2): webhook `messages.upsert` com a mídia em base64 e envio
por POST /message/sendText/{instancia}.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date, datetime

import httpx

from . import db, extracao, motor

EVOLUTION_URL = os.environ.get("EVOLUTION_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_APIKEY = os.environ.get("EVOLUTION_APIKEY", "")
EVOLUTION_INSTANCIA = os.environ.get("EVOLUTION_INSTANCIA", "conta-talhao")
WEBHOOK_TOKEN = os.environ.get("WHATSAPP_WEBHOOK_TOKEN", "")

AJUDA = (
    "Oi! Eu anoto os custos da lavoura e do gado para você.\n\n"
    "Mande:\n"
    "• foto da *nota fiscal* da revenda\n"
    "• foto da *conta de luz* da bomba\n"
    "• foto do *romaneio* ou da nota de venda\n"
    "• ou escreva: _passei 200 kg de ureia no talhão 3 por 640 reais_\n\n"
    "Escreva *resumo* para ver o custo de cada talhão."
)

ESQUEMA_CONVERSA = """
CREATE TABLE IF NOT EXISTS conversas (
  jid TEXT PRIMARY KEY, estado TEXT NOT NULL, atualizado_em TEXT NOT NULL
);
"""


# ------------------------------------------------------------------ envio

def enviar(jid: str, texto: str) -> None:
    if not EVOLUTION_APIKEY:
        print(f"[whatsapp sem EVOLUTION_APIKEY] para {jid}:\n{texto}\n")
        return
    httpx.post(
        f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCIA}",
        headers={"apikey": EVOLUTION_APIKEY},
        json={"number": jid, "text": texto},
        timeout=30,
    ).raise_for_status()


# ------------------------------------------------------------------ estado

def _estado(con, jid: str) -> dict | None:
    con.executescript(ESQUEMA_CONVERSA)
    r = con.execute("SELECT estado FROM conversas WHERE jid = ?", (jid,)).fetchone()
    return json.loads(r["estado"]) if r else None


def _guardar(con, jid: str, estado: dict | None) -> None:
    con.executescript(ESQUEMA_CONVERSA)
    if estado is None:
        con.execute("DELETE FROM conversas WHERE jid = ?", (jid,))
    else:
        con.execute(
            "INSERT INTO conversas (jid, estado, atualizado_em) VALUES (?, ?, ?) "
            "ON CONFLICT(jid) DO UPDATE SET estado = excluded.estado, atualizado_em = excluded.atualizado_em",
            (jid, json.dumps(estado, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
        )
    con.commit()


# ------------------------------------------------------------------ formatação

def _rs(v: float | None) -> str:
    if v is None:
        return "?"
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").strip()


def _nome_categoria(cat: str) -> str:
    return (motor.CATEGORIAS_CUSTO | motor.CATEGORIAS_RECEITA).get(cat, cat).lower()


def _opcoes(con, receita: bool, energia: bool) -> list[dict]:
    """Destinos possíveis, numerados para o produtor responder com um número."""
    ops = [{"rotulo": t["nome"], "alvo_tipo": "talhao", "alvo_id": t["id"]} for t in db.talhoes(con)]
    ops += [{"rotulo": f"Lote {lt['nome']}", "alvo_tipo": "lote", "alvo_id": lt["id"]} for lt in db.lotes(con)]
    if energia:
        ops += [{"rotulo": b["nome"], "alvo_tipo": "bomba", "alvo_id": b["id"]} for b in db.bombas(con)]
    if not receita:
        ops.append({"rotulo": "Geral da lavoura (dividir por área)", "alvo_tipo": "geral", "alvo_id": None})
    return ops


def _rotulo_alvo(con, alvo: dict) -> str:
    tipo, i = alvo["alvo_tipo"], alvo["alvo_id"]
    if tipo == "geral":
        return "geral da lavoura"
    fonte = {"talhao": db.talhoes, "lote": db.lotes, "bomba": db.bombas}[tipo](con)
    nome = next((x["nome"] for x in fonte if x["id"] == i), "?")
    return f"lote {nome}" if tipo == "lote" else nome


def _resumo_itens(itens: list[dict]) -> str:
    linhas = []
    for it in itens:
        qtd = f"{it['quantidade']:g} {it['unidade'] or ''}".strip() + ", " if it.get("quantidade") else ""
        linhas.append(f"• {it['descricao'] or _nome_categoria(it['categoria'])}: {qtd}{_rs(it.get('valor_total'))} "
                      f"({_nome_categoria(it['categoria'])})")
    return "\n".join(linhas)


# ------------------------------------------------------------------ fluxo

def _proximo_passo(con, jid: str, estado: dict) -> str:
    """Decide o que perguntar a seguir, ou salva quando está tudo certo."""
    itens = estado["itens"]
    faltando = [i for i, it in enumerate(itens) if not it.get("valor_total")]
    if faltando:
        estado["aguardando"] = "valor"
        estado["item_valor"] = faltando[0]
        _guardar(con, jid, estado)
        it = itens[faltando[0]]
        return f"Qual foi o valor total de *{it['descricao'] or _nome_categoria(it['categoria'])}*, em reais?"

    if not estado.get("alvo"):
        receita = any(it["categoria"] in motor.CATEGORIAS_RECEITA for it in itens)
        energia = all(it["categoria"] == "energia" for it in itens)
        ops = _opcoes(con, receita, energia)
        estado["aguardando"] = "alvo"
        estado["opcoes"] = ops
        _guardar(con, jid, estado)
        lista = "\n".join(f"*{n}* {o['rotulo']}" for n, o in enumerate(ops, start=1))
        return f"Li isto:\n{_resumo_itens(itens)}\n\nEm qual {'talhão ou lote' if not energia else 'bomba ou talhão'} lanço? Responda o número:\n{lista}"

    estado["aguardando"] = "confirmar"
    _guardar(con, jid, estado)
    return (f"Li isto:\n{_resumo_itens(itens)}\n\nLanço em *{_rotulo_alvo(con, estado['alvo'])}*?\n"
            "Responda *sim*, ou *outro* para escolher outro lugar, ou *cancelar*.")


def _salvar(con, jid: str, estado: dict) -> str:
    alvo = estado["alvo"]
    data = estado.get("data") or date.today().isoformat()
    total = 0.0
    for n, it in enumerate(estado["itens"]):
        cat = it["categoria"]
        tipo = "receita" if cat in motor.CATEGORIAS_RECEITA else "custo"
        if alvo["alvo_tipo"] == "bomba" and cat != "energia":
            cat = "energia"
        db.inserir_lancamento(con, {
            "client_id": f"wa-{estado['msg_id']}-{n}", "data": data, "tipo": tipo, "categoria": cat,
            "descricao": (it["descricao"] or _nome_categoria(cat))[:200], "quantidade": it.get("quantidade"),
            "unidade": it.get("unidade"), "valor": float(it["valor_total"]), "alvo_tipo": alvo["alvo_tipo"],
            "alvo_id": alvo["alvo_id"], "origem": estado.get("origem", "texto"), "anexo": estado.get("anexo"),
        })
        total += float(it["valor_total"])
    _guardar(con, jid, None)

    msg = f"✅ Salvo em *{_rotulo_alvo(con, alvo)}*: {_rs(total)}."
    if alvo["alvo_tipo"] == "talhao":
        p = motor.painel(db.talhoes(con), db.bombas(con), db.lotes(con), db.lancamentos(con))
        t = next(x for x in p["talhoes"] if x["id"] == alvo["alvo_id"])
        msg += f"\nCusto do talhão até agora: {_rs(t['custo_ha'])}/ha."
        alerta = next((a for a in p["alertas"] if a["talhao_id"] == t["id"] and a["tipo"] != "margem"), None)
        if alerta:
            msg += f"\n⚠️ {alerta['texto']}"
    return msg


def _resumo(con) -> str:
    p = motor.painel(db.talhoes(con), db.bombas(con), db.lotes(con), db.lancamentos(con))
    linhas = ["*Custo e margem por talhão*"]
    for t in p["talhoes"]:
        margem = f", margem {_rs(t['margem_ha'])}/ha" if t["receita"] else ""
        linhas.append(f"• {t['nome']}: {_rs(t['custo_ha'])}/ha{margem}")
    for a in p["alertas"][:2]:
        linhas.append(f"⚠️ {a['texto']}")
    return "\n".join(linhas)


def _numero_br(s: str) -> float | None:
    m = re.search(r"([\d.,]+)\s*(mil)?", s)
    if not m:
        return None
    n = m.group(1)
    n = n.replace(".", "").replace(",", ".") if "," in n else (n.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", n) else n)
    try:
        return float(n) * (1000 if m.group(2) else 1)
    except ValueError:
        return None


def _novo_registro(con, jid: str, msg_id: str, rascunho: dict, origem: str) -> str:
    t, lt, b = db.talhoes(con), db.lotes(con), db.bombas(con)
    alvo = extracao.resolver_alvo(rascunho, t, lt, b)
    itens = [it for it in rascunho.get("itens", []) if it.get("descricao") or it.get("valor_total")]
    if not itens:
        return "Não consegui entender o que lançar. Pode escrever, por exemplo: _passei 200 kg de ureia no talhão 3 por 640 reais_."
    estado = {"msg_id": msg_id, "itens": itens, "alvo": alvo, "data": rascunho.get("data"),
              "origem": origem, "anexo": rascunho.get("anexo")}
    return _proximo_passo(con, jid, estado)


def responder_texto(con, jid: str, msg_id: str, texto: str, origem: str = "texto") -> str:
    """Resposta para uma mensagem de texto (ou áudio já transcrito)."""
    t = _sem_acento(texto)
    estado = _estado(con, jid)

    if t in ("cancelar", "cancela", "nao", "não"):
        _guardar(con, jid, None)
        return "Cancelado. Nada foi salvo."
    if t in ("oi", "ola", "ajuda", "menu", "bom dia", "boa tarde", "boa noite"):
        return AJUDA
    if t in ("resumo", "painel", "custos"):
        return _resumo(con)

    if estado:
        espera = estado.get("aguardando")
        if espera == "confirmar":
            if t in ("sim", "s", "ok", "isso", "pode", "confirmo"):
                return _salvar(con, jid, estado)
            if t in ("outro", "outra", "trocar", "mudar"):
                estado["alvo"] = None
                return _proximo_passo(con, jid, estado)
        elif espera == "alvo":
            ops = estado.get("opcoes", [])
            if t.isdigit() and 1 <= int(t) <= len(ops):
                o = ops[int(t) - 1]
                estado["alvo"] = {"alvo_tipo": o["alvo_tipo"], "alvo_id": o["alvo_id"]}
                return _salvar(con, jid, estado)
            if re.fullmatch(r"\d+", t):
                return f"Responda um número de 1 a {len(ops)}, ou *cancelar*."
        elif espera == "valor":
            v = _numero_br(t)
            if v and v > 0:
                estado["itens"][estado["item_valor"]]["valor_total"] = v
                return _proximo_passo(con, jid, estado)
            return "Não entendi o valor. Escreva só o número, por exemplo *640* ou *1.250,50*."

    # mensagem nova: vira um registro (substitui o que estava pendente)
    try:
        rascunho = extracao.ler_texto(texto, extracao.cadastro_texto(db.talhoes(con), db.lotes(con), db.bombas(con)))
    except extracao.LeituraIndisponivel as e:
        return f"Não consegui ler agora: {e} Mande de novo daqui a pouco."
    return _novo_registro(con, jid, msg_id, rascunho, origem)


def responder_imagem(con, jid: str, msg_id: str, imagem: bytes, media_type: str, legenda: str | None) -> str:
    db.ANEXOS.mkdir(parents=True, exist_ok=True)
    anexo = f"wa-{msg_id}.jpg"
    (db.ANEXOS / anexo).write_bytes(imagem)
    if not extracao.ia_disponivel():
        if legenda:
            return responder_texto(con, jid, msg_id, legenda, origem="foto")
        return ("Recebi a foto e guardei. A leitura automática de notas está desligada agora, "
                "então escreva em uma frase o que é, por exemplo: _2.000 kg de ureia, R$ 6.400, talhão 3_.")
    try:
        rascunho = extracao.ler_imagem(imagem, media_type,
                                       extracao.cadastro_texto(db.talhoes(con), db.lotes(con), db.bombas(con)), legenda)
    except extracao.LeituraIndisponivel as e:
        return f"Não consegui ler a foto agora: {e}"
    rascunho["anexo"] = anexo
    return _novo_registro(con, jid, msg_id, rascunho, origem="foto")


def tratar_webhook(con, corpo: dict) -> tuple[str, str] | None:
    """Processa um evento da Evolution. Devolve (jid, resposta) ou None se não há o que responder."""
    if corpo.get("event") != "messages.upsert":
        return None
    dados = corpo.get("data") or {}
    chave = dados.get("key") or {}
    jid = chave.get("remoteJid") or ""
    if chave.get("fromMe") or jid.endswith("@g.us") or jid.endswith("@broadcast") or not jid:
        return None
    msg_id = chave.get("id") or datetime.now().strftime("%Y%m%d%H%M%S%f")
    m = dados.get("message") or {}

    if "imageMessage" in m:
        import base64
        b64 = m.get("base64")
        if not b64:
            return jid, "Recebi a foto, mas ela veio sem o conteúdo. Ative o envio em base64 no webhook da Evolution."
        img = m["imageMessage"]
        return jid, responder_imagem(con, jid, msg_id, base64.b64decode(b64), img.get("mimetype", "image/jpeg").split(";")[0],
                                     img.get("caption"))
    if "audioMessage" in m:
        transcrito = (m.get("speechToText") or "").removeprefix("[audio]").strip()
        if transcrito:
            return jid, responder_texto(con, jid, msg_id, transcrito, origem="audio")
        return jid, ("Recebi o áudio, mas ainda não consigo ouvir. Escreva em uma frase, por exemplo: "
                     "_passei 200 kg de ureia no talhão 3 por 640 reais_.")
    texto = m.get("conversation") or (m.get("extendedTextMessage") or {}).get("text")
    if texto:
        return jid, responder_texto(con, jid, msg_id, texto)
    return jid, "Por enquanto entendo texto, foto e áudio. " + AJUDA.split("\n\n")[1]
