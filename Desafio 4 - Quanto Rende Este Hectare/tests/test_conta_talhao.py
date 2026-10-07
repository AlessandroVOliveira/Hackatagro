import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["CONTA_TALHAO_DB"] = str(Path(tempfile.mkdtemp()) / "teste.db")
for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
    os.environ.pop(var, None)

from conta_talhao import extracao, motor  # noqa: E402

TALHOES = [{"id": 1, "nome": "Talhão 1", "area_ha": 30}, {"id": 2, "nome": "Talhão 2", "area_ha": 10}]
BOMBAS = [{"id": 1, "nome": "Bomba A", "uc": "123", "talhoes": [1, 2]}]
LOTES = [{"id": 1, "nome": "Novilhos", "cabecas": 10}]


def lanc(valor, alvo_tipo, alvo_id=None, categoria="adubo", tipo="custo", **kw):
    return {"valor": valor, "alvo_tipo": alvo_tipo, "alvo_id": alvo_id, "categoria": categoria, "tipo": tipo, **kw}


# ------------------------------------------------------------------ rateio

def test_conta_da_bomba_divide_por_area():
    r = motor.ratear(TALHOES, BOMBAS, LOTES, [lanc(1000, "bomba", 1, "energia")])
    assert r["talhao"][1]["custos"]["energia"] == pytest.approx(750)
    assert r["talhao"][2]["custos"]["energia"] == pytest.approx(250)


def test_gasto_geral_divide_entre_todos_os_talhoes():
    r = motor.ratear(TALHOES, BOMBAS, LOTES, [lanc(400, "geral", None, "mao_de_obra")])
    assert r["talhao"][1]["custos"]["mao_de_obra"] == pytest.approx(300)
    assert r["lote"][1]["custos"] == {}


def test_painel_custo_por_saca_e_margem():
    ls = [lanc(3000, "talhao", 2), lanc(5000, "talhao", 2, "venda_arroz", "receita", quantidade=50, unidade="sc")]
    t2 = motor.painel(TALHOES, BOMBAS, LOTES, ls)["talhoes"][1]
    assert t2["custo_ha"] == 300
    assert t2["custo_saca"] == 60
    assert t2["preco_medio"] == 100
    assert t2["margem_ha"] == 200


def test_alerta_energia_acima_da_media():
    bombas = [{"id": 1, "nome": "A", "talhoes": [1]}, {"id": 2, "nome": "B", "talhoes": [2]}]
    ls = [lanc(3000, "bomba", 1, "energia"), lanc(2000, "bomba", 2, "energia")]  # 100/ha vs 200/ha
    al = motor.painel(TALHOES, bombas, LOTES, ls)["alertas"]
    assert len(al) == 1 and al[0]["talhao_id"] == 2 and "energia" in al[0]["texto"]


def test_alerta_margem_negativa():
    ls = [lanc(5000, "talhao", 1), lanc(4000, "talhao", 1, "venda_arroz", "receita", quantidade=40, unidade="sc")]
    al = motor.painel(TALHOES, BOMBAS, LOTES, ls)["alertas"]
    assert any(a["tipo"] == "margem" and a["talhao_id"] == 1 for a in al)


# --------------------------------------------------------- leitura por regras

@pytest.mark.parametrize("frase, categoria, qtd, un, valor, alvo", [
    ("passei 200 kg de ureia no talhão 3", "adubo", 200, "kg", None, "talhao 3"),
    ("Comprei 500 litros de diesel por R$ 3.200,00", "combustivel", 500, "L", 3200, None),
    ("vacina no lote dos novilhos, 120 doses, 960 reais", "sanidade", 120, "un", 960, "lote novilhos"),
    ("vendi 1.200 sacas do talhão 1 por 98.400", "venda_arroz", 1200, "sc", 98400, "talhao 1"),
    ("vendi 30 bois do lote novilhos por R$ 105 mil", "venda_gado", 30, "cab", 105000, "lote novilhos"),
])
def test_regras(frase, categoria, qtd, un, valor, alvo):
    r = extracao.ler_texto_regras(frase)
    item = r["itens"][0]
    assert item["categoria"] == categoria
    assert item["quantidade"] == qtd and item["unidade"] == un
    assert item["valor_total"] == valor
    assert r["alvo_mencionado"] == alvo


def test_resolver_alvo_por_nome_e_por_uc():
    talhoes = [{"id": 3, "nome": "Talhão 3 Beira-rio"}]
    lotes = [{"id": 1, "nome": "Novilhos"}]
    bombas = [{"id": 2, "nome": "Bomba do rio", "uc": "3012457"}]
    assert extracao.resolver_alvo({"alvo_mencionado": "talhão 3"}, talhoes, lotes, bombas) == {"alvo_tipo": "talhao", "alvo_id": 3}
    assert extracao.resolver_alvo({"alvo_mencionado": "lote dos novilhos"}, talhoes, lotes, bombas) == {"alvo_tipo": "lote", "alvo_id": 1}
    assert extracao.resolver_alvo({"unidade_consumidora": "301.245-7"}, talhoes, lotes, bombas) == {"alvo_tipo": "bomba", "alvo_id": 2}
    assert extracao.resolver_alvo({"alvo_mencionado": "talhão 9"}, talhoes, lotes, bombas) is None


# --------------------------------------------------------------------- API

@pytest.fixture(scope="module")
def cliente():
    from fastapi.testclient import TestClient
    from conta_talhao.api import app
    return TestClient(app)


def test_api_fluxo_texto_confirmar_painel(cliente):
    antes = cliente.get("/api/painel").json()["talhoes"][2]["custo"]
    r = cliente.post("/api/extrair", data={"texto": "passei 200 kg de ureia no talhão 3 por 640 reais"}).json()
    assert r["alvo"] == {"alvo_tipo": "talhao", "alvo_id": 3}
    item = r["itens"][0]
    corpo = [{"client_id": "teste-0001", "data": "2026-01-10", "categoria": item["categoria"],
              "descricao": item["descricao"], "quantidade": item["quantidade"], "unidade": item["unidade"],
              "valor": item["valor_total"], "alvo_tipo": "talhao", "alvo_id": 3, "origem": "texto"}]
    assert cliente.post("/api/lancamentos", json=corpo).json()[0]["novo"] is True
    # reenvio da fila offline não duplica
    assert cliente.post("/api/lancamentos", json=corpo).json()[0]["novo"] is False
    depois = cliente.get("/api/painel").json()["talhoes"][2]["custo"]
    assert depois == pytest.approx(antes + 640)


def test_api_foto_sem_ia_vira_rascunho_manual(cliente):
    r = cliente.post("/api/extrair", files={"arquivo": ("nota.jpg", b"\xff\xd8\xff fake", "image/jpeg")},
                     data={"dica": "conta_luz", "client_id": "teste-foto-1"}).json()
    assert r["fonte"] == "manual" and r["itens"][0]["categoria"] == "energia"
    assert r["anexo"] == "teste-foto-1.jpg"


def test_api_valida_destino(cliente):
    base = {"client_id": "teste-0002", "data": "2026-01-10", "categoria": "adubo", "descricao": "x", "valor": 10}
    assert cliente.post("/api/lancamentos", json=[{**base, "alvo_tipo": "talhao", "alvo_id": 99}]).status_code == 422
    assert cliente.post("/api/lancamentos", json=[{**base, "alvo_tipo": "bomba", "alvo_id": 1}]).status_code == 422


def test_api_relatorio_pdf(cliente):
    r = cliente.get("/api/relatorio.pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
