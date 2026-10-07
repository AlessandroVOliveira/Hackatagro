"""Banco SQLite e a propriedade fictícia da demonstração."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "data"
ARQUIVO = Path(os.environ.get("CONTA_TALHAO_DB", PASTA / "fazenda.db"))
ANEXOS = PASTA / "anexos"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS talhoes (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, area_ha REAL NOT NULL, cultura TEXT, poligono TEXT
);
CREATE TABLE IF NOT EXISTS bombas (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, uc TEXT, talhoes TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lotes (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, cabecas INTEGER NOT NULL, poligono TEXT
);
CREATE TABLE IF NOT EXISTS lancamentos (
  id INTEGER PRIMARY KEY,
  client_id TEXT UNIQUE NOT NULL,
  data TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('custo', 'receita')),
  categoria TEXT NOT NULL,
  descricao TEXT NOT NULL,
  quantidade REAL, unidade TEXT,
  valor REAL NOT NULL,
  alvo_tipo TEXT NOT NULL CHECK (alvo_tipo IN ('talhao', 'lote', 'bomba', 'geral')),
  alvo_id INTEGER,
  origem TEXT NOT NULL DEFAULT 'manual',
  anexo TEXT,
  criado_em TEXT NOT NULL
);
"""


def conectar(arquivo: Path | str = ARQUIVO) -> sqlite3.Connection:
    Path(arquivo).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(arquivo, check_same_thread=False)
    con.row_factory = sqlite3.Row
    if str(arquivo) != ":memory:":
        con.execute("PRAGMA journal_mode=WAL")  # leituras e escritas de threads diferentes sem travar
    con.execute("PRAGMA busy_timeout=5000")
    con.executescript(ESQUEMA)
    return con


def talhoes(con) -> list[dict]:
    return [{**dict(r), "poligono": json.loads(r["poligono"] or "[]")} for r in con.execute("SELECT * FROM talhoes ORDER BY id")]


def bombas(con) -> list[dict]:
    return [{**dict(r), "talhoes": json.loads(r["talhoes"])} for r in con.execute("SELECT * FROM bombas ORDER BY id")]


def lotes(con) -> list[dict]:
    return [{**dict(r), "poligono": json.loads(r["poligono"] or "[]")} for r in con.execute("SELECT * FROM lotes ORDER BY id")]


def lancamentos(con, alvo_tipo: str | None = None, alvo_id: int | None = None, limite: int | None = None) -> list[dict]:
    sql, args = "SELECT * FROM lancamentos", []
    if alvo_tipo:
        sql += " WHERE alvo_tipo = ?"
        args.append(alvo_tipo)
        if alvo_id is not None:
            sql += " AND alvo_id = ?"
            args.append(alvo_id)
    sql += " ORDER BY data DESC, id DESC"
    if limite:
        sql += f" LIMIT {int(limite)}"
    return [dict(r) for r in con.execute(sql, args)]


def inserir_lancamento(con, lanc: dict) -> tuple[dict, bool]:
    """Grava um lançamento. Reenvio do mesmo client_id não duplica (sincronização offline)."""
    existente = con.execute("SELECT * FROM lancamentos WHERE client_id = ?", (lanc["client_id"],)).fetchone()
    if existente:
        return dict(existente), False
    campos = ["client_id", "data", "tipo", "categoria", "descricao", "quantidade", "unidade", "valor",
              "alvo_tipo", "alvo_id", "origem", "anexo"]
    valores = [lanc.get(c) for c in campos] + [datetime.now().isoformat(timespec="seconds")]
    cur = con.execute(
        f"INSERT INTO lancamentos ({', '.join(campos)}, criado_em) VALUES ({', '.join('?' * (len(campos) + 1))})",
        valores,
    )
    con.commit()
    return dict(con.execute("SELECT * FROM lancamentos WHERE id = ?", (cur.lastrowid,)).fetchone()), True


def apagar_lancamento(con, lanc_id: int) -> bool:
    cur = con.execute("DELETE FROM lancamentos WHERE id = ?", (lanc_id,))
    con.commit()
    return cur.rowcount > 0


# ------------------------------------------------------------ fazenda fictícia

TALHOES = [
    # nome, área, polígono no mapa (viewBox 1000 x 620)
    ("Talhão 1 Coxilha", 80, [[60, 70], [395, 50], [410, 280], [72, 300]]),
    ("Talhão 2 Banhado", 60, [[72, 322], [410, 302], [428, 520], [92, 560]]),
    ("Talhão 3 Beira-rio", 90, [[440, 290], [770, 262], [800, 520], [452, 548]]),
    ("Talhão 4 Sanga", 70, [[425, 52], [750, 34], [764, 240], [438, 268]]),
]
BOMBAS = [("Bomba do açude", "3012456", [1, 2]), ("Bomba do rio", "3012457", [3]), ("Bomba da sanga", "3012458", [4])]
LOTES = [
    ("Novilhos", 120, [[790, 34], [962, 26], [970, 236], [780, 246]]),
    ("Vacas de cria", 200, [[812, 268], [962, 258], [972, 566], [830, 566]]),
]

# Custo por hectare de cada talhão (R$/ha), perto dos R$ 15 mil/ha do desafio.
# Talhão 2 gasta mais defensivo; talhão 3 tem a bomba mais gastona.
POR_HA = {
    "sementes": {1: 900, 2: 900, 3: 900, 4: 900},
    "adubo": {1: 2250, 2: 2250, 3: 2250, 4: 2250},
    "defensivos": {1: 1800, 2: 2600, 3: 1800, 4: 1800},
    "agua": {1: 1384, 2: 1384, 3: 1384, 4: 1384},
    "arrendamento": {1: 2500, 2: 2500, 3: 2500, 4: 2500},
}
ENERGIA_HA = {1: 1124, 2: 1124, 3: 1911, 4: 1050}  # por bomba, ver BOMBAS
GERAIS_HA = {"combustivel": 1100, "maquinas": 1500, "mao_de_obra": 1600, "outros": 400}
SACAS_HA = {1: 185, 2: 140, 3: 172, 4: 182}
VENDAS = [("2026-04-15", 0.30, 66.0), ("2026-07-20", 0.30, 80.0), ("2026-09-18", 0.40, 94.0)]

ITENS = {
    "sementes": [("Semente de arroz IRGA 424 RI", "kg", 4.50, 1.0, "2025-09-20")],
    "adubo": [("Ureia 45% N", "kg", 3.20, 0.55, "2025-10-05"), ("NPK 05-20-20", "kg", 3.80, 0.45, "2025-09-28")],
    "defensivos": [("Herbicida pré-emergente", "L", 95.0, 0.45, "2025-10-18"), ("Fungicida brusone", "L", 160.0, 0.55, "2026-01-12")],
    "agua": [("Taxa de água da associação de irrigantes", None, None, 1.0, "2025-11-10")],
    "arrendamento": [("Arrendamento safra 25/26", None, None, 1.0, "2025-08-30")],
}
MESES_LUZ = ["2025-11-30", "2025-12-31", "2026-01-31", "2026-02-28", "2026-03-31"]
PESO_LUZ = [0.12, 0.24, 0.27, 0.24, 0.13]
GERAIS_DESC = {"combustivel": "Óleo diesel", "maquinas": "Manutenção de máquinas e peças",
               "mao_de_obra": "Folha de pagamento", "outros": "Assistência técnica e seguro"}
MESES_GERAIS = ["2025-09-30", "2025-11-30", "2026-01-31", "2026-03-31", "2026-05-31"]


def _lanc(data, tipo, cat, desc, valor, alvo_tipo, alvo_id, qtd=None, un=None):
    return {"client_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"seed/{data}/{cat}/{desc}/{alvo_tipo}/{alvo_id}")),
            "data": data, "tipo": tipo, "categoria": cat, "descricao": desc, "quantidade": qtd, "unidade": un,
            "valor": round(valor, 2), "alvo_tipo": alvo_tipo, "alvo_id": alvo_id, "origem": "exemplo", "anexo": None}


def semear(con) -> None:
    """Cria a propriedade fictícia se o banco estiver vazio."""
    if con.execute("SELECT COUNT(*) FROM talhoes").fetchone()[0]:
        return
    for nome, area, pol in TALHOES:
        con.execute("INSERT INTO talhoes (nome, area_ha, cultura, poligono) VALUES (?, ?, 'arroz irrigado', ?)",
                    (nome, area, json.dumps(pol)))
    for nome, uc, ids in BOMBAS:
        con.execute("INSERT INTO bombas (nome, uc, talhoes) VALUES (?, ?, ?)", (nome, uc, json.dumps(ids)))
    for nome, cab, pol in LOTES:
        con.execute("INSERT INTO lotes (nome, cabecas, poligono) VALUES (?, ?, ?)", (nome, cab, json.dumps(pol)))

    area = {i + 1: t[1] for i, t in enumerate(TALHOES)}
    ls = []
    for cat, por_t in POR_HA.items():
        for tid, rha in por_t.items():
            total = rha * area[tid]
            for desc, un, preco, frac, data in ITENS[cat]:
                v = total * frac
                ls.append(_lanc(data, "custo", cat, desc, v, "talhao", tid, round(v / preco) if preco else None, un))
    for b_id, (nome, _, ids) in enumerate(BOMBAS, start=1):
        total = sum(ENERGIA_HA[t] * area[t] for t in ids)
        for data, peso in zip(MESES_LUZ, PESO_LUZ):
            v = total * peso
            ls.append(_lanc(data, "custo", "energia", f"Conta de luz {nome.lower()}", v, "bomba", b_id, round(v / 0.85), "kWh"))
    area_total = sum(area.values())
    for cat, rha in GERAIS_HA.items():
        for data in MESES_GERAIS:
            v = rha * area_total / len(MESES_GERAIS)
            qtd, un = (round(v / 6.4), "L") if cat == "combustivel" else (None, None)
            ls.append(_lanc(data, "custo", cat, GERAIS_DESC[cat], v, "geral", None, qtd, un))
    for tid, sha in SACAS_HA.items():
        sacas = sha * area[tid]
        for data, frac, preco in VENDAS:
            sc = round(sacas * frac)
            ls.append(_lanc(data, "receita", "venda_arroz", f"Romaneio de venda de arroz em casca, R$ {preco:.0f}/saca",
                            sc * preco, "talhao", tid, sc, "sc"))
    # gado
    ls += [
        _lanc("2025-08-15", "custo", "outros", "Compra de 120 terneiros para recria", 240_000, "lote", 1, 120, "cab"),
        _lanc("2025-10-10", "custo", "suplementacao", "Sal mineral proteinado", 21_000, "lote", 1, 7000, "kg"),
        _lanc("2026-05-12", "custo", "suplementacao", "Suplemento de inverno", 15_000, "lote", 1, 5000, "kg"),
        _lanc("2025-09-05", "custo", "sanidade", "Vacinas e vermífugo", 12_000, "lote", 1, 240, "un"),
        _lanc("2026-08-28", "receita", "venda_gado", "Venda de novilhos para frigorífico", 414_000, "lote", 1, 120, "cab"),
        _lanc("2025-10-10", "custo", "suplementacao", "Sal mineral", 30_000, "lote", 2, 10000, "kg"),
        _lanc("2025-09-05", "custo", "sanidade", "Vacinas, vermífugo e carrapaticida", 16_000, "lote", 2, 400, "un"),
        _lanc("2026-04-22", "receita", "venda_gado", "Venda de terneiros desmamados", 189_000, "lote", 2, 90, "cab"),
    ]
    for lanc in ls:
        inserir_lancamento(con, lanc)
    con.commit()
