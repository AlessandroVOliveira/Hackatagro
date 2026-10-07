"""Onde gastar primeiro: nota de prioridade de cada foco de annoni e o plano da semana.

A regra vem da ecologia de invasões: os focos pequenos, novos e isolados
("satélites") são os que fazem a invasão avançar e são os mais baratos de
eliminar. A mancha grande e antiga se contém (não deixar sementear) e se
recupera aos poucos.

Nota de 0 a 100, só com regras:
  tamanho do foco          até 40  (menor = mais barato e mais urgente)
  perto de vetor           até 25  (estrada, porteira, corredor, mangueira, embarcadouro)
  perto de campo limpo     até 25  (o que ainda dá para proteger)
  foco isolado (satélite)  10
"""

from __future__ import annotations

from datetime import date, timedelta

from . import geo

# Parâmetros editáveis. Valores de referência para a demonstração.
PARAM = {
    "mao_de_obra_h": 30.0,          # R$ por hora de peão (diária de ~R$ 240)
    "horas_semana": 12.0,           # horas que dá para dedicar ao annoni por semana
    "kg_pv_recuperacao_ha": 243,    # custo do Mirapasto em kg de peso vivo por ha (Embrapa)
    "preco_kg_pv": 10.0,            # R$ por kg de peso vivo
    "revisita_dias": 60,            # o banco de sementes dura mais de 20 anos: voltar ao foco
    "sementes_planta_ano": 80_000,  # Embrapa
}

# (até m², rótulo, pontos, horas, insumo R$)
CLASSES = [
    (1, "touceira isolada", 40, 0.5, 0),
    (10, "foco pequeno", 34, 2, 30),
    (100, "foco médio", 20, 6, 150),
]
MANCHA = "mancha estabelecida"


def classe(area_m2: float | None) -> tuple[str, int, float, float]:
    a = area_m2 or 1
    for limite, rot, pts, h, ins in CLASSES:
        if a <= limite:
            return rot, pts, h, ins
    return MANCHA, 6, 0, 0


def epoca_de_sementes(d: date) -> bool:
    """O annoni espiga e solta semente de outubro a maio."""
    return d.month >= 10 or d.month <= 5


def custo_recuperar_ha() -> float:
    return PARAM["kg_pv_recuperacao_ha"] * PARAM["preco_kg_pv"]


def _vetores(feicoes):
    linhas, pontos = [], []
    for f in feicoes:
        if f["tipo"] in ("estrada", "corredor"):
            linhas.append((f["nome"], f["km"], f["tipo"]))
        elif f["tipo"] == "vetor":
            pontos.append((f["nome"], f["km"], f["subtipo"]))
    return linhas, pontos


def vetor_mais_proximo(p, feicoes) -> tuple[str, float, str] | None:
    linhas, pontos = _vetores(feicoes)
    cands = [(n, geo.dist_linha(p, km), t) for n, km, t in linhas] + [(n, geo.dist(p, km), t) for n, km, t in pontos]
    return min(cands, key=lambda c: c[1]) if cands else None


def avaliar(oc: dict, feicoes: list[dict], ativos: list[dict]) -> dict:
    """Nota e explicação de um foco de annoni."""
    p = oc["km"]
    rot, pts_tam, horas, insumo = classe(oc.get("area_m2"))
    partes = [{"fator": rot, "pontos": pts_tam}]

    v = vetor_mais_proximo(p, feicoes)
    pts_v = 0
    if v:
        nome, d, _ = v
        m = d * 1000
        pts_v = 25 if m <= 50 else 18 if m <= 200 else 8 if m <= 500 else 0
        if pts_v:
            partes.append({"fator": f"a {_metros(m)} {_artigo(nome)}", "pontos": pts_v})

    limpos = [f for f in feicoes if f["tipo"] == "campo_limpo"]
    pts_c = 0
    if limpos:
        f = min(limpos, key=lambda f: geo.dist_poligono(p, f["km"]))
        m = geo.dist_poligono(p, f["km"]) * 1000
        pts_c = 25 if m <= 100 else 15 if m <= 500 else 6 if m <= 1000 else 0
        if pts_c:
            nome_c = f["nome"][0].lower() + f["nome"][1:]
            partes.append({"fator": ("dentro do " if m == 0 else f"a {_metros(m)} do ") + nome_c, "pontos": pts_c})

    outros = [o for o in ativos if o["id"] != oc["id"]]
    viz = min((geo.dist(p, o["km"]) for o in outros), default=99) * 1000
    pts_s = 10 if viz >= 500 and rot != MANCHA else 0
    if pts_s:
        partes.append({"fator": "foco isolado, na frente de avanço", "pontos": pts_s})

    nota = pts_tam + pts_v + pts_c + pts_s
    if rot == MANCHA:
        ha = (oc.get("area_m2") or 0) / 10_000
        acao = "Conter: roçar antes de sementear e não tirar gado dali sem quarentena. Recuperar com o método Mirapasto (Embrapa)."
        custo = round(max(ha, 0.01) * custo_recuperar_ha(), 2)
    else:
        acao = ("Arrancar com a raiz e ensacar as sementes" if rot == "touceira isolada"
                else "Arrancar ou aplicar herbicida só no foco, com receituário agronômico")
        custo = round(horas * PARAM["mao_de_obra_h"] + insumo, 2)
    return {"nota": nota, "classe": rot, "partes": partes, "acao": acao, "custo": custo, "horas": horas,
            "mancha": rot == MANCHA, "vetor": v[0] if v else None, "pts_campo": pts_c}


def _metros(m: float) -> str:
    if m < 1000:
        return f"{max(5, round(m / 5) * 5):.0f} m"
    return f"{m / 1000:.1f} km".replace(".", ",")


def _artigo(nome: str) -> str:
    return ("da " if nome.split()[0] in ("Estrada", "Porteira", "Mangueira") else "do ") + nome


def plano(ocorrencias: list[dict], feicoes: list[dict], hoje: date, propriedade_id: int | None = None) -> dict:
    """Plano da semana: focos a eliminar dentro das horas disponíveis, manchas a conter e revisitas."""
    annoni = [o for o in ocorrencias if o["tipo"] == "annoni" and o["status"] != "descartada"]
    ativos = [o for o in annoni if o["situacao"] == "ativo"]
    meus = [o for o in ativos if propriedade_id is None or o["propriedade_id"] == propriedade_id]
    avaliados = sorted(({**o, "prioridade": avaliar(o, feicoes, ativos)} for o in meus),
                       key=lambda o: (-o["prioridade"]["nota"], -o["prioridade"]["pts_campo"], o["observado_em"]))
    focos = [o for o in avaliados if not o["prioridade"]["mancha"]]
    manchas = [o for o in avaliados if o["prioridade"]["mancha"]]

    semana, horas = [], 0.0
    for o in focos:
        h = o["prioridade"]["horas"]
        if horas + h > PARAM["horas_semana"] and semana:
            continue
        semana.append(o)
        horas += h
        if len(semana) == 5:
            break
    depois = [o for o in focos if o not in semana]

    revisitas = []
    for o in annoni:
        if o["situacao"] != "eliminado" or (propriedade_id is not None and o["propriedade_id"] != propriedade_id):
            continue
        base = date.fromisoformat(o["revisado_em"] or o["eliminado_em"])
        vence = base + timedelta(days=PARAM["revisita_dias"])
        if vence <= hoje + timedelta(days=7):
            revisitas.append({**o, "revisita_em": vence.isoformat(), "atrasada": vence < hoje})

    custo_semana = sum(o["prioridade"]["custo"] for o in semana)
    area_manchas = sum((o.get("area_m2") or 0) for o in manchas) / 10_000
    return {
        "epoca_sementes": epoca_de_sementes(hoje),
        "semana": semana, "depois": depois, "manchas": manchas, "revisitas": revisitas,
        "resumo": {
            "focos_semana": len(semana), "custo_semana": round(custo_semana, 2), "horas_semana": horas,
            "focos_ativos": len(focos), "manchas": len(manchas), "area_manchas_ha": round(area_manchas, 2),
            "custo_recuperar_manchas": round(area_manchas * custo_recuperar_ha(), 2),
            "custo_recuperar_ha": custo_recuperar_ha(),
            "sementes_evitadas": len(semana) * PARAM["sementes_planta_ano"],
        },
        "parametros": PARAM,
    }
