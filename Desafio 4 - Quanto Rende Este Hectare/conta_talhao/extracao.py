"""Transforma foto de nota, conta de luz, romaneio ou frase falada em rascunho
de lançamento. O produtor sempre confirma antes de salvar.

Com credencial da Anthropic, a leitura é feita pelo Claude (imagem e texto).
Sem credencial, o texto passa por regras simples e a foto vira um rascunho
vazio para o produtor preencher.
"""

from __future__ import annotations

import base64
import json
import os
import re
import unicodedata

from .motor import CATEGORIAS_CUSTO, CATEGORIAS_RECEITA

MODELO = "claude-opus-5-5"
CATEGORIAS = list(CATEGORIAS_CUSTO) + list(CATEGORIAS_RECEITA)

_NUM_OU_NULO = {"type": ["number", "null"]}
_TXT_OU_NULO = {"type": ["string", "null"]}

ESQUEMA = {
    "type": "object",
    "properties": {
        "documento": {"type": "string", "enum": ["nota_fiscal", "conta_luz", "romaneio", "venda_gado", "anotacao", "outro"]},
        "data": {"type": ["string", "null"], "description": "AAAA-MM-DD"},
        "fornecedor": _TXT_OU_NULO,
        "unidade_consumidora": {"type": ["string", "null"], "description": "Número da UC na conta de luz"},
        "alvo_mencionado": {"type": ["string", "null"], "description": "Talhão, lote ou bomba citado, como escrito"},
        "itens": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "descricao": {"type": "string"},
                    "categoria": {"type": "string", "enum": CATEGORIAS},
                    "quantidade": _NUM_OU_NULO,
                    "unidade": {"type": ["string", "null"], "description": "kg, t, L, sc, cab, kWh, un"},
                    "valor_total": _NUM_OU_NULO,
                },
                "required": ["descricao", "categoria", "quantidade", "unidade", "valor_total"],
                "additionalProperties": False,
            },
        },
        "observacao": _TXT_OU_NULO,
    },
    "required": ["documento", "data", "fornecedor", "unidade_consumidora", "alvo_mencionado", "itens", "observacao"],
    "additionalProperties": False,
}

SISTEMA = """Você lê documentos e anotações de uma propriedade rural do RS (arroz irrigado e gado de corte) \
e devolve os lançamentos de custo ou receita que eles representam.

Categorias de custo: {custos}.
Categorias de receita: {receitas}.

Regras:
- Uma linha de produto da nota é um item. Valores em reais, número puro (1.234,56 vira 1234.56).
- Conta de luz: um único item de categoria energia com o valor total da conta e o consumo em kWh.
- Romaneio ou nota de venda de arroz: categoria venda_arroz, quantidade em sacas de 50 kg (unidade "sc").
- Venda de gado: categoria venda_gado, quantidade em cabeças (unidade "cab").
- Ureia, NPK, cloreto, superfosfato: adubo. Herbicida, fungicida, inseticida: defensivos. Diesel: combustivel.
  Sal mineral, ração, suplemento: suplementacao. Vacina, vermífugo, carrapaticida: sanidade.
- Se o texto cita quantidade mas não valor, deixe valor_total nulo. Nunca invente valores.
- alvo_mencionado: copie como está escrito o talhão, lote ou bomba citado ("talhão 3", "lote dos novilhos"), ou nulo.

Talhões, lotes e bombas desta propriedade (para reconhecer os nomes): {cadastro}"""


def ia_disponivel() -> bool:
    """Há credencial para chamar a API? (chave, token ou perfil do `ant auth login`)."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    home = os.path.expanduser("~/.config/anthropic")
    return os.path.isdir(home) and any(os.scandir(home))


class LeituraIndisponivel(Exception):
    """A API não respondeu (sem sinal, limite ou erro). O item continua na fila."""


def _sistema(cadastro: str) -> str:
    return SISTEMA.format(
        custos=", ".join(CATEGORIAS_CUSTO), receitas=", ".join(CATEGORIAS_RECEITA), cadastro=cadastro
    )


def _chamar_claude(conteudo: list[dict], cadastro: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    try:
        resp = client.beta.messages.create(
            model=MODELO,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": ESQUEMA}},
            system=_sistema(cadastro),
            messages=[{"role": "user", "content": conteudo}],
        )
    except anthropic.RateLimitError as e:
        raise LeituraIndisponivel("Muitas leituras ao mesmo tempo. Tente de novo em instantes.") from e
    except anthropic.APIConnectionError as e:
        raise LeituraIndisponivel("Sem conexão com o serviço de leitura.") from e
    except anthropic.APIStatusError as e:
        raise LeituraIndisponivel(f"O serviço de leitura recusou o pedido ({e.status_code}).") from e

    if resp.stop_reason == "refusal":
        raise LeituraIndisponivel("Não foi possível ler este documento. Preencha os campos à mão.")
    texto = next((b.text for b in resp.content if b.type == "text"), None)
    if not texto:
        raise LeituraIndisponivel("A leitura voltou vazia. Preencha os campos à mão.")
    dados = json.loads(texto)
    dados["fonte"] = "ia"
    return dados


def ler_imagem(imagem: bytes, media_type: str, cadastro: str, dica: str | None = None) -> dict:
    if not ia_disponivel():
        return rascunho_vazio(dica)
    conteudo = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                     "data": base64.standard_b64encode(imagem).decode("ascii")}},
        {"type": "text", "text": "Leia este documento." + (f" O produtor indicou que é: {dica}." if dica else "")},
    ]
    return _chamar_claude(conteudo, cadastro)


def ler_texto(texto: str, cadastro: str) -> dict:
    if ia_disponivel():
        return _chamar_claude([{"type": "text", "text": f"Anotação do produtor: {texto}"}], cadastro)
    return ler_texto_regras(texto)


def rascunho_vazio(dica: str | None = None) -> dict:
    categoria = {"conta_luz": "energia", "romaneio": "venda_arroz", "venda_gado": "venda_gado"}.get(dica or "", "outros")
    return {
        "documento": dica or "nota_fiscal", "data": None, "fornecedor": None, "unidade_consumidora": None,
        "alvo_mencionado": None, "observacao": None, "fonte": "manual",
        "itens": [{"descricao": "", "categoria": categoria, "quantidade": None, "unidade": None, "valor_total": None}],
    }


# ------------------------------------------------------------ leitura por regras

_PALAVRAS = [
    (("ureia", "npk", "adubo", "fertiliz", "cloreto", "superfosfato", "calcario"), "adubo"),
    (("herbicida", "fungicida", "inseticida", "glifosato", "defensivo", "veneno"), "defensivos"),
    (("semente",), "sementes"),
    (("diesel", "oleo", "combustivel", "gasolina"), "combustivel"),
    (("luz", "energia", "kwh"), "energia"),
    (("agua", "irrigacao"), "agua"),
    (("peca", "manutencao", "conserto", "pneu", "trator", "colheitadeira"), "maquinas"),
    (("diarista", "salario", "peao", "mao de obra", "funcionario"), "mao_de_obra"),
    (("arrendamento",), "arrendamento"),
    (("vacina", "vermifugo", "carrapaticida", "veterinari"), "sanidade"),
    (("sal mineral", "racao", "suplemento", "sal "), "suplementacao"),
]
_UNIDADES = {"kg": "kg", "quilo": "kg", "quilos": "kg", "t": "t", "ton": "t", "tonelada": "t", "toneladas": "t",
             "l": "L", "litro": "L", "litros": "L", "sc": "sc", "saca": "sc", "sacas": "sc", "sacos": "un",
             "cabecas": "cab", "cabeca": "cab", "cab": "cab", "kwh": "kWh", "un": "un", "doses": "un",
             "bois": "cab", "boi": "cab", "vacas": "cab", "novilhos": "cab", "terneiros": "cab"}


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _numero_br(s: str) -> float:
    s = s.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    return float(s)


def ler_texto_regras(texto: str) -> dict:
    t = _sem_acento(texto)
    vendeu = bool(re.search(r"\bvend", t))
    categoria = "outros"
    for palavras, cat in _PALAVRAS:
        if any(p in t for p in palavras):
            categoria = cat
            break
    if vendeu:
        categoria = "venda_gado" if re.search(r"boi|vaca|novilh|terneir|gado|cabec", t) else "venda_arroz"

    valor = None
    m = re.search(r"r\$\s*([\d.,]+)(\s*mil\b)?", t) or re.search(r"([\d.,]+)(\s*mil)?\s*(?:reais|pila)", t) \
        or re.search(r"\bpor\s+([\d.,]+)(\s*mil\b)?(?!\s*(?:kg|quilo|l\b|litro|sc|saca|cab|t\b|ton))", t)
    if m:
        valor = _numero_br(m.group(1)) * (1000 if m.group(2) else 1)

    quantidade = unidade = None
    for m in re.finditer(r"([\d.,]+)\s*(kg|quilos?|toneladas?|ton|t|litros?|l|sacas?|sc|sacos|cabecas?|cab|kwh|doses|un|bois|boi|vacas|novilhos|terneiros)\b", t):
        if valor is not None and m.start() > 0 and t[max(0, m.start() - 3):m.start()].strip().endswith("r$"):
            continue
        quantidade, unidade = _numero_br(m.group(1)), _UNIDADES[m.group(2)]
        break

    alvo = None
    m = re.search(r"(talh[aã]o|lote|bomba)\s+(?:d[oa]s?\s+)?([\w-]+)", t)
    if m:
        alvo = f"{m.group(1)} {m.group(2)}"

    return {
        "documento": "anotacao", "data": None, "fornecedor": None, "unidade_consumidora": None,
        "alvo_mencionado": alvo, "observacao": None, "fonte": "regras",
        "itens": [{"descricao": texto.strip()[:120], "categoria": categoria, "quantidade": quantidade,
                   "unidade": unidade, "valor_total": valor}],
    }


# ------------------------------------------------------- reconhecer o destino


def resolver_alvo(rascunho: dict, talhoes: list[dict], lotes: list[dict], bombas: list[dict]) -> dict | None:
    """Liga o que foi citado ("talhão 3", UC da conta de luz) a um cadastro."""
    uc = (rascunho.get("unidade_consumidora") or "").strip()
    if uc:
        for b in bombas:
            if b.get("uc") and re.sub(r"\D", "", b["uc"]) == re.sub(r"\D", "", uc):
                return {"alvo_tipo": "bomba", "alvo_id": b["id"]}
    citado = _sem_acento(rascunho.get("alvo_mencionado") or "")
    if not citado:
        return None
    grupos = [("talhao", talhoes, ("talh",)), ("lote", lotes, ("lote",)), ("bomba", bombas, ("bomba",))]
    for tipo, itens, prefixos in grupos:
        if not any(citado.startswith(p) for p in prefixos):
            continue
        resto = re.sub(r"^(talh\w*|lote|bomba)\s*(d[oa]s?\s+)?", "", citado).strip()
        for it in itens:
            nome = _sem_acento(it["nome"])
            if resto and (resto == nome or re.search(rf"\b{re.escape(resto)}\b", nome)):
                return {"alvo_tipo": tipo, "alvo_id": it["id"]}
    return None


def cadastro_texto(talhoes: list[dict], lotes: list[dict], bombas: list[dict]) -> str:
    partes = [f"talhões: {', '.join(t['nome'] for t in talhoes)}",
              f"lotes: {', '.join(lt['nome'] for lt in lotes)}",
              "bombas: " + ", ".join(f"{b['nome']} (UC {b.get('uc') or '-'})" for b in bombas)]
    return "; ".join(partes)
