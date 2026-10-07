"""Banco SQLite e a vizinhança fictícia da demonstração.

Geometrias ficam em latitude/longitude (como vêm do GPS do celular). As contas
de distância usam quilômetros (geo.para_km).
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from . import geo

PASTA = Path(__file__).resolve().parent.parent / "data"
ARQUIVO = Path(os.environ.get("RONDA_DB", PASTA / "ronda.db"))
FOTOS = PASTA / "fotos"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS propriedades (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, responsavel TEXT, atividade TEXT,
  poligono TEXT NOT NULL, whatsapp TEXT, compartilha_exato INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS feicoes (
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('estrada', 'arroio', 'corredor', 'vetor', 'campo_limpo')),
  subtipo TEXT, nome TEXT, geometria TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ocorrencias (
  id INTEGER PRIMARY KEY,
  client_id TEXT UNIQUE NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('annoni', 'javali')),
  subtipo TEXT NOT NULL,
  lat REAL NOT NULL, lon REAL NOT NULL,
  area_m2 REAL, animais INTEGER, prejuizo REAL,
  obs TEXT, foto TEXT,
  propriedade_id INTEGER, autor_id INTEGER,
  status TEXT NOT NULL DEFAULT 'confirmada' CHECK (status IN ('suspeita', 'confirmada', 'descartada')),
  situacao TEXT NOT NULL DEFAULT 'ativo' CHECK (situacao IN ('ativo', 'eliminado')),
  eliminado_em TEXT, revisado_em TEXT, custo_real REAL,
  triagem_ia TEXT,
  observado_em TEXT NOT NULL,
  criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS avisos (
  id INTEGER PRIMARY KEY,
  propriedade_id INTEGER,            -- nulo: coordenação do sindicato
  tipo TEXT NOT NULL, texto TEXT NOT NULL,
  ocorrencia_id INTEGER, dispositivo_id INTEGER,
  criado_em TEXT NOT NULL, lido INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS dispositivos (
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('armadilha', 'camera')),
  nome TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
  estado TEXT NOT NULL, atualizado_em TEXT NOT NULL,
  rodizio TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS eventos_dispositivo (
  id INTEGER PRIMARY KEY, dispositivo_id INTEGER NOT NULL, evento TEXT NOT NULL, criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS controladores (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, municipio TEXT, contato TEXT, registro TEXT
);
CREATE TABLE IF NOT EXISTS movimentos (
  id INTEGER PRIMARY KEY,
  client_id TEXT UNIQUE NOT NULL,
  propriedade_id INTEGER NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('gado', 'maquina')),
  descricao TEXT NOT NULL,
  origem_id INTEGER, origem_texto TEXT,
  risco TEXT NOT NULL,
  chegada TEXT NOT NULL, liberar_em TEXT,
  criado_em TEXT NOT NULL
);
"""


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def conectar(arquivo: Path | str = ARQUIVO) -> sqlite3.Connection:
    Path(arquivo).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(arquivo, check_same_thread=False)
    con.row_factory = sqlite3.Row
    if str(arquivo) != ":memory:":
        con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    con.executescript(ESQUEMA)
    return con


# ------------------------------------------------------------------ leitura

def _km(pontos):
    return [geo.para_km(lat, lon) for lat, lon in pontos]


def propriedades(con) -> list[dict]:
    out = []
    for r in con.execute("SELECT * FROM propriedades ORDER BY id"):
        pol = json.loads(r["poligono"])
        out.append({**dict(r), "poligono": pol, "km": _km(pol), "compartilha_exato": bool(r["compartilha_exato"])})
    return out


def feicoes(con) -> list[dict]:
    out = []
    for r in con.execute("SELECT * FROM feicoes ORDER BY id"):
        g = json.loads(r["geometria"])
        km = geo.para_km(*g) if r["tipo"] == "vetor" else _km(g)
        out.append({**dict(r), "geometria": g, "km": km})
    return out


def _ocorrencia(r) -> dict:
    d = dict(r)
    d["km"] = geo.para_km(r["lat"], r["lon"])
    d["triagem_ia"] = json.loads(r["triagem_ia"]) if r["triagem_ia"] else None
    return d


def ocorrencias(con, tipo: str | None = None, desde: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM ocorrencias WHERE 1=1", []
    if tipo:
        sql += " AND tipo = ?"
        args.append(tipo)
    if desde:
        sql += " AND observado_em >= ?"
        args.append(desde)
    sql += " ORDER BY observado_em DESC, id DESC"
    return [_ocorrencia(r) for r in con.execute(sql, args)]


def ocorrencia(con, oid: int) -> dict | None:
    r = con.execute("SELECT * FROM ocorrencias WHERE id = ?", (oid,)).fetchone()
    return _ocorrencia(r) if r else None


def dispositivos(con) -> list[dict]:
    return [{**dict(r), "rodizio": json.loads(r["rodizio"]), "km": geo.para_km(r["lat"], r["lon"])}
            for r in con.execute("SELECT * FROM dispositivos ORDER BY id")]


def dispositivo(con, did: int) -> dict | None:
    return next((d for d in dispositivos(con) if d["id"] == did), None)


def controladores(con) -> list[dict]:
    return [dict(r) for r in con.execute("SELECT * FROM controladores ORDER BY id")]


def avisos(con, propriedade_id: int | None, limite: int = 40) -> list[dict]:
    if propriedade_id is None:
        rs = con.execute("SELECT * FROM avisos WHERE propriedade_id IS NULL ORDER BY criado_em DESC, id DESC LIMIT ?", (limite,))
    else:
        rs = con.execute("SELECT * FROM avisos WHERE propriedade_id = ? ORDER BY criado_em DESC, id DESC LIMIT ?",
                         (propriedade_id, limite))
    return [dict(r) for r in rs]


def movimentos(con, propriedade_id: int | None) -> list[dict]:
    if propriedade_id is None:
        rs = con.execute("SELECT * FROM movimentos ORDER BY chegada DESC, id DESC")
    else:
        rs = con.execute("SELECT * FROM movimentos WHERE propriedade_id = ? ORDER BY chegada DESC, id DESC", (propriedade_id,))
    return [dict(r) for r in rs]


# ------------------------------------------------------------------ escrita

CAMPOS_OCORRENCIA = ["client_id", "tipo", "subtipo", "lat", "lon", "area_m2", "animais", "prejuizo", "obs", "foto",
                     "propriedade_id", "autor_id", "status", "situacao", "eliminado_em", "revisado_em", "custo_real",
                     "observado_em"]


def inserir_ocorrencia(con, oc: dict) -> tuple[dict, bool]:
    """Grava uma ocorrência. Reenvio do mesmo client_id não duplica (fila offline)."""
    r = con.execute("SELECT * FROM ocorrencias WHERE client_id = ?", (oc["client_id"],)).fetchone()
    if r:
        return _ocorrencia(r), False
    valores = [oc.get(c) for c in CAMPOS_OCORRENCIA]
    valores[CAMPOS_OCORRENCIA.index("status")] = oc.get("status") or "confirmada"
    valores[CAMPOS_OCORRENCIA.index("situacao")] = oc.get("situacao") or "ativo"
    cur = con.execute(
        f"INSERT INTO ocorrencias ({', '.join(CAMPOS_OCORRENCIA)}, criado_em) "
        f"VALUES ({', '.join('?' * (len(CAMPOS_OCORRENCIA) + 1))})",
        valores + [agora()],
    )
    con.commit()
    return ocorrencia(con, cur.lastrowid), True


def atualizar_ocorrencia(con, oid: int, **campos) -> dict | None:
    if campos:
        sets = ", ".join(f"{k} = ?" for k in campos)
        con.execute(f"UPDATE ocorrencias SET {sets} WHERE id = ?", [*campos.values(), oid])
        con.commit()
    return ocorrencia(con, oid)


def inserir_aviso(con, propriedade_id, tipo, texto, ocorrencia_id=None, dispositivo_id=None, criado_em=None) -> None:
    con.execute(
        "INSERT INTO avisos (propriedade_id, tipo, texto, ocorrencia_id, dispositivo_id, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
        (propriedade_id, tipo, texto, ocorrencia_id, dispositivo_id, criado_em or agora()),
    )


def marcar_lidos(con, propriedade_id: int | None) -> None:
    if propriedade_id is None:
        con.execute("UPDATE avisos SET lido = 1 WHERE propriedade_id IS NULL")
    else:
        con.execute("UPDATE avisos SET lido = 1 WHERE propriedade_id = ?", (propriedade_id,))
    con.commit()


def registrar_evento(con, did: int, evento: str, estado: str) -> None:
    con.execute("INSERT INTO eventos_dispositivo (dispositivo_id, evento, criado_em) VALUES (?, ?, ?)", (did, evento, agora()))
    con.execute("UPDATE dispositivos SET estado = ?, atualizado_em = ? WHERE id = ?", (estado, agora(), did))
    con.commit()


def eventos(con, did: int, limite: int = 10) -> list[dict]:
    return [dict(r) for r in con.execute(
        "SELECT * FROM eventos_dispositivo WHERE dispositivo_id = ? ORDER BY criado_em DESC, id DESC LIMIT ?", (did, limite))]


def inserir_movimento(con, mov: dict) -> tuple[dict, bool]:
    r = con.execute("SELECT * FROM movimentos WHERE client_id = ?", (mov["client_id"],)).fetchone()
    if r:
        return dict(r), False
    campos = ["client_id", "propriedade_id", "tipo", "descricao", "origem_id", "origem_texto", "risco", "chegada", "liberar_em"]
    cur = con.execute(
        f"INSERT INTO movimentos ({', '.join(campos)}, criado_em) VALUES ({', '.join('?' * (len(campos) + 1))})",
        [mov.get(c) for c in campos] + [agora()],
    )
    con.commit()
    return dict(con.execute("SELECT * FROM movimentos WHERE id = ?", (cur.lastrowid,)).fetchone()), True


# ------------------------------------------------------------------ vizinhança fictícia
# Coordenadas em km a partir do canto sudoeste (geo.LAT0, geo.LON0).

ESTRADA_GERAL = [(0, 5.2), (2, 5.45), (4, 5.6), (6, 5.45), (8, 5.3), (10, 5.6), (12, 5.9), (14, 5.75), (16, 5.6)]
RINCAO_N = [(8, 5.3), (7.95, 8.5), (7.85, 11)]
RINCAO_S = [(8, 5.3), (7.75, 2.5), (7.5, 0)]
ARROIO = [(0, 8.4), (1.5, 8.9), (3, 8.6), (4.5, 9.2), (6, 9.0), (7.5, 8.4), (9, 8.1), (10.5, 8.6), (12, 8.9),
          (13.5, 8.2), (16, 7.8)]


def _y_estrada(x: float) -> float:
    for (x1, y1), (x2, y2) in zip(ESTRADA_GERAL, ESTRADA_GERAL[1:]):
        if x1 <= x <= x2:
            return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    return ESTRADA_GERAL[-1][1]


def _divisa(x: float, topo: float) -> list[tuple[float, float]]:
    return [(x, _y_estrada(x)), (x, topo)]


def _faixa(esq, dir_):
    """Propriedade entre duas divisas que saem da Estrada Geral (para o norte ou para o sul)."""
    x1, x2 = esq[0][0], dir_[0][0]
    estrada = [esq[0]] + [p for p in ESTRADA_GERAL if x1 < p[0] < x2] + [dir_[0]]
    return estrada + dir_[1:] + list(reversed(esq[1:]))


N, S = geo.ALTURA_KM, 0.0
PROPRIEDADES = [
    # nome, responsável, atividade, divisa oeste, divisa leste
    ("Estância Três Capões", "Seu Valdir", "ovinos e gado de cria", _divisa(0, N), _divisa(4.5, N)),
    ("Fazenda Boa Vista", "Dona Marlene", "gado de corte", _divisa(4.5, N), RINCAO_N),
    ("Granja São Pedro", "Paulo e Rafael", "arroz irrigado e gado", RINCAO_N, _divisa(12, N)),
    ("Estância do Cerro", "Seu Aldo", "gado de cria em campo nativo", _divisa(12, N), _divisa(16, N)),
    ("Fazenda Rincão Grande", "Seu Ivo", "gado de corte", _divisa(0, S), _divisa(4, S)),
    ("Estância Santa Clara", "Dona Cleusa", "gado de cria e ovinos", _divisa(4, S), RINCAO_S),
    ("Fazenda Coxilha Bonita", "Seu Nestor", "recria e soja", RINCAO_S, _divisa(11.5, S)),
    ("Estância São Jorge", "Família Prates", "gado de corte", _divisa(11.5, S), _divisa(16, S)),
]

VETORES = [  # pontos por onde a semente entra: porteiras, mangueiras, embarcadouro
    ("porteira", "Porteira da Três Capões", (3.0, 5.55)), ("porteira", "Porteira da Boa Vista", (6.3, 5.47)),
    ("porteira", "Porteira da São Pedro", (9.6, 5.55)), ("porteira", "Porteira do Cerro", (13.0, 5.85)),
    ("porteira", "Porteira do Rincão Grande", (2.0, 5.45)), ("porteira", "Porteira da Santa Clara", (5.2, 5.5)),
    ("porteira", "Porteira da Coxilha Bonita", (10.5, 5.65)), ("porteira", "Porteira da São Jorge", (14.5, 5.72)),
    ("mangueira", "Mangueira do Rincão Grande", (1.6, 3.5)), ("mangueira", "Mangueira da Santa Clara", (5.6, 4.3)),
    ("mangueira", "Mangueira do Cerro", (13.6, 7.0)),
    ("embarcadouro", "Embarcadouro do cruzamento", (8.25, 5.1)),
]
CORREDORES = [
    ("Corredor do Rincão Grande", [(2.0, 5.45), (1.8, 4.5), (1.6, 3.5)]),
    ("Corredor da Santa Clara", [(5.2, 5.5), (5.4, 4.9), (5.6, 4.3)]),
    ("Corredor do Cerro", [(13.0, 5.85), (13.3, 6.5), (13.6, 7.0)]),
]
CAMPOS_LIMPOS = [
    ("Campo nativo do Cerro", [(12.6, 9.3), (15.7, 8.6), (15.7, 10.8), (12.6, 10.8)]),
    ("Campo nativo da Santa Clara", [(4.6, 1.0), (7.0, 1.0), (7.25, 3.8), (4.8, 4.0)]),
    ("Campo nativo da Boa Vista", [(5.0, 6.5), (7.3, 6.3), (7.4, 8.0), (5.1, 8.2)]),
]

# Annoni: (x, y, área m², subtipo, status, situação, dias atrás, observação)
ANNONI = [
    (0.8, 5.0, 6000, "mancha", "confirmada", "ativo", 400, "Mancha antiga na beira da estrada, já tomou o potreiro."),
    (1.7, 5.1, 2500, "mancha", "confirmada", "ativo", 380, "Mancha na frente da porteira."),
    (2.6, 4.85, 1200, "mancha", "confirmada", "ativo", 300, None),
    (1.5, 3.75, 800, "mancha", "confirmada", "ativo", 250, "Em volta da mangueira."),
    (3.6, 5.35, 30, "foco", "confirmada", "ativo", 40, "Beira da estrada, algumas touceiras juntas."),
    (4.3, 5.42, 4, "foco", "confirmada", "ativo", 12, "Beira da estrada."),
    (5.25, 5.38, 1, "touceira", "suspeita", "ativo", 3, "Touceira do lado da porteira, não tenho certeza."),
    (5.5, 4.45, 6, "foco", "confirmada", "ativo", 9, "No corredor, perto da mangueira."),
    (6.35, 5.62, 2, "touceira", "confirmada", "ativo", 15, None),
    (8.15, 5.15, 15, "foco", "confirmada", "ativo", 20, "Do lado do embarcadouro."),
    (9.65, 5.7, 1, "touceira", "suspeita", "ativo", 2, None),
    (13.1, 6.15, 3, "foco", "confirmada", "ativo", 6, "Na entrada do corredor."),
    (13.35, 9.05, 1, "touceira", "suspeita", "ativo", 1, "O campeiro achou uma touceira na beira do campo nativo."),
    (11.0, 5.75, 40, "foco", "confirmada", "ativo", 30, "Beira da estrada."),
    (2.2, 6.3, 8, "foco", "confirmada", "ativo", 25, None),
    (4.9, 5.48, 3, "foco", "confirmada", "eliminado", 150, None),
    (6.9, 5.5, 1, "touceira", "confirmada", "eliminado", 45, None),
    (12.4, 6.05, 5, "foco", "confirmada", "eliminado", 200, None),
    (10.2, 3.0, 2, "touceira", "descartada", "ativo", 35, "Era outra gramínea nativa."),
]
ELIMINADO = {15: (120, None), 16: (20, None), 17: (190, 70)}  # índice: (dias desde a eliminação, dias desde a revisita)

DISPOSITIVOS = [
    ("armadilha", "Curral coletivo do Arroio", (4.2, 8.45), "aberta", [1, 2, 3, 5]),
    ("camera", "Câmera da sanga", (2.8, 8.25), "ativa", []),
    ("camera", "Câmera da lavoura", (9.6, 7.75), "ativa", []),
]
CONTROLADORES = [
    ("Controlador A (exemplo)", "Alegrete", "(55) 9 0000-0001", "CR e CTF/Ibama ativos"),
    ("Controlador B (exemplo)", "Alegrete", "(55) 9 0000-0002", "CR e CTF/Ibama ativos"),
]

VALOR_OVINO = 3_100_000 / 6_255  # R$ por ovino, do caso de Sant'Ana do Livramento citado no desafio


def _ll(p):
    return list(geo.para_latlon(*p))


def _javali(hoje: date) -> list[dict]:
    """Registros de javali ao longo do arroio, quase todos à noite."""
    rnd = random.Random(7)
    focos = [(3.4, 8.7, 0.9, 14), (5.0, 8.9, 0.8, 9), (9.7, 8.2, 0.7, 9), (1.5, 8.7, 0.6, 4)]
    tipos = [("rastro", 10), ("fucada", 8), ("avistamento", 4), ("lavoura", 0), ("ataque_criacao", 0)]
    out = []
    for cx, cy, r, n in focos:
        for _ in range(n):
            x = cx + rnd.uniform(-r, r)
            y = cy + rnd.uniform(-0.45, 0.35)
            dias = rnd.randint(1, 58)
            hora = rnd.choice([20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 5, 6, 19])
            sub = rnd.choices([t for t, _ in tipos], [w for _, w in tipos])[0]
            oc = {"subtipo": sub, "x": x, "y": y, "dias": dias, "hora": hora, "animais": None, "prejuizo": None}
            if sub == "avistamento":
                oc["animais"] = rnd.randint(3, 9)
            out.append(oc)
    # danos com valor
    out += [
        {"subtipo": "ataque_criacao", "x": 2.6, "y": 8.0, "dias": 41, "hora": 3, "animais": 4, "obs": "Ovelhas mortas no potreiro da sanga."},
        {"subtipo": "ataque_criacao", "x": 3.3, "y": 7.9, "dias": 19, "hora": 4, "animais": 6, "obs": "Cordeiros atacados de madrugada."},
        {"subtipo": "ataque_criacao", "x": 2.9, "y": 8.15, "dias": 4, "hora": 2, "animais": 3, "obs": None},
        {"subtipo": "lavoura", "x": 9.3, "y": 7.7, "dias": 12, "hora": 22, "prejuizo": 3800, "obs": "Quadro recém semeado revirado."},
        {"subtipo": "lavoura", "x": 10.1, "y": 7.9, "dias": 2, "hora": 1, "prejuizo": 2400, "obs": "Taipa fuçada."},
    ]
    for oc in out:
        if oc["subtipo"] == "ataque_criacao":
            oc["prejuizo"] = round(oc["animais"] * VALOR_OVINO, 2)
    return out


def _quando(hoje: date, dias: int, hora: int) -> str:
    return datetime.combine(hoje - timedelta(days=dias), datetime.min.time()).replace(hour=hora).isoformat(timespec="seconds")


def _dono(con, p) -> int | None:
    for pr in propriedades(con):
        if geo.dentro(p, pr["km"]):
            return pr["id"]
    return None


def semear(con, hoje: date | None = None) -> None:
    """Cria a vizinhança fictícia se o banco estiver vazio."""
    if con.execute("SELECT COUNT(*) FROM propriedades").fetchone()[0]:
        return
    hoje = hoje or date.today()
    for i, (nome, resp, ativ, esq, dir_) in enumerate(PROPRIEDADES):
        pol = [_ll(p) for p in _faixa(esq, dir_)]
        con.execute("INSERT INTO propriedades (nome, responsavel, atividade, poligono, compartilha_exato) VALUES (?, ?, ?, ?, ?)",
                    (nome, resp, ativ, json.dumps(pol), 1 if i == 4 else 0))
    con.execute("INSERT INTO feicoes (tipo, nome, geometria) VALUES ('estrada', 'Estrada Geral', ?)",
                (json.dumps([_ll(p) for p in ESTRADA_GERAL]),))
    con.execute("INSERT INTO feicoes (tipo, nome, geometria) VALUES ('estrada', 'Estrada do Rincão', ?)",
                (json.dumps([_ll(p) for p in list(reversed(RINCAO_N)) + RINCAO_S[1:]]),))
    con.execute("INSERT INTO feicoes (tipo, nome, geometria) VALUES ('arroio', 'Arroio das Pedras', ?)",
                (json.dumps([_ll(p) for p in ARROIO]),))
    for nome, linha in CORREDORES:
        con.execute("INSERT INTO feicoes (tipo, nome, geometria) VALUES ('corredor', ?, ?)", (nome, json.dumps([_ll(p) for p in linha])))
    for sub, nome, p in VETORES:
        con.execute("INSERT INTO feicoes (tipo, subtipo, nome, geometria) VALUES ('vetor', ?, ?, ?)", (sub, nome, json.dumps(_ll(p))))
    for nome, pol in CAMPOS_LIMPOS:
        con.execute("INSERT INTO feicoes (tipo, nome, geometria) VALUES ('campo_limpo', ?, ?)", (nome, json.dumps([_ll(p) for p in pol])))
    for tipo, nome, p, estado, rod in DISPOSITIVOS:
        lat, lon = geo.para_latlon(*p)
        con.execute("INSERT INTO dispositivos (tipo, nome, lat, lon, estado, atualizado_em, rodizio) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tipo, nome, lat, lon, estado, _quando(hoje, 6, 17), json.dumps(rod)))
    con.execute("INSERT INTO eventos_dispositivo (dispositivo_id, evento, criado_em) VALUES (1, 'armada', ?)", (_quando(hoje, 6, 17),))
    for nome, mun, cont, reg in CONTROLADORES:
        con.execute("INSERT INTO controladores (nome, municipio, contato, registro) VALUES (?, ?, ?, ?)", (nome, mun, cont, reg))
    con.commit()

    ids = []
    for i, (x, y, area, sub, status, sit, dias, obs) in enumerate(ANNONI):
        lat, lon = geo.para_latlon(x, y)
        oc = {"client_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"seed/annoni/{i}")), "tipo": "annoni", "subtipo": sub,
              "lat": lat, "lon": lon, "area_m2": area, "obs": obs, "status": status, "situacao": sit,
              "propriedade_id": _dono(con, (x, y)), "observado_em": _quando(hoje, dias, 9 + i % 7)}
        oc["autor_id"] = oc["propriedade_id"]
        if i in ELIMINADO:
            de, dr = ELIMINADO[i]
            oc["eliminado_em"] = (hoje - timedelta(days=de)).isoformat()
            oc["revisado_em"] = (hoje - timedelta(days=dr)).isoformat() if dr else None
            oc["custo_real"] = 40.0
        ids.append(inserir_ocorrencia(con, oc)[0])
    for i, j in enumerate(_javali(hoje)):
        lat, lon = geo.para_latlon(j["x"], j["y"])
        dono = _dono(con, (j["x"], j["y"]))
        oc = {"client_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"seed/javali/{i}")), "tipo": "javali", "subtipo": j["subtipo"],
              "lat": lat, "lon": lon, "animais": j.get("animais"), "prejuizo": j.get("prejuizo"), "obs": j.get("obs"),
              "propriedade_id": dono, "autor_id": dono, "observado_em": _quando(hoje, j["dias"], j["hora"])}
        ids.append(inserir_ocorrencia(con, oc)[0])

    # avisos das duas últimas semanas, como se tivessem sido gerados na hora
    from . import avisos as av
    limite = (hoje - timedelta(days=14)).isoformat()
    for oc in sorted(ids, key=lambda o: o["observado_em"]):
        if oc["observado_em"] >= limite and oc["status"] != "descartada":
            av.ocorrencia_nova(con, oc, enviar=False, criado_em=oc["observado_em"])
    con.commit()
