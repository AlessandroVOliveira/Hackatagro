"""Hora Certa: simulador de comercialização de arroz e gado.

Rodar: streamlit run app.py
"""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from hora_certa import cenarios as cen
from hora_certa import dados
from hora_certa import sazonalidade as saz

VERDE = "#2e6b3c"
VERDE_CLARO = "#9cc5a1"
CINZA = "#8a8a8a"
VERMELHO = "#b5432f"

st.set_page_config(page_title="Hora Certa", page_icon="🌾", layout="centered")


def brl(valor: float, casas: int = 2) -> str:
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def brl_sinal(valor: float, casas: int = 2) -> str:
    return ("+" if valor >= 0 else "−") + brl(abs(valor), casas)


def pct(valor: float) -> str:
    return f"{valor:.1%}".replace(".", ",")


@st.cache_data
def carregar():
    return (
        dados.carregar_precos("arroz"),
        dados.carregar_precos("boi"),
        dados.carregar_juros(),
    )


precos_arroz, precos_boi, juros = carregar()
cdi_padrao = juros["cdi"]["taxa_aa"]
ultimo_arroz = precos_arroz.iloc[-1]
ultimo_boi = precos_boi.iloc[-1]
arroz_mensal = saz.mensal(precos_arroz)
ano_colheita = max(a for a in arroz_mensal.index.year if pd.Timestamp(a, 4, 1) in arroz_mensal.index)
colheita_recente = arroz_mensal[f"{ano_colheita}-03":f"{ano_colheita}-04"].mean()

st.title("Hora Certa")
st.caption(
    "Quanto custa vender na pressa, em R$ por saca e por cabeça, "
    "e como pagar as contas enquanto espera."
)

variacao_safra = ultimo_arroz["preco"] / colheita_recente - 1
st.info(
    f"**Safra {ano_colheita}:** quem vendeu na colheita recebeu em média "
    f"**{brl(colheita_recente)}** por saca. Em {ultimo_arroz['data']:%d/%m/%Y} o "
    f"indicador estava em **{brl(ultimo_arroz['preco'])}** "
    f"({'+' if variacao_safra >= 0 else '−'}{pct(abs(variacao_safra))})."
)

aba_arroz, aba_gado, aba_caixa = st.tabs(["Arroz", "Gado", "Como pagar as contas"])

# ======================================================================= ARROZ
with aba_arroz:
    st.subheader("Sua safra")
    c1, c2 = st.columns(2)
    area = c1.number_input("Área plantada (ha)", 1.0, 50_000.0, 300.0, step=10.0)
    produtividade = c2.number_input("Produtividade (sacas/ha)", 50.0, 300.0, 170.0, step=5.0)
    c1, c2 = st.columns(2)
    custo_ha = c1.number_input("Custo de produção (R$/ha)", 0.0, 50_000.0, 15_000.0, step=500.0)
    contas = c2.number_input(
        "Contas a pagar na colheita (R$)", 0.0, 1e9, 1_500_000.0, step=50_000.0,
        help="Insumos, parcelas, arrendamento: o que vence em mar/abr e obriga a vender.",
    )
    c1, c2 = st.columns(2)
    preco_colheita = c1.number_input(
        "Preço na colheita (R$/saca)", 1.0, 500.0,
        float(round(colheita_recente, 2)), step=1.0,
        help=f"Padrão: média do indicador CEPEA/IRGA-RS em mar/abr de {ano_colheita}.",
    )
    meses_opcoes = list(range(1, 11))
    mes_alvo = c2.selectbox(
        "Vender o que guardar em",
        meses_opcoes,
        index=3,
        format_func=lambda k: saz.nome_mes(4, k).capitalize(),
    )

    with st.expander("Premissas de custo (editáveis)"):
        c1, c2 = st.columns(2)
        armazenagem = c1.number_input("Armazenagem (R$/saca/mês)", 0.0, 20.0, 1.00, step=0.10)
        recepcao = c2.number_input(
            "Recepção e secagem (R$/saca, uma vez)", 0.0, 30.0, 3.00, step=0.50,
            help="Só o que o armazém cobra a mais do que a venda direta na colheita.",
        )
        c1, c2 = st.columns(2)
        frete = c1.number_input("Frete até o armazém (R$/saca)", 0.0, 30.0, 0.0, step=0.50)
        quebra = c2.number_input("Quebra técnica (% ao mês)", 0.0, 3.0, 0.3, step=0.1) / 100
        c1, c2 = st.columns(2)
        juros_fin = c1.number_input("Juros do financiamento de estocagem (% a.a.)", 0.0, 40.0, 12.0, step=0.5) / 100
        cdi = c2.number_input(
            "CDI (% a.a.)", 0.0, 40.0, float(cdi_padrao), step=0.25,
            help=f"Banco Central, {juros['cdi']['data']}. É o que o dinheiro renderia parado.",
        ) / 100
        c1, c2 = st.columns(2)
        financiavel = c1.slider("Quanto do estoque o banco financia", 0, 100, 70, format="%d%%") / 100
        anos_hist = c2.slider("Anos de histórico", 5, 20, 15)
        st.caption(
            "Valores de armazenagem, secagem, quebra e juros são referências para a "
            "demonstração e devem ser validados com cooperativas e bancos de Alegrete."
        )

    sacas = area * produtividade
    p = cen.ParametrosArroz(
        sacas=sacas,
        preco_colheita=preco_colheita,
        contas_colheita=contas,
        mes_alvo=mes_alvo,
        cdi_aa=cdi,
        juros_financiamento_aa=juros_fin,
        percentual_financiavel=financiavel,
        armazenagem_mes=armazenagem,
        recepcao_secagem=recepcao,
        frete_armazem=frete,
        quebra_mes=quebra,
        custo_producao_saca=custo_ha / produtividade,
    )
    fatores = saz.fatores_por_ano(precos_arroz, (3, 4), horizonte=10, anos=anos_hist)
    lista = cen.cenarios_arroz(p, fatores)
    tabela = cen.tabela_resultados(p, lista)
    rec = cen.recomendar(p, lista)
    nome_alvo = saz.nome_mes(4, mes_alvo)
    anos_txt = f"{fatores.index.min()}–{fatores.index.max()}"

    # ---- recado principal
    st.subheader("O que o histórico diz")
    linha_rec = tabela.set_index("cenario").loc[rec.nome]
    if rec.nome == lista[0].nome:
        st.warning(
            f"**Com esses custos, esperar até {nome_alvo} não compensou na maioria dos anos.** "
            f"Vender na colheita é o mais seguro. Teste outro mês ou reveja os custos de armazenagem."
        )
    else:
        vendas_txt = []
        for k, frac in rec.vendas:
            if frac <= 0.001:
                continue
            quando = "agora" if k == 0 else f"em {saz.nome_mes(4, k)}"
            vendas_txt.append(f"{frac:.0%} {quando}")
        st.success(
            f"**Esperar vale {brl(linha_rec['ganho_mediano_saca'])} por saca, "
            f"ou {brl(linha_rec['ganho_mediano_safra'], 0)} na sua safra** "
            f"(mediana {anos_txt}).\n\n"
            f"Plano: **{rec.nome.lower()}**, vendendo {', '.join(vendas_txt)}. "
            f"Em {linha_rec['anos_melhor']} de {linha_rec['anos']} anos isso rendeu "
            f"mais do que vender tudo na colheita."
        )

    m1, m2, m3 = st.columns(3)
    m1.metric("Sua safra", f"{sacas:,.0f} sacas".replace(",", "."))
    m2.metric("Custo por saca", brl(p.custo_producao_saca))
    m3.metric("Margem na colheita", brl_sinal(preco_colheita - p.custo_producao_saca),
              delta=f"{(preco_colheita / p.custo_producao_saca - 1):.0%} sobre o custo")

    # ---- gráfico de cenários
    fig = go.Figure()
    for _, r in tabela.iterrows():
        cor = VERDE if r["cenario"] == rec.nome else (CINZA if r["paga_contas"] else VERMELHO)
        fig.add_trace(
            go.Bar(
                x=[r["cenario"]],
                y=[r["mediana"]],
                marker_color=cor,
                error_y=dict(
                    type="data", symmetric=False,
                    array=[r["melhor"] - r["mediana"]],
                    arrayminus=[r["mediana"] - r["pior"]],
                    color="#444", thickness=1.2, width=6,
                ),
                text=[brl(r["mediana"])],
                textposition="inside",
                hovertemplate=(
                    f"<b>{r['cenario']}</b><br>Mediana: {brl(r['mediana'])}<br>"
                    f"Pior ano: {brl(r['pior'])}<br>Melhor ano: {brl(r['melhor'])}<extra></extra>"
                ),
                showlegend=False,
            )
        )
    fig.add_hline(y=p.custo_producao_saca, line_dash="dot", line_color=VERMELHO,
                  annotation_text="custo de produção", annotation_position="bottom right")
    piso = min(tabela["pior"].min(), p.custo_producao_saca) * 0.9
    fig.update_layout(
        title=f"R$ líquido por saca, vendendo o que guardar em {nome_alvo}",
        yaxis_title="R$/saca (já descontados custos e juros)",
        yaxis_range=[piso, tabela["melhor"].max() * 1.05],
        height=420, margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Barra = ano mediano; traço = pior e melhor ano do histórico. "
        "Verde = recomendado; vermelho = não paga as contas da colheita."
    )

    # ---- tabela
    mostrar = pd.DataFrame(
        {
            "Cenário": tabela["cenario"],
            "Ganho/saca (mediana)": tabela["ganho_mediano_saca"].map(brl_sinal),
            "Na safra (mediana)": tabela["ganho_mediano_safra"].map(lambda v: brl_sinal(v, 0)),
            "Anos melhores": tabela.apply(lambda r: f"{r['anos_melhor']}/{r['anos']}", axis=1),
            "Caixa na colheita": tabela["caixa_colheita"].map(lambda v: brl(v, 0)),
            "Paga as contas?": tabela["paga_contas"].map({True: "sim", False: "não"}),
        }
    )
    st.dataframe(mostrar, hide_index=True, width="stretch")
    for c in lista:
        st.markdown(f"- **{c.nome}:** {c.descricao}")

    # ---- melhor mês
    st.subheader("Qual mês costuma compensar?")
    por_mes = cen.ganho_por_mes(p, fatores)
    por_mes["mes"] = por_mes["k"].map(lambda k: saz.nome_mes(4, k))
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=por_mes["mes"], y=por_mes["melhor"], line=dict(width=0),
                              showlegend=False, hoverinfo="skip"))
    fig2.add_trace(go.Scatter(x=por_mes["mes"], y=por_mes["pior"], fill="tonexty",
                              fillcolor="rgba(156,197,161,0.35)", line=dict(width=0),
                              name="pior a melhor ano", hoverinfo="skip"))
    fig2.add_trace(go.Scatter(
        x=por_mes["mes"], y=por_mes["mediana"], mode="lines+markers",
        line=dict(color=VERDE, width=3), name="ano mediano",
        customdata=por_mes[["anos_melhor", "anos"]],
        hovertemplate="%{x}: %{y:.2f} R$/saca<br>melhor que vender na colheita em "
        "%{customdata[0]} de %{customdata[1]} anos<extra></extra>",
    ))
    fig2.add_hline(y=0, line_color="#444", line_width=1)
    fig2.update_layout(
        yaxis_title="Ganho líquido vs. colheita (R$/saca)",
        height=360, margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig2, width="stretch")
    st.caption("Estocagem financiada para pagar as contas; o resto do dinheiro parado custa o CDI.")

    with st.expander("Ver ano a ano"):
        ano_a_ano = pd.DataFrame({c.nome: c.liquido_saca for c in lista}).round(2)
        ano_a_ano.insert(0, f"Preço {nome_alvo} ÷ colheita", fatores[mes_alvo].round(3))
        st.dataframe(ano_a_ano, width="stretch")
        st.caption(
            "Para cada ano, aplicamos ao seu preço de hoje a variação de preço que "
            "aconteceu entre mar/abr e o mês de venda. Fonte: indicador do arroz em "
            "casca CEPEA/IRGA-RS."
        )

# ======================================================================== GADO
with aba_gado:
    mes_atual = date.today().month
    st.subheader("Vender agora ou segurar?")
    c1, c2 = st.columns(2)
    cabecas = c1.number_input("Cabeças", 1, 100_000, 100, step=10)
    peso = c2.number_input("Peso vivo médio hoje (kg)", 100.0, 900.0, 450.0, step=10.0)
    c1, c2 = st.columns(2)
    preco_arroba = c1.number_input(
        "Preço hoje (R$/@)", 50.0, 1000.0, float(round(ultimo_boi["preco"], 2)), step=5.0,
        help=f"Padrão: indicador do boi gordo CEPEA/ESALQ de {ultimo_boi['data']:%d/%m/%Y}. "
        "Troque pelo preço que você recebe no RS.",
    )
    meses_gado = c2.slider("Segurar por (meses)", 1, 12, 4)
    c1, c2, c3 = st.columns(3)
    ganho_dia = c1.number_input("Ganho de peso (kg/dia)", 0.0, 2.0, 0.5, step=0.05)
    custo_cab = c2.number_input("Custo por cabeça (R$/mês)", 0.0, 1000.0, 60.0, step=5.0)
    rendimento = c3.number_input("Rendimento de carcaça (%)", 40.0, 60.0, 50.0, step=0.5) / 100

    pg = cen.ParametrosGado(
        cabecas=cabecas, peso_kg=peso, preco_arroba=preco_arroba, meses=meses_gado,
        ganho_kg_dia=ganho_dia, custo_cabeca_mes=custo_cab, cdi_aa=cdi,
        rendimento_carcaca=rendimento,
    )
    fatores_boi = saz.fatores_por_ano(precos_boi, (mes_atual,), horizonte=12, anos=anos_hist)
    res = cen.segurar_gado(pg, fatores_boi)
    g = res["ganho_cabeca"]
    mes_venda = saz.nome_mes(mes_atual, meses_gado)

    if g.median() > 0 and (g > 0).mean() > 0.5:
        st.success(
            f"**Segurar até {mes_venda} vale {brl(g.median())} por cabeça, "
            f"{brl(g.median() * cabecas, 0)} no lote** (mediana). "
            f"Compensou em {(g > 0).sum()} de {g.count()} anos."
        )
    else:
        st.warning(
            f"**Segurar até {mes_venda} não compensou na maioria dos anos** "
            f"({(g > 0).sum()} de {g.count()}). Mediana: {brl_sinal(g.median())} por cabeça."
        )

    m1, m2, m3 = st.columns(3)
    m1.metric("Pior ano", brl_sinal(g.min()))
    m2.metric("Mediana", brl_sinal(g.median()))
    m3.metric("Melhor ano", brl_sinal(g.max()))

    linhas = []
    for n in range(1, 13):
        pn = cen.ParametrosGado(**{**pg.__dict__, "meses": n})
        gn = cen.segurar_gado(pn, fatores_boi)["ganho_cabeca"]
        linhas.append({"mes": saz.nome_mes(mes_atual, n), "pior": gn.min(),
                       "mediana": gn.median(), "melhor": gn.max()})
    curva = pd.DataFrame(linhas)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=curva["mes"], y=curva["melhor"], line=dict(width=0),
                              showlegend=False, hoverinfo="skip"))
    fig3.add_trace(go.Scatter(x=curva["mes"], y=curva["pior"], fill="tonexty",
                              fillcolor="rgba(156,197,161,0.35)", line=dict(width=0),
                              name="pior a melhor ano", hoverinfo="skip"))
    fig3.add_trace(go.Scatter(x=curva["mes"], y=curva["mediana"], mode="lines+markers",
                              line=dict(color=VERDE, width=3), name="ano mediano",
                              hovertemplate="vender em %{x}: %{y:.0f} R$/cabeça<extra></extra>"))
    fig3.add_hline(y=0, line_color="#444", line_width=1)
    fig3.update_layout(
        title="Ganho por cabeça conforme o mês de venda",
        yaxis_title="R$/cabeça vs. vender hoje",
        height=360, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=1.02),
    )
    st.plotly_chart(fig3, width="stretch")
    st.caption(
        "Já descontados o custo de manutenção e o CDI sobre o valor do animal. "
        "Sazonalidade do indicador do boi gordo CEPEA/ESALQ (SP), usada como "
        "referência até incluirmos a série do NESPRO/UFRGS para o RS."
    )

# ====================================================================== CAIXA
with aba_caixa:
    st.subheader("Quanto custa o adiantamento?")
    st.write(
        "Receber adiantado do comprador em troca de desconto no preço é um "
        "empréstimo. Veja os juros que estão embutidos nele."
    )
    c1, c2 = st.columns(2)
    desconto = c1.number_input("Desconto no preço (%)", 0.0, 50.0, 8.0, step=0.5) / 100
    antecedencia = c2.number_input("Meses de antecedência", 1, 12, 4)
    taxa_adiant = cen.juros_implicitos_adiantamento(desconto, antecedencia)
    m1, m2, m3 = st.columns(3)
    m1.metric("Juros do adiantamento", f"{pct(taxa_adiant)} a.a.")
    m2.metric("Financiamento de estocagem", f"{pct(juros_fin)} a.a.")
    m3.metric("CDI", f"{pct(cdi)} a.a.")
    if taxa_adiant > juros_fin:
        st.info(
            f"O adiantamento custa {pct(taxa_adiant - juros_fin)} ao ano a mais que o "
            "financiamento de estocagem. Vale procurar o crédito formal."
        )

    st.subheader("Alternativas para atravessar o aperto de caixa")
    st.markdown(
        """
- **EGF (Plano Safra):** financiamento de estocagem. O produto fica guardado
  como garantia e o produtor recebe o dinheiro para pagar as contas da colheita.
- **CDA/WA:** títulos emitidos por armazém certificado. O produtor guarda o
  arroz e usa o *warrant* como garantia para conseguir crédito no banco.
- **CPR:** Cédula de Produto Rural. Vende antecipado ou capta crédito com
  entrega futura do produto. Atenção ao desconto embutido.
- **Venda escalonada:** vende só o necessário para as contas agora e o resto
  em parcelas, para não depender de acertar um único mês.
"""
    )
    st.caption("Taxas e condições variam por banco e por safra. Confirme com seu banco ou cooperativa.")
