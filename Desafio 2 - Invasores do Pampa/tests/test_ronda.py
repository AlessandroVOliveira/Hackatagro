import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["RONDA_DB"] = str(Path(tempfile.mkdtemp()) / "teste.db")
for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "EVOLUTION_APIKEY", "RONDA_SENSOR_TOKEN"):
    os.environ.pop(var, None)

from fastapi.testclient import TestClient  # noqa: E402

from ronda import geo, prioridade  # noqa: E402
from ronda.api import app  # noqa: E402

c = TestClient(app)
SANTA_CLARA, CERRO, SAO_JORGE = 6, 4, 8


def registrar(x, y, tipo="annoni", subtipo="touceira", perfil=CERRO, client_id=None, **extra):
    lat, lon = geo.para_latlon(x, y)
    dados = {"client_id": client_id or os.urandom(8).hex(), "tipo": tipo, "subtipo": subtipo,
             "lat": lat, "lon": lon, "perfil": str(perfil), **extra}
    return c.post("/api/ocorrencias", data={"dados": json.dumps(dados)})


# ------------------------------------------------------------------ prioridade

FEICOES = [
    {"tipo": "estrada", "nome": "Estrada", "km": [(0, 0), (10, 0)]},
    {"tipo": "campo_limpo", "nome": "Campo nativo", "km": [(0, 2), (2, 2), (2, 4), (0, 4)]},
]


def oc(i, x, y, area):
    return {"id": i, "km": (x, y), "area_m2": area}


def test_foco_pequeno_isolado_passa_na_frente_da_mancha():
    mancha, satelite = oc(1, 5, 0.01, 5000), oc(2, 1, 1.95, 1)
    ativos = [mancha, satelite]
    a = prioridade.avaliar(mancha, FEICOES, ativos)
    b = prioridade.avaliar(satelite, FEICOES, ativos)
    assert a["mancha"] and not b["mancha"]
    assert b["nota"] > a["nota"]
    assert b["pts_campo"] == 25  # a 50 m do campo limpo


def test_custo_da_mancha_e_o_da_recuperacao():
    a = prioridade.avaliar(oc(1, 5, 5, 10_000), FEICOES, [])
    assert a["custo"] == pytest.approx(prioridade.custo_recuperar_ha())


def test_epoca_de_sementes():
    assert prioridade.epoca_de_sementes(date(2026, 10, 7))
    assert not prioridade.epoca_de_sementes(date(2026, 7, 1))


def test_plano_respeita_horas_da_semana():
    ocs = [{"id": i, "tipo": "annoni", "status": "confirmada", "situacao": "ativo", "km": (i * 2.0, 8),
            "area_m2": 50, "observado_em": "2026-10-01T10:00:00", "propriedade_id": 1} for i in range(5)]
    p = prioridade.plano(ocs, FEICOES, date(2026, 10, 7))
    assert p["resumo"]["horas_semana"] <= prioridade.PARAM["horas_semana"]
    assert len(p["semana"]) + len(p["depois"]) == 5


# ------------------------------------------------------------------ privacidade

def test_vizinho_ve_annoni_alheio_so_por_quadricula():
    m = c.get(f"/api/mapa?perfil={SANTA_CLARA}").json()
    sind = c.get("/api/mapa?perfil=sindicato").json()
    assert m["celulas"], "focos de vizinhos devem aparecer agregados"
    assert sum(1 for o in m["exatos"] if o["tipo"] == "annoni") < sum(1 for o in sind["exatos"] if o["tipo"] == "annoni")
    assert all("propriedade_id" not in o for o in m["exatos"])
    assert sind["celulas"] == []


# ------------------------------------------------------------------ registro e avisos

def test_registro_offline_reenviado_nao_duplica():
    r1 = registrar(14.6, 9.6, client_id="fila-offline-01")
    r2 = registrar(14.6, 9.6, client_id="fila-offline-01")
    assert r1.status_code == 200 and r1.json()["novo"]
    assert r2.json()["novo"] is False
    assert r1.json()["ocorrencia"]["status"] == "suspeita"


def test_aviso_ao_vizinho_nao_diz_de_quem_e_a_terra():
    r = registrar(13.8, 6.0, perfil=CERRO, subtipo="foco")  # dentro do Cerro, perto da divisa com o São Jorge
    assert r.json()["avisados"] >= 1
    textos = [a["texto"] for a in c.get(f"/api/avisos?perfil={SAO_JORGE}").json()]
    assert any("Capim-annoni" in t for t in textos)
    assert not any("Estância do Cerro" in t or "Seu Aldo" in t for t in textos)


def test_ponto_fora_da_vizinhanca_e_recusado():
    assert registrar(40, 40).status_code == 422


def test_ataque_calcula_prejuizo_por_ovino():
    r = registrar(2.8, 8.0, tipo="javali", subtipo="ataque_criacao", perfil=1, animais=2).json()
    assert r["ocorrencia"]["prejuizo"] == pytest.approx(2 * 3_100_000 / 6_255, abs=0.01)


def test_eliminar_e_rebrotar():
    oid = registrar(14.0, 10.0).json()["ocorrencia"]["id"]
    assert c.post(f"/api/ocorrencias/{oid}/eliminar", json={}).json()["situacao"] == "eliminado"
    assert c.post(f"/api/ocorrencias/{oid}/revisar", json={"rebrota": True}).json()["situacao"] == "ativo"


# ------------------------------------------------------------------ armadilha e prevenção

def test_sensor_da_armadilha_avisa_responsavel_e_coordenacao():
    r = c.post("/api/dispositivos/1/sensor", json={"evento": "fechou"}).json()
    assert r["estado"] == "fechada" and r["avisados"] == 2
    assert "fechou" in c.get("/api/avisos?perfil=sindicato").json()[0]["texto"]
    c.post("/api/dispositivos/1/sensor", json={"evento": "armada"})


def test_gado_de_origem_com_annoni_entra_em_quarentena():
    base = {"propriedade_id": SANTA_CLARA, "tipo": "gado", "descricao": "Terneiros", "chegada": "2026-10-07"}
    alto = c.post("/api/movimentos", json={**base, "client_id": "mov-00000001", "origem_id": 5}).json()
    assert alto["risco"] == "alto" and alto["liberar_em"] == "2026-10-17"
    fora = c.post("/api/movimentos", json={**base, "client_id": "mov-00000002"}).json()
    assert fora["risco"] == "desconhecido"
