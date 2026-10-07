"""Camada visual do Entressafra: estilos e componentes HTML para o Streamlit.

Paleta tirada da lavoura de arroz na colheita: verde da lavoura para ganho,
barro vermelho da campanha para perda, dourado da casca só para o preço.
"""

from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import streamlit as st

LAVOURA = "#1E4D3A"
LAVOURA_CLARO = "#CFE0D3"
CASCA = "#C8952B"
BARRO = "#9A3F24"
BARRO_CLARO = "#EBCFC4"
PAPEL = "#FAFAF7"
TINTA = "#18201B"
TINTA_SUAVE = "#58625B"
NEVOA = "#DFE4DC"

FONTE = "Archivo, 'Archivo Narrow', system-ui, -apple-system, 'Segoe UI', sans-serif"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&display=swap');

:root {{
  --lavoura: {LAVOURA}; --lavoura-claro: {LAVOURA_CLARO}; --casca: {CASCA};
  --barro: {BARRO}; --barro-claro: {BARRO_CLARO}; --papel: {PAPEL};
  --tinta: {TINTA}; --tinta-suave: {TINTA_SUAVE}; --nevoa: {NEVOA};
}}

.stApp {{ background: var(--papel); color: var(--tinta); }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button,
.stApp h1, .stApp h2, .stApp h3, .stApp summary, .stApp td, .stApp th {{
  font-family: {FONTE};
}}
.stApp p, .stApp li {{ font-size: 1rem; line-height: 1.5; }}

[data-testid="stHeader"] {{ background: transparent; height: 0; }}
[data-testid="stMainBlockContainer"], .block-container {{
  max-width: none; padding: 1.75rem clamp(1.25rem, 3vw, 3.5rem) 4rem;
}}

.stApp h2 {{
  font-size: 1.25rem; font-weight: 700; letter-spacing: -0.01em;
  margin: 2rem 0 0.25rem; padding: 0;
}}
.stApp h3 {{ font-size: 1.05rem; font-weight: 700; margin: 1.5rem 0 0.25rem; padding: 0; }}

/* abas */
[data-baseweb="tab-list"] {{
  gap: 0; border-bottom: 2px solid var(--nevoa); overflow-x: auto;
  scrollbar-width: none;
}}
button[data-baseweb="tab"] {{
  padding: 0.75rem 1rem; min-height: 48px;
}}
button[data-baseweb="tab"] p {{ font-size: 1rem; font-weight: 600; }}
button[data-baseweb="tab"][aria-selected="true"] p {{ color: var(--lavoura); }}
[data-baseweb="tab-highlight"] {{ background: var(--lavoura); height: 3px; }}

/* campos: 16px evita o zoom automático do iOS */
.stApp input {{ font-size: 16px !important; font-variant-numeric: tabular-nums; }}
[data-testid="stNumberInput"] > div, [data-baseweb="select"] > div {{ min-height: 46px; }}
.stApp label p {{ font-size: 0.9rem; font-weight: 600; color: var(--tinta-suave); }}

[data-testid="stExpander"] details {{ border: 1px solid var(--nevoa); border-radius: 6px; background: #fff; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}

*:focus-visible {{ outline: 3px solid var(--casca) !important; outline-offset: 2px; }}

/* ---------- componentes ---------- */
.hc-marca {{ display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }}
.hc-marca b {{
  font-size: 1.9rem; font-weight: 800; font-stretch: 75%; letter-spacing: -0.01em;
  color: var(--lavoura); line-height: 1;
}}
.hc-marca span {{ color: var(--tinta-suave); font-size: 0.95rem; }}

.hc-safra {{ border-top: 2px solid var(--tinta); padding: 0.9rem 0 0.25rem; margin-bottom: 0.5rem; }}
.hc-topo {{ margin-bottom: 0.5rem; }}
@media (min-width: 900px) {{
  .hc-topo {{
    display: grid; grid-template-columns: 1fr minmax(360px, 34rem); gap: 3rem; align-items: end;
    border-bottom: 2px solid var(--tinta); padding-bottom: 1rem; margin-bottom: 0.25rem;
  }}
  .hc-topo .hc-marca {{ margin-bottom: 0; }}
  .hc-topo .hc-marca b {{ font-size: 2.6rem; }}
  .hc-topo .hc-safra {{ border-top: 0; padding: 0; margin: 0; }}
  .hc-topo .hc-safra p {{ margin-bottom: 1.4rem; }}
  [data-baseweb="tab-list"] {{ border-bottom: 0; }}
  /* a coluna de campos acompanha a rolagem dos resultados */
  [data-testid="stColumn"]:has([class*="st-key-campos"]) {{
    position: sticky; top: 1rem; align-self: flex-start;
  }}
}}
@media (min-width: 1700px) {{ html {{ font-size: 17px; }} }}
@media (min-width: 2200px) {{ html {{ font-size: 19px; }} }}
.hc-safra p {{ margin: 0 0 0.75rem; }}
.hc-trilho {{ display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 0.75rem; }}
.hc-ponto small {{ display: block; color: var(--tinta-suave); font-size: 0.8rem; }}
.hc-ponto strong {{ font-size: 1.35rem; font-weight: 800; font-stretch: 80%; font-variant-numeric: tabular-nums; }}
.hc-ponto.hoje {{ text-align: right; }}
.hc-ponto.hoje strong {{ color: var(--casca); }}
.hc-linha {{ position: relative; height: 3px; background: var(--nevoa); }}
.hc-linha::after {{
  content: ''; position: absolute; right: -2px; top: -5px;
  border-left: 9px solid var(--casca); border-top: 6.5px solid transparent; border-bottom: 6.5px solid transparent;
}}
.hc-linha span {{
  position: absolute; left: 50%; top: -1.6rem; transform: translateX(-50%);
  font-weight: 700; font-size: 0.95rem; white-space: nowrap; color: var(--casca);
}}

.hc-veredito {{ margin: 1.5rem 0 0.5rem; container-type: inline-size; }}
.hc-veredito .rotulo {{ font-size: 1rem; color: var(--tinta-suave); margin: 0; }}
.hc-numero {{
  font-size: clamp(2.6rem, 19cqi, 6.4rem); font-weight: 900; font-stretch: 62%;
  line-height: 0.92; letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
  margin: 0.15rem 0 0.35rem;
  display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 0.3rem;
}}
.hc-numero small {{ font-size: 0.32em; font-weight: 700; font-stretch: 85%; letter-spacing: 0; white-space: nowrap; line-height: 1.15; }}
.hc-numero.ganho {{ color: var(--lavoura); }}
.hc-numero.perda {{ color: var(--barro); }}
.hc-veredito .frase {{ font-size: 1.1rem; line-height: 1.45; max-width: 36em; margin: 0; }}

.hc-plano {{ margin: 1.25rem 0 0.5rem; }}
.hc-plano > p {{ font-weight: 700; margin: 0 0 0.5rem; }}
.hc-meses {{ display: grid; grid-template-columns: repeat(11, 1fr); gap: 3px; align-items: end; height: 88px; }}
.hc-mes {{ display: flex; flex-direction: column; justify-content: flex-end; height: 100%; text-align: center; }}
.hc-mes i {{ display: block; background: var(--nevoa); min-height: 3px; border-radius: 2px 2px 0 0; }}
.hc-mes.venda i {{ background: var(--lavoura); }}
.hc-mes.venda.colheita i {{ background: var(--casca); }}
.hc-mes em {{ font-style: normal; font-size: 0.72rem; font-weight: 700; color: var(--lavoura); min-height: 1.1rem; }}
.hc-mes.colheita em {{ color: #8a6418; }}
.hc-eixo {{ display: grid; grid-template-columns: repeat(11, 1fr); gap: 3px; border-top: 1px solid var(--tinta); }}
.hc-eixo span {{ text-align: center; font-size: 0.72rem; color: var(--tinta-suave); padding-top: 0.25rem; }}

.hc-cenarios {{ margin: 0.5rem 0 0; }}
.hc-cen {{ padding: 0.9rem 0; border-bottom: 1px solid var(--nevoa); }}
.hc-cen:first-child {{ border-top: 1px solid var(--nevoa); }}
.hc-cen header {{ display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; }}
.hc-cen h4 {{ font-size: 1.02rem; font-weight: 700; margin: 0; padding: 0; color: var(--tinta); }}
.hc-cen.rec h4::before {{
  content: ''; display: inline-block; width: 0.6rem; height: 0.6rem; border-radius: 50%;
  background: var(--lavoura); margin-right: 0.45rem; vertical-align: 0.05rem;
}}
.hc-cen .val {{ font-size: 1.15rem; font-weight: 800; font-stretch: 80%; white-space: nowrap; font-variant-numeric: tabular-nums; }}
.hc-cen .val.ganho {{ color: var(--lavoura); }}
.hc-cen .val.perda {{ color: var(--barro); }}
.hc-faixa {{ position: relative; height: 18px; margin: 0.55rem 0 0.35rem; }}
.hc-faixa .zero {{ position: absolute; top: -3px; bottom: -3px; width: 1.5px; background: var(--tinta); }}
.hc-faixa .bar {{ position: absolute; top: 6px; height: 6px; border-radius: 3px; }}
.hc-faixa .bar.neg {{ background: var(--barro-claro); }}
.hc-faixa .bar.pos {{ background: var(--lavoura-claro); }}
.hc-faixa .med {{
  position: absolute; top: 2px; width: 14px; height: 14px; margin-left: -7px;
  border-radius: 50%; border: 2.5px solid var(--papel);
}}
.hc-faixa .med.ganho {{ background: var(--lavoura); }}
.hc-faixa .med.perda {{ background: var(--barro); }}
.hc-extremos {{ display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--tinta-suave); font-variant-numeric: tabular-nums; }}
.hc-meta {{ display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; font-size: 0.88rem; color: var(--tinta-suave); margin-top: 0.4rem; }}
.hc-meta .alerta {{ color: var(--barro); font-weight: 700; }}
.hc-legenda {{ font-size: 0.85rem; color: var(--tinta-suave); margin: 0.6rem 0 0; }}

.hc-numeros {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin: 1rem 0; container-type: inline-size; }}
.hc-numeros.topo {{ margin-top: 2.6rem; }}
.hc-numeros div {{ border-left: 3px solid var(--nevoa); padding-left: 0.6rem; }}
.hc-numeros small {{ display: block; font-size: 0.8rem; color: var(--tinta-suave); }}
.hc-numeros strong {{ font-size: clamp(0.95rem, 5.2cqi, 1.3rem); font-weight: 800; font-stretch: 80%; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.hc-numeros strong.perda {{ color: var(--barro); }}
.hc-numeros strong.ganho {{ color: var(--lavoura); }}

.hc-taxas {{ margin: 1rem 0; }}
.hc-taxa {{ display: grid; grid-template-columns: 9.5rem 1fr 4.5rem; align-items: center; gap: 0.75rem; padding: 0.45rem 0; }}
.hc-taxa span {{ font-size: 0.92rem; }}
.hc-taxa i {{ display: block; height: 14px; border-radius: 0 3px 3px 0; background: var(--nevoa); }}
.hc-taxa.destaque i {{ background: var(--barro); }}
.hc-taxa b {{ text-align: right; font-variant-numeric: tabular-nums; }}

.hc-instrumentos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 0 2.5rem; margin: 0; }}
.hc-instrumentos div {{ border-top: 1px solid var(--nevoa); padding: 0.9rem 0; }}
.hc-instrumentos dt {{ font-weight: 700; }}
.hc-instrumentos dd {{ margin: 0.15rem 0 0; color: var(--tinta-suave); max-width: 36em; }}
.hc-nota {{ font-size: 0.85rem; color: var(--tinta-suave); margin-top: 1.25rem; }}

.hc-aviso {{
  background: var(--lavoura-claro); border-left: 3px solid var(--lavoura); border-radius: 0 6px 6px 0;
  padding: 0.75rem 1rem; margin: 0 0 1.25rem; font-size: 0.95rem; line-height: 1.5;
}}

@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding: 1rem 1rem 3rem; }}
  /* campos em pares continuam lado a lado no celular: o resultado fica mais perto */
  [class*="st-key-campos"] [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 0.6rem !important; }}
  [class*="st-key-campos"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    min-width: 0 !important; width: auto !important; flex: 1 1 0 !important;
  }}
  [data-testid="stNumberInput"] button {{ width: 2rem; }}
  .stApp label p {{ font-size: 0.82rem; line-height: 1.25; }}
  .hc-meses, .hc-eixo {{ gap: 2px; }}
  .hc-eixo span, .hc-mes em {{ font-size: 0.64rem; }}
  .hc-numeros {{ gap: 0.5rem; }}
  .hc-numeros small {{ font-size: 0.74rem; }}
  .hc-taxa {{ grid-template-columns: 7rem 1fr 4rem; gap: 0.5rem; }}
  .hc-taxa span {{ font-size: 0.85rem; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
"""


def _html(texto: str) -> None:
    # O markdown trata linhas indentadas como bloco de código: remove a indentação.
    limpo = "\n".join(linha.strip() for linha in texto.strip().splitlines())
    st.markdown(limpo, unsafe_allow_html=True)


def aplicar_estilo() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def brl(valor: float, casas: int = 2) -> str:
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def brl_sinal(valor: float, casas: int = 2) -> str:
    return ("+" if valor >= 0 else "−") + brl(abs(valor), casas)


def pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}%}".replace(".", ",")


def classe(valor: float) -> str:
    return "ganho" if valor > 0 else "perda"


# ------------------------------------------------------------- componentes


def cabecalho(ano: int, preco_colheita: float, preco_hoje: float, data_hoje: str) -> None:
    """Marca e trilho de preço da safra: empilhados no celular, lado a lado na tela larga."""
    var = preco_hoje / preco_colheita - 1
    sinal = "+" if var >= 0 else "−"
    _html(
        f"""
        <header class="hc-topo">
        <div class="hc-marca"><b>Entressafra</b>
        <span>Quanto custa vender na pressa, e como esperar sem atrasar as contas.</span></div>
        <section class="hc-safra" aria-label="Preço do arroz na safra {ano}">
        <p>Arroz em casca no RS, safra {ano}</p>
        <div class="hc-trilho">
        <div class="hc-ponto"><small>Colheita (mar/abr)</small><strong>{brl(preco_colheita)}</strong></div>
        <div class="hc-linha"><span>{sinal}{pct(abs(var), 0)}</span></div>
        <div class="hc-ponto hoje"><small>{escape(data_hoje)}</small><strong>{brl(preco_hoje)}</strong></div>
        </div>
        </section>
        </header>
        """
    )


def veredito(rotulo: str, valor: float, unidade: str, frase: str) -> None:
    _html(
        f"""
        <section class="hc-veredito" aria-live="polite">
        <p class="rotulo">{escape(rotulo)}</p>
        <div class="hc-numero {classe(valor)}">{brl_sinal(valor)}<small>{escape(unidade)}</small></div>
        <p class="frase">{frase}</p>
        </section>
        """
    )


def plano_vendas(vendas: list[tuple[int, float]], nomes_meses: list[str]) -> None:
    """Faixa de meses (abr = colheita, mai..fev) com a fração vendida em cada um."""
    por_mes = {k: f for k, f in vendas if f > 0.001}
    maior = max(por_mes.values()) if por_mes else 1
    colunas, eixo = [], []
    for k, nome in enumerate(nomes_meses):
        f = por_mes.get(k, 0.0)
        altura = 6 + 64 * f / maior if f else 3
        cls = "hc-mes" + (" venda" if f else "") + (" colheita" if k == 0 else "")
        rotulo = pct(f, 0) if f else ""
        colunas.append(f'<div class="{cls}"><em>{rotulo}</em><i style="height:{altura:.0f}px"></i></div>')
        eixo.append(f"<span>{nome}</span>")
    _html(
        f"""
        <section class="hc-plano" aria-label="Quanto vender em cada mês">
        <p>Quanto vender em cada mês</p>
        <div class="hc-meses">{''.join(colunas)}</div>
        <div class="hc-eixo">{''.join(eixo)}</div>
        </section>
        """
    )


def cenarios(linhas: list[dict], unidade: str = "por saca") -> None:
    """Uma linha por cenário com faixa pior–melhor na mesma escala.

    Cada dict: nome, pior, mediana, melhor (ganho vs. colheita), rec (bool),
    meta (lista de str), alerta (str ou None).
    """
    lo = min(0.0, *(l["pior"] for l in linhas))
    hi = max(0.0, *(l["melhor"] for l in linhas))
    span = (hi - lo) or 1.0

    def x(v: float) -> float:
        return 100 * (v - lo) / span

    blocos = []
    for l in linhas:
        a, b = x(l["pior"]), x(l["melhor"])
        partes = []
        z = x(0)
        if l["pior"] < 0:
            partes.append(f'<i class="bar neg" style="left:{a:.1f}%;width:{min(b, z) - a:.1f}%"></i>')
        if l["melhor"] > 0:
            ini = max(a, z)
            partes.append(f'<i class="bar pos" style="left:{ini:.1f}%;width:{b - ini:.1f}%"></i>')
        faixa = (
            f'<div class="hc-faixa" aria-hidden="true">{"".join(partes)}'
            f'<i class="zero" style="left:{z:.1f}%"></i>'
            f'<i class="med {classe(l["mediana"])}" style="left:{x(l["mediana"]):.1f}%"></i></div>'
        )
        if l["pior"] == l["melhor"]:
            faixa = ""
            extremos = ""
        else:
            extremos = (
                f'<div class="hc-extremos"><span>pior ano {brl_sinal(l["pior"])}</span>'
                f'<span>melhor ano {brl_sinal(l["melhor"])}</span></div>'
            )
        meta = "".join(f"<span>{escape(m)}</span>" for m in l["meta"])
        if l.get("alerta"):
            meta += f'<span class="alerta">{escape(l["alerta"])}</span>'
        val_cls = classe(l["mediana"]) if l["mediana"] != 0 else ""
        blocos.append(
            f'<article class="hc-cen{" rec" if l["rec"] else ""}">'
            f'<header><h4>{escape(l["nome"])}</h4>'
            f'<span class="val {val_cls}">{brl_sinal(l["mediana"])}</span></header>'
            f"{faixa}{extremos}<div class=\"hc-meta\">{meta}</div></article>"
        )
    _html(
        f"""
        <section class="hc-cenarios">{''.join(blocos)}</section>
        <p class="hc-legenda">Valor grande: ganho no ano mediano, {escape(unidade)}, contra vender tudo na
        colheita. A barra vai do pior ao melhor ano; o ponto é a mediana. Já descontados armazenagem,
        quebra e juros.</p>
        """
    )


def numeros(itens: list[tuple[str, str, str]], topo: bool = False) -> None:
    """Linha de números de apoio: (rótulo, valor, classe css)."""
    cel = "".join(
        f'<div><small>{escape(r)}</small><strong class="{c}">{escape(v)}</strong></div>'
        for r, v, c in itens
    )
    _html(f'<div class="hc-numeros{" topo" if topo else ""}">{cel}</div>')


def taxas(itens: list[tuple[str, float, bool]]) -> None:
    """Barras horizontais de taxa anual: (rótulo, taxa, destaque)."""
    maior = max(t for _, t, _ in itens) or 1
    linhas = "".join(
        f'<div class="hc-taxa{" destaque" if d else ""}"><span>{escape(r)}</span>'
        f'<i style="width:{100 * t / maior:.1f}%"></i><b>{pct(t)}</b></div>'
        for r, t, d in itens
    )
    _html(f'<div class="hc-taxas" role="list">{linhas}</div>')


def instrumentos(itens: list[tuple[str, str]]) -> None:
    corpo = "".join(f"<div><dt>{escape(t)}</dt><dd>{escape(d)}</dd></div>" for t, d in itens)
    _html(f'<dl class="hc-instrumentos">{corpo}</dl>')


def nota(texto: str) -> None:
    _html(f'<p class="hc-nota">{escape(texto)}</p>')


def aviso(html: str) -> None:
    """Destaque com HTML (ex.: <b>) já formatado pelo chamador."""
    _html(f'<div class="hc-aviso">{html}</div>')


# ----------------------------------------------------------------- gráficos


def faixa_por_mes(meses: list[str], pior, mediana, melhor, eixo_y: str, dica: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=melhor, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=meses, y=pior, mode="lines", fill="tonexty", fillcolor="rgba(30,77,58,0.13)",
        line=dict(width=0), name="pior a melhor ano", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=meses, y=mediana, mode="lines+markers", name="ano mediano",
        line=dict(color=LAVOURA, width=3), marker=dict(size=7),
        hovertemplate=dica,
    ))
    fig.add_hline(y=0, line_color=TINTA, line_width=1.5)
    fig.update_layout(
        font=dict(family=FONTE, color=TINTA, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=4, r=4, t=30, b=4),
        title=dict(text=eixo_y, font=dict(size=13, color=TINTA_SUAVE), x=0, xanchor="left", y=0.98),
        yaxis=dict(gridcolor=NEVOA, zeroline=False, tickformat=",.0f", automargin=True),
        xaxis=dict(showgrid=False, fixedrange=True),
        legend=dict(orientation="h", y=-0.15, x=0, font=dict(size=12)),
        hoverlabel=dict(font_family=FONTE),
        separators=",.",
        dragmode=False,
    )
    fig.update_yaxes(fixedrange=True)
    return fig


CONFIG_GRAFICO = {"displayModeBar": False, "scrollZoom": False}
