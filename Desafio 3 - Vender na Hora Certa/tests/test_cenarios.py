import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hora_certa import cenarios as c  # noqa: E402
from hora_certa import sazonalidade as s  # noqa: E402


def fatores_constantes(valor: float, anos=(2020, 2021, 2022), horizonte=10):
    return pd.DataFrame(
        valor, index=pd.Index(anos, name="ano"), columns=range(1, horizonte + 1)
    )


def params(**kw):
    base = dict(
        sacas=1000,
        preco_colheita=80.0,
        contas_colheita=20_000.0,
        mes_alvo=4,
        cdi_aa=0.12,
        juros_financiamento_aa=0.08,
        armazenagem_mes=1.0,
        recepcao_secagem=3.0,
        quebra_mes=0.0,
    )
    base.update(kw)
    return c.ParametrosArroz(**base)


def test_fator_juros_um_ano():
    assert c.fator_juros(0.12, 12) == pytest.approx(0.12)
    assert c.fator_juros(0.12, 0) == 0


def test_juros_adiantamento():
    # 10% de desconto por 6 meses de antecedência ≈ 23,5% a.a.
    assert c.juros_implicitos_adiantamento(0.10, 6) == pytest.approx(0.2346, abs=1e-3)


def test_preco_parado_guardar_so_perde_custos():
    p = params()
    cen = {x.nome: x for x in c.cenarios_arroz(p, fatores_constantes(1.0))}
    esperado = 80 - (1.0 * 4 + 3.0) - 80 * c.fator_juros(0.12, 4)
    assert cen["Armazenar e vender depois"].liquido_saca.iloc[0] == pytest.approx(esperado)
    assert cen["Vender tudo na colheita"].liquido_saca.iloc[0] == 80


def test_financiar_usa_juros_do_financiamento_na_parte_financiada():
    p = params()
    fin = {x.nome: x for x in c.cenarios_arroz(p, fatores_constantes(1.0))}[
        "Financiar a estocagem"
    ]
    financiado_saca = 20.0  # 20 mil / 1000 sacas
    custo_dinheiro = financiado_saca * c.fator_juros(0.08, 4) + 60 * c.fator_juros(0.12, 4)
    assert fin.liquido_saca.iloc[0] == pytest.approx(80 - 7 - custo_dinheiro)
    assert fin.caixa_colheita == 20_000
    assert fin.paga_contas


def test_financiamento_limitado_ao_percentual_do_estoque():
    p = params(contas_colheita=70_000, percentual_financiavel=0.5)
    fin = c.cenarios_arroz(p, fatores_constantes(1.0))[2]
    assert fin.caixa_colheita == 40_000
    assert not fin.paga_contas


def test_escalonada_vende_o_necessario_para_as_contas():
    p = params()  # contas = 25% da safra
    esc = c.cenarios_arroz(p, fatores_constantes(1.2))[3]
    assert esc.vendas[0] == (0, pytest.approx(0.25))
    assert sum(f for _, f in esc.vendas) == pytest.approx(1.0)
    assert esc.paga_contas


def test_guardar_sem_caixa_nao_paga_contas():
    guardar = c.cenarios_arroz(params(), fatores_constantes(1.2))[1]
    assert not guardar.paga_contas
    assert c.cenarios_arroz(params(contas_colheita=0), fatores_constantes(1.2))[1].paga_contas


def test_recomenda_colheita_quando_esperar_nao_compensa():
    p = params()
    cens = c.cenarios_arroz(p, fatores_constantes(1.0))
    assert c.recomendar(p, cens).nome == "Vender tudo na colheita"


def test_recomenda_esperar_quando_alta_e_consistente():
    p = params()
    cens = c.cenarios_arroz(p, fatores_constantes(1.25))
    rec = c.recomendar(p, cens)
    assert rec.nome in {"Financiar a estocagem", "Venda escalonada"}
    assert rec.paga_contas


def test_gado_preco_parado_sem_ganho_de_peso_perde_custos():
    p = c.ParametrosGado(
        cabecas=10, peso_kg=450, preco_arroba=300, meses=3,
        ganho_kg_dia=0, custo_cabeca_mes=50, cdi_aa=0.0,
    )
    r = c.segurar_gado(p, fatores_constantes(1.0))
    assert r["ganho_cabeca"].iloc[0] == pytest.approx(-150)


def test_sazonalidade_razao_contra_media_da_colheita():
    datas = pd.date_range("2020-01-01", "2021-12-31", freq="D")
    # mar/abr = 100, depois 110
    preco = [100.0 if d.month in (3, 4) else 110.0 for d in datas]
    df = pd.DataFrame({"data": datas, "preco": preco})
    f = s.fatores_por_ano(df, (3, 4), horizonte=6, anos=None)
    assert list(f.index) == [2020, 2021]
    assert f.loc[2020, 1] == pytest.approx(1.1)
    assert s.nome_mes(4, 1) == "mai"
    assert s.nome_mes(4, 10) == "fev"
