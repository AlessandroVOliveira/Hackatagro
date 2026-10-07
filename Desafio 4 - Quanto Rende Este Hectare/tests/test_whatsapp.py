"""Conversa no WhatsApp com eventos no formato da Evolution API v2 (messages.upsert)."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
    os.environ.pop(var, None)

from conta_talhao import db, whatsapp  # noqa: E402

JID = "5555999990000@s.whatsapp.net"


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "ANEXOS", tmp_path / "anexos")
    c = db.conectar(":memory:")
    db.semear(c)
    return c


def evento(texto=None, msg_id="ABC1", jid=JID, from_me=False, **mensagem):
    m = dict(mensagem)
    if texto is not None:
        m["conversation"] = texto
    return {"event": "messages.upsert", "instance": "conta-talhao",
            "data": {"key": {"remoteJid": jid, "fromMe": from_me, "id": msg_id}, "pushName": "Produtor",
                     "message": m, "messageType": "conversation"}}


def falar(con, texto, msg_id="ABC1"):
    jid, resposta = whatsapp.tratar_webhook(con, evento(texto, msg_id))
    assert jid == JID
    return resposta


def custo_talhao(con, tid):
    return sum(l["valor"] for l in db.lancamentos(con, "talhao", tid) if l["tipo"] == "custo")


def test_frase_completa_pede_confirmacao_e_salva(con):
    antes = custo_talhao(con, 3)
    r = falar(con, "passei 200 kg de ureia no talhão 3 por 640 reais")
    assert "Talhão 3 Beira-rio" in r and "sim" in r
    r = falar(con, "sim", "ABC2")
    assert r.startswith("✅ Salvo em *Talhão 3 Beira-rio*")
    assert "/ha" in r
    assert custo_talhao(con, 3) == pytest.approx(antes + 640)


def test_sem_valor_e_sem_talhao_pergunta_os_dois(con):
    r = falar(con, "comprei 500 litros de diesel")
    assert "valor total" in r
    r = falar(con, "3.200,00", "ABC2")
    assert "Responda o número" in r and "Geral da lavoura" in r
    geral_antes = len(db.lancamentos(con, "geral"))
    r = falar(con, "5", "ABC3")  # 4 talhões, 2 lotes, então 7 = geral; 5 = lote Novilhos
    assert "lote Novilhos" in r
    assert len(db.lancamentos(con, "geral")) == geral_antes


def test_numero_fora_da_lista(con):
    falar(con, "comprei 500 litros de diesel por 3200 reais")
    assert "de 1 a" in falar(con, "42", "X2")


def test_cancelar_nao_salva(con):
    total = len(db.lancamentos(con))
    falar(con, "passei 200 kg de ureia no talhão 3 por 640 reais")
    assert "Cancelado" in falar(con, "cancelar", "X2")
    assert len(db.lancamentos(con)) == total


def test_reenvio_do_mesmo_evento_nao_duplica(con):
    falar(con, "passei 200 kg de ureia no talhão 3 por 640 reais", "DUP1")
    falar(con, "sim", "DUP2")
    total = len(db.lancamentos(con))
    falar(con, "passei 200 kg de ureia no talhão 3 por 640 reais", "DUP1")
    falar(con, "sim", "DUP2")
    assert len(db.lancamentos(con)) == total


def test_resumo(con):
    r = falar(con, "resumo")
    assert "Talhão 1 Coxilha" in r and "⚠️" in r


def test_ignora_mensagem_propria_e_grupo(con):
    assert whatsapp.tratar_webhook(con, evento("oi", from_me=True)) is None
    assert whatsapp.tratar_webhook(con, evento("oi", jid="123-456@g.us")) is None
    assert whatsapp.tratar_webhook(con, {"event": "connection.update", "data": {}}) is None


def test_audio_transcrito_pela_evolution(con):
    ev = evento(audioMessage={"seconds": 4}, speechToText="[audio] passei 200 kg de ureia no talhão 3 por 640 reais")
    jid, r = whatsapp.tratar_webhook(con, ev)
    assert "Talhão 3 Beira-rio" in r


def test_audio_sem_transcricao_pede_texto(con):
    jid, r = whatsapp.tratar_webhook(con, evento(audioMessage={"seconds": 4}))
    assert "Escreva" in r


def test_foto_sem_ia_guarda_anexo_e_usa_legenda(con):
    import base64
    ev = evento(imageMessage={"mimetype": "image/jpeg", "caption": "ureia 2000 kg talhão 1 por R$ 6.400"},
                base64=base64.b64encode(b"\xff\xd8\xff").decode())
    jid, r = whatsapp.tratar_webhook(con, ev)
    assert "Talhão 1 Coxilha" in r and "6.400,00" in r
    assert (db.ANEXOS / "wa-ABC1.jpg").exists()


def test_webhook_http_exige_token(monkeypatch):
    from fastapi.testclient import TestClient
    from conta_talhao import api
    monkeypatch.setattr(whatsapp, "WEBHOOK_TOKEN", "segredo")
    enviados = []
    monkeypatch.setattr(whatsapp, "enviar", lambda jid, txt: enviados.append((jid, txt)))
    c = TestClient(api.app)
    assert c.post("/api/whatsapp/webhook", json=evento("oi")).status_code == 401
    assert c.post("/api/whatsapp/webhook", json=evento("oi"), headers={"x-webhook-token": "segredo"}).status_code == 200
    assert enviados and enviados[0][0] == JID
