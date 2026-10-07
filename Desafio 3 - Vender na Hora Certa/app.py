"""Entressafra: simulador de comercialização de arroz e gado.

Rodar: streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

from hora_certa import cenarios as cen
from hora_certa import dados
from hora_certa import sazonalidade as saz
from hora_certa import ui
from hora_certa.ui import brl, brl_sinal, pct

st.set_page_config(page_title="Entressafra", page_icon="🌾", layout="wide")
ui.aplicar_estilo()

# Proporção entre a coluna de campos e a de resultados em telas largas.
# No celular as duas empilham.
LAYOUT = [1, 2.1]


def pares():
    """Dois campos lado a lado, inclusive no celular."""
    return st.columns(2, vertical_alignment="bottom")


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
MESES_SAFRA = ["abr"] + [saz.nome_mes(4, k) for k in range(1, 11)]

ui.cabecalho(ano_colheita, colheita_recente, ultimo_arroz["preco"], f"{ultimo_arroz['data']:%d/%m/%Y}")

aba_arroz, aba_gado, aba_caixa = st.tabs(["Arroz", "Gado", "Pagar as contas"])

# ======================================================================= ARROZ
with aba_arroz:
    col_campos, col_result = st.columns(LAYOUT, gap="large")

    with col_campos, st.container(key="campos_arroz"):
        st.subheader("Sua safra")
        c1, c2 = pares()
        area = c1.number_input("Área plantada (ha)", 1.0, 50_000.0, 300.0, step=10.0, format="%.0f")
        produtividade = c2.number_input("Produtividade (sacas/ha)", 50.0, 300.0, 170.0, step=5.0, format="%.0f")
        c1, c2 = pares()
        custo_ha = c1.number_input("Custo de produção (R$/ha)", 0.0, 50_000.0, 15_000.0, step=500.0, format="%.0f")
        contas = c2.number_input(
            "Contas que vencem na colheita (R$)", 0.0, 1e9, 1_500_000.0, step=50_000.0, format="%.0f",
            help="Insumos, parcelas, arrendamento: o que vence em mar/abr e obriga a vender.",
        )
        c1, c2 = pares()
        preco_colheita = c1.number_input(
            "Preço na colheita (R$/saca)", 1.0, 500.0,
            float(round(colheita_recente, 2)), step=1.0,
            help=f"Padrão: média do indicador CEPEA/IRGA-RS em mar/abr de {ano_colheita}.",
        )
        mes_alvo = c2.selectbox(
            "Vender o que guardar em",
            list(range(1, 11)),
            index=3,
            format_func=lambda k: saz.nome_mes(4, k).capitalize(),
        )

        with st.expander("Custos de armazenar e juros"):
            c1, c2 = pares()
            armazenagem = c1.number_input("Armazenagem (R$/saca/mês)", 0.0, 20.0, 1.00, step=0.10)
            recepcao = c2.number_input(
                "Recepção e secagem (R$/saca, uma vez)", 0.0, 30.0, 3.00, step=0.50,
                help="Só o que o armazém cobra a mais do que a venda direta na colheita.",
            )
            c1, c2 = pares()
            frete = c1.number_input("Frete até o armazém (R$/saca)", 0.0, 30.0, 0.0, step=0.50)
            quebra = c2.number_input("Quebra técnica (% ao mês)", 0.0, 3.0, 0.3, step=0.1) / 100
            c1, c2 = pares()
            juros_fin = c1.number_input("Juros do financiamento de estocagem (% a.a.)", 0.0, 40.0, 12.0, step=0.5) / 100
            cdi = c2.number_input(
                "CDI (% a.a.)", 0.0, 40.0, float(cdi_padrao), step=0.25,
                help=f"Banco Central, {juros['cdi']['data']}. É o que o dinheiro renderia parado.",
            ) / 100
            financiavel = st.slider("Quanto do estoque o banco financia", 0, 100, 70, format="%d%%") / 100
            anos_hist = st.slider("Anos de histórico", 5, 20, 15)
            ui.nota(
                "Armazenagem, secagem, quebra e juros são valores de referência para a "
                "demonstração. Confirme com sua cooperativa e seu banco."
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
    tabela = cen.tabela_resultados(p, lista).set_index("cenario")
    rec = cen.recomendar(p, lista)
    nome_alvo = saz.nome_mes(4, mes_alvo)
    periodo = f"{fatores.index.min()} a {fatores.index.max()}"

    with col_result:
        # ---- veredito e plano lado a lado em telas largas
        v1, v2 = st.columns([1.25, 1], gap="large")
        with v1:
            if rec.nome != lista[0].nome:
                r = tabela.loc[rec.nome]
                ui.veredito(
                    f"Esperar até {nome_alvo}, no ano típico, rende",
                    r["ganho_mediano_saca"],
                    "por saca",
                    f"São <b>{brl(r['ganho_mediano_safra'], 0)}</b> a mais na sua safra. "
                    f"Melhor jeito: {rec.nome.lower()}. Rendeu mais que vender tudo na colheita "
                    f"em {r['anos_melhor']} de {r['anos']} anos ({periodo}).",
                )
                plano = rec.vendas
            else:
                alternativas = [c for c in lista[1:] if c.paga_contas] or lista[1:]
                melhor_alt = max(alternativas, key=lambda c: c.liquido_saca.median())
                r = tabela.loc[melhor_alt.nome]
                ui.veredito(
                    f"Esperar até {nome_alvo}, no ano típico, rende",
                    r["ganho_mediano_saca"],
                    "por saca",
                    f"Com esses custos, esperar só compensou em {r['anos_melhor']} de "
                    f"{r['anos']} anos. <b>Vender na colheita é o mais seguro.</b> "
                    "Teste outro mês ou um armazém mais barato.",
                )
                plano = lista[0].vendas
        with v2:
            ui.plano_vendas(plano, MESES_SAFRA)
            margem = preco_colheita - p.custo_producao_saca
            ui.numeros([
                ("Sua safra", f"{sacas:,.0f} sacas".replace(",", "."), ""),
                ("Custo por saca", brl(p.custo_producao_saca), ""),
                ("Margem na colheita", brl_sinal(margem), ui.classe(margem)),
            ])

        # ---- cenários e melhor mês lado a lado em telas largas
        e1, e2 = st.columns([1, 1], gap="large")
        with e1:
            st.subheader(f"Quatro jeitos de vender, guardando até {nome_alvo}")
            linhas = []
            for c in lista:
                r = tabela.loc[c.nome]
                diff = c.liquido_saca - p.preco_colheita
                meta = [f"{brl(c.caixa_colheita, 0)} entra na colheita"]
                if c is not lista[0]:
                    meta.insert(0, f"melhor que a colheita em {r['anos_melhor']} de {r['anos']} anos")
                linhas.append({
                    "nome": c.nome,
                    "pior": diff.min(), "mediana": diff.median(), "melhor": diff.max(),
                    "rec": c.nome == rec.nome,
                    "meta": meta,
                    "alerta": None if c.paga_contas else "não paga as contas da colheita",
                })
            ui.cenarios(linhas)
            with st.expander("Como cada jeito funciona"):
                for c in lista:
                    st.markdown(f"**{c.nome}.** {c.descricao}")

        with e2:
            st.subheader("Em que mês costuma compensar")
            por_mes = cen.ganho_por_mes(p, fatores)
            meses_nome = [saz.nome_mes(4, k) for k in por_mes["k"]]
            fig = ui.faixa_por_mes(
                meses_nome, por_mes["pior"], por_mes["mediana"], por_mes["melhor"],
                "R$/saca vs. vender na colheita",
                "%{x}: %{y:,.2f} R$/saca<extra></extra>",
            )
            st.plotly_chart(fig, width="stretch", config=ui.CONFIG_GRAFICO, theme=None)
            ui.nota(
                "Guardando tudo, com financiamento de estocagem para as contas e CDI sobre o "
                f"resto. Faixa: pior e melhor ano entre {periodo}."
            )

        with st.expander("Ver ano a ano"):
            ano_a_ano = pd.DataFrame({c.nome: c.liquido_saca for c in lista}).round(2)
            ano_a_ano.insert(0, f"Preço de {nome_alvo} ÷ colheita", fatores[mes_alvo].round(3))
            st.dataframe(ano_a_ano, width="stretch")
            ui.nota(
                "Para cada ano, aplicamos ao seu preço de colheita a variação que aconteceu "
                "entre mar/abr e o mês de venda. Valores em R$/saca, já descontados os custos. "
                "Fonte: indicador do arroz em casca CEPEA/IRGA-RS."
            )

# ======================================================================== GADO
with aba_gado:
    mes_atual = date.today().month
    col_campos, col_result = st.columns(LAYOUT, gap="large")

    with col_campos, st.container(key="campos_gado"):
        st.subheader("Seu lote")
        c1, c2 = pares()
        cabecas = c1.number_input("Cabeças", 1, 100_000, 100, step=10)
        peso = c2.number_input("Peso vivo médio hoje (kg)", 100.0, 900.0, 450.0, step=10.0, format="%.0f")
        preco_arroba = st.number_input(
            "Preço hoje (R$/@)", 50.0, 1000.0, float(round(ultimo_boi["preco"], 2)), step=5.0,
            help=f"Padrão: indicador do boi gordo CEPEA/ESALQ de {ultimo_boi['data']:%d/%m/%Y}. "
            "Troque pelo preço que você recebe no RS.",
        )
        meses_gado = st.slider("Segurar por (meses)", 1, 12, 4)
        contas_gado = st.number_input(
            "Contas que vencem agora (R$)", 0.0, 1e9, 60_000.0, step=5_000.0, format="%.0f",
            help="O que precisa ser pago já: a pressão que obriga a vender parte do lote mesmo "
            "sem ser o melhor momento.",
        )
        with st.expander("Ganho de peso e custos"):
            c1, c2 = pares()
            ganho_dia = c1.number_input("Ganho de peso (kg/dia)", 0.0, 2.0, 0.5, step=0.05)
            custo_cab = c2.number_input("Custo por cabeça (R$/mês)", 0.0, 1000.0, 60.0, step=5.0)
            rendimento = st.number_input("Rendimento de carcaça (%)", 40.0, 60.0, 50.0, step=0.5) / 100

    pg = cen.ParametrosGado(
        cabecas=cabecas, peso_kg=peso, preco_arroba=preco_arroba, meses=meses_gado,
        ganho_kg_dia=ganho_dia, custo_cabeca_mes=custo_cab, cdi_aa=cdi,
        rendimento_carcaca=rendimento, contas_vencem=contas_gado,
    )
    fatores_boi = saz.fatores_por_ano(precos_boi, (mes_atual,), horizonte=12, anos=anos_hist)
    g = cen.segurar_gado(pg, fatores_boi)["ganho_cabeca"]
    mes_venda = saz.nome_mes(mes_atual, meses_gado)
    anos_bons = int((g > 0).sum())
    cab_vender = pg.cabecas_para_contas
    cab_segurar = cabecas - cab_vender

    with col_result:
        if cab_vender > 0:
            ui.aviso(
                f"Para cobrir as contas, venda <b>{cab_vender} cabeças agora</b> "
                f"({brl(cab_vender * pg.valor_cabeca_hoje, 0)} de caixa) e segure as outras "
                f"<b>{cab_segurar}</b>. O ganho abaixo já é a média do lote inteiro."
            )
        v1, v2 = st.columns([1.25, 1], gap="large")
        with v1:
            if g.median() > 0 and anos_bons > len(g) / 2:
                frase = (
                    f"São <b>{brl(g.median() * cabecas, 0)}</b> a mais no lote. Segurar compensou "
                    f"em {anos_bons} de {len(g)} anos."
                )
            else:
                frase = (
                    f"Segurar só compensou em {anos_bons} de {len(g)} anos. "
                    "<b>Vender agora é o mais seguro.</b>"
                )
            ui.veredito(f"Segurar até {mes_venda}, no ano típico, rende", g.median(), "por cabeça", frase)
        with v2:
            ui.numeros([
                ("Pior ano", brl_sinal(g.min(), 0), ui.classe(g.min())),
                ("Ano mediano", brl_sinal(g.median(), 0), ui.classe(g.median())),
                ("Melhor ano", brl_sinal(g.max(), 0), ui.classe(g.max())),
            ], topo=True)

        st.subheader("Em que mês vender")
        curva = []
        for n in range(1, 13):
            gn = cen.segurar_gado(cen.ParametrosGado(**{**pg.__dict__, "meses": n}), fatores_boi)["ganho_cabeca"]
            curva.append((saz.nome_mes(mes_atual, n), gn.min(), gn.median(), gn.max()))
        meses_g, pior_g, med_g, melhor_g = zip(*curva)
        fig = ui.faixa_por_mes(
            list(meses_g), list(pior_g), list(med_g), list(melhor_g),
            "R$/cabeça vs. vender hoje",
            "vender em %{x}: %{y:,.0f} R$/cabeça<extra></extra>",
        )
        st.plotly_chart(fig, width="stretch", config=ui.CONFIG_GRAFICO, theme=None)
        ui.nota(
            "Já descontados o custo de manutenção e o CDI sobre o valor do animal. "
            "Sazonalidade do indicador do boi gordo CEPEA/ESALQ (SP), usada como referência "
            "até incluirmos a série do NESPRO/UFRGS para o RS."
        )

# ====================================================================== CAIXA
with aba_caixa:
    col_campos, col_result = st.columns(LAYOUT, gap="large")

    with col_campos, st.container(key="campos_caixa"):
        st.subheader("Quanto custa o adiantamento")
        st.markdown(
            "Receber adiantado do comprador com desconto no preço é um empréstimo. "
            "Veja os juros que estão embutidos nele."
        )
        c1, c2 = pares()
        desconto = c1.number_input("Desconto no preço (%)", 0.0, 50.0, 8.0, step=0.5) / 100
        antecedencia = c2.number_input("Meses de antecedência", 1, 12, 4)
        taxa_adiant = cen.juros_implicitos_adiantamento(desconto, antecedencia)

        ui.taxas([
            ("Adiantamento", taxa_adiant, True),
            ("Financiar estocagem", juros_fin, False),
            ("CDI", cdi, False),
        ])
        if taxa_adiant > juros_fin:
            st.markdown(
                f"O adiantamento custa **{pct(taxa_adiant - juros_fin)} ao ano a mais** que o "
                "financiamento de estocagem. Vale procurar o crédito formal."
            )

    with col_result:
        st.subheader("Como atravessar o aperto de caixa")
        ui.instrumentos([
            ("EGF (Plano Safra)",
             "Financiamento de estocagem. O produto fica guardado como garantia e o "
             "dinheiro paga as contas da colheita."),
            ("CDA/WA",
             "Títulos emitidos por armazém certificado. Você guarda o arroz e usa o "
             "warrant como garantia para conseguir crédito no banco."),
            ("CPR",
             "Cédula de Produto Rural. Vende antecipado ou capta crédito com entrega "
             "futura do produto. Atenção ao desconto embutido."),
            ("Venda escalonada",
             "Vende agora só o necessário para as contas e o resto em parcelas, para "
             "não depender de acertar um único mês."),
        ])
        ui.nota("Taxas e condições variam por banco e por safra. Confirme com seu banco ou cooperativa.")
