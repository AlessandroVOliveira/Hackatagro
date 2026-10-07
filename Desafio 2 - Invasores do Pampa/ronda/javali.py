"""Javali: por onde o bando passa, em que horário e quanto já custou.

Os registros dos vizinhos formam as rotas. Quadrículas de 1 km com mais sinais
recentes são os lugares para a câmera de trilha e a armadilha coletiva.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from . import geo

PESO = {"ataque_criacao": 3, "lavoura": 3, "avistamento": 2, "rastro": 1, "fucada": 1}
COBERTURA_KM = 0.8  # câmera ou armadilha a menos disso já cobre a quadrícula


def resumo(ocorrencias: list[dict], dispositivos: list[dict], hoje: date, dias: int = 60) -> dict:
    desde = (hoje - timedelta(days=dias)).isoformat()
    js = [o for o in ocorrencias if o["tipo"] == "javali" and o["observado_em"] >= desde]
    horas = [0] * 24
    for o in js:
        horas[datetime.fromisoformat(o["observado_em"]).hour] += 1
    noite = sum(horas[h] for h in list(range(18, 24)) + list(range(0, 6)))

    cel = {}
    for o in js:
        idade = (hoje - datetime.fromisoformat(o["observado_em"]).date()).days
        peso = PESO.get(o["subtipo"], 1) * (1.0 if idade <= 30 else 0.5)
        c = geo.celula(o["km"])
        d = cel.setdefault(c, {"celula": c, "peso": 0.0, "n": 0, "tipos": Counter(), "pontos": []})
        d["peso"] += peso
        d["n"] += 1
        d["tipos"][o["subtipo"]] += 1
        d["pontos"].append(o["km"])
    quentes = sorted(cel.values(), key=lambda d: -d["peso"])
    for d in quentes:
        cx = sum(p[0] for p in d["pontos"]) / d["n"]
        cy = sum(p[1] for p in d["pontos"]) / d["n"]
        d["centro"] = (round(cx, 3), round(cy, 3))
        d["latlon"] = geo.para_latlon(cx, cy)
        perto = [x for x in dispositivos if geo.dist((cx, cy), x["km"]) <= COBERTURA_KM]
        d["coberto_por"] = [x["nome"] for x in perto]
        d["tipos"] = dict(d["tipos"])
        d["peso"] = round(d["peso"], 1)
        del d["pontos"]

    ataques = [o for o in js if o["subtipo"] == "ataque_criacao"]
    return {
        "dias": dias,
        "registros": len(js),
        "por_tipo": dict(Counter(o["subtipo"] for o in js)),
        "animais_mortos": sum(o.get("animais") or 0 for o in ataques),
        "prejuizo": round(sum(o.get("prejuizo") or 0 for o in js), 2),
        "pct_noite": round(100 * noite / len(js)) if js else 0,
        "horas": horas,
        "quentes": quentes[:6],
        "sem_cobertura": [d for d in quentes[:4] if not d["coberto_por"]],
    }
