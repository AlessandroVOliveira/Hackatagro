"""Rateio de custos e resultado por talhão e por lote.

Regras de rateio:
- lançamento num talhão ou lote: vai inteiro para ele;
- conta de luz de uma bomba: dividida entre os talhões que a bomba irriga,
  proporcional à área;
- gasto geral da lavoura (mão de obra fixa, manutenção, diesel sem destino):
  dividido entre todos os talhões, proporcional à área.
"""

from __future__ import annotations

from collections import defaultdict

CATEGORIAS_CUSTO = {
    "sementes": "Sementes",
    "adubo": "Adubo",
    "defensivos": "Defensivos",
    "energia": "Energia",
    "agua": "Água",
    "combustivel": "Combustível",
    "maquinas": "Máquinas e manutenção",
    "mao_de_obra": "Mão de obra",
    "arrendamento": "Arrendamento",
    "sanidade": "Sanidade animal",
    "suplementacao": "Sal e suplementação",
    "outros": "Outros",
}
CATEGORIAS_RECEITA = {"venda_arroz": "Venda de arroz", "venda_gado": "Venda de gado", "outras_receitas": "Outras receitas"}

# Um talhão chama atenção quando gasta este tanto acima da média da fazenda por hectare.
LIMITE_ALERTA = 1.30
CATEGORIAS_ALERTA = {
    "energia": "verificar a lâmina d'água ou a eficiência da bomba",
    "adubo": "conferir a recomendação de adubação e a análise de solo",
    "defensivos": "revisar o manejo de pragas e doenças",
}


def _destinos(lanc: dict, talhoes: dict, bombas: dict) -> list[tuple[str, int, float]]:
    """Para onde vai o valor de um lançamento: lista de (tipo, id, fração)."""
    tipo, alvo = lanc["alvo_tipo"], lanc.get("alvo_id")
    if tipo in ("talhao", "lote"):
        return [(tipo, alvo, 1.0)]
    if tipo == "bomba":
        ids = bombas[alvo]["talhoes"]
    else:  # geral
        ids = list(talhoes)
    area = sum(talhoes[i]["area_ha"] for i in ids)
    return [("talhao", i, talhoes[i]["area_ha"] / area) for i in ids]


def ratear(talhoes: list[dict], bombas: list[dict], lotes: list[dict], lancamentos: list[dict]) -> dict:
    """Soma custos, receitas e produção de cada talhão e lote após o rateio."""
    t_idx = {t["id"]: t for t in talhoes}
    b_idx = {b["id"]: b for b in bombas}
    base = lambda: {"custos": defaultdict(float), "receita": 0.0, "sacas": 0.0, "cabecas_vendidas": 0.0}  # noqa: E731
    res = {"talhao": {i: base() for i in t_idx}, "lote": {lt["id"]: base() for lt in lotes}}

    for lanc in lancamentos:
        for tipo, alvo, frac in _destinos(lanc, t_idx, b_idx):
            acc = res[tipo][alvo]
            valor = lanc["valor"] * frac
            if lanc["tipo"] == "custo":
                acc["custos"][lanc["categoria"]] += valor
            else:
                acc["receita"] += valor
                qtd = (lanc.get("quantidade") or 0) * frac
                if lanc["categoria"] == "venda_arroz" and lanc.get("unidade") == "sc":
                    acc["sacas"] += qtd
                elif lanc["categoria"] == "venda_gado" and lanc.get("unidade") == "cab":
                    acc["cabecas_vendidas"] += qtd
    return res


def _div(a: float, b: float) -> float | None:
    return a / b if b else None


def painel(talhoes: list[dict], bombas: list[dict], lotes: list[dict], lancamentos: list[dict]) -> dict:
    r = ratear(talhoes, bombas, lotes, lancamentos)
    area_total = sum(t["area_ha"] for t in talhoes)

    linhas_t = []
    for t in talhoes:
        acc = r["talhao"][t["id"]]
        custo = sum(acc["custos"].values())
        linhas_t.append({
            "id": t["id"], "nome": t["nome"], "area_ha": t["area_ha"], "cultura": t.get("cultura"),
            "custo": custo, "custo_ha": custo / t["area_ha"],
            "receita": acc["receita"], "sacas": acc["sacas"],
            "sacas_ha": acc["sacas"] / t["area_ha"],
            "custo_saca": _div(custo, acc["sacas"]),
            "preco_medio": _div(acc["receita"], acc["sacas"]),
            "margem": acc["receita"] - custo,
            "margem_ha": (acc["receita"] - custo) / t["area_ha"],
            "por_categoria": {k: v for k, v in sorted(acc["custos"].items(), key=lambda kv: -kv[1])},
        })

    linhas_l = []
    for lt in lotes:
        acc = r["lote"][lt["id"]]
        custo = sum(acc["custos"].values())
        linhas_l.append({
            "id": lt["id"], "nome": lt["nome"], "cabecas": lt["cabecas"],
            "custo": custo, "custo_cabeca": custo / lt["cabecas"],
            "receita": acc["receita"], "cabecas_vendidas": acc["cabecas_vendidas"],
            "resultado": acc["receita"] - custo,
            "resultado_cabeca": (acc["receita"] - custo) / lt["cabecas"],
            "por_categoria": {k: v for k, v in sorted(acc["custos"].items(), key=lambda kv: -kv[1])},
        })

    custo_total = sum(x["custo"] for x in linhas_t)
    receita_total = sum(x["receita"] for x in linhas_t)
    sacas_total = sum(x["sacas"] for x in linhas_t)
    fazenda = {
        "area_ha": area_total, "custo": custo_total, "custo_ha": custo_total / area_total,
        "receita": receita_total, "margem": receita_total - custo_total,
        "sacas": sacas_total, "custo_saca": _div(custo_total, sacas_total),
        "media_categoria_ha": {
            cat: sum(x["por_categoria"].get(cat, 0) for x in linhas_t) / area_total
            for cat in CATEGORIAS_CUSTO
        },
    }
    return {"talhoes": linhas_t, "lotes": linhas_l, "fazenda": fazenda, "alertas": alertas(linhas_t, fazenda)}


def alertas(linhas_t: list[dict], fazenda: dict) -> list[dict]:
    """Avisos que viram decisão: gasto muito acima da média e margem negativa."""
    out = []
    for t in linhas_t:
        for cat, acao in CATEGORIAS_ALERTA.items():
            media = fazenda["media_categoria_ha"].get(cat, 0)
            valor_ha = t["por_categoria"].get(cat, 0) / t["area_ha"]
            if media and valor_ha > media * LIMITE_ALERTA:
                acima = valor_ha / media - 1
                out.append({
                    "talhao_id": t["id"], "tipo": cat, "gravidade": acima,
                    "texto": f"{t['nome']} gastou {acima:.0%} mais {CATEGORIAS_CUSTO[cat].lower()} "
                             f"por hectare que a média da fazenda: {acao}.",
                })
        if t["receita"] > 0 and t["margem"] < 0:
            out.append({
                "talhao_id": t["id"], "tipo": "margem", "gravidade": -t["margem_ha"] / max(t["custo_ha"], 1),
                "texto": f"{t['nome']} fechou a safra com margem negativa de "
                         f"R$ {abs(t['margem_ha']):,.0f}/ha: avaliar manejo ou rotação com soja.".replace(",", "."),
            })
    return sorted(out, key=lambda a: -a["gravidade"])
