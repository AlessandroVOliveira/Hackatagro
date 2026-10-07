"""Sazonalidade histórica: quanto o preço de cada mês ficou acima ou abaixo
do preço de referência (colheita), ano a ano.

Trabalhar com razões (preço do mês ÷ preço da colheita do mesmo ano) elimina a
inflação e o nível de preço de cada safra, e permite aplicar o histórico ao
preço de hoje.
"""

from __future__ import annotations

import pandas as pd

NOMES_MESES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]


def mensal(precos: pd.DataFrame) -> pd.Series:
    """Média mensal da série diária (índice = primeiro dia do mês)."""
    return precos.set_index("data")["preco"].resample("MS").mean().dropna()


def fatores_por_ano(
    precos: pd.DataFrame,
    meses_ref: tuple[int, ...],
    horizonte: int = 10,
    anos: int | None = 15,
) -> pd.DataFrame:
    """Razão preço(mês ref + k) / preço(ref), uma linha por ano.

    meses_ref: meses que formam o preço de referência, ex.: (3, 4) para a
        colheita do arroz. O mês k=1 é o mês seguinte ao último de meses_ref.
    horizonte: quantos meses à frente calcular.
    anos: usar só os N anos completos mais recentes (None = todos).
    """
    m = mensal(precos)
    ultimo_ref = meses_ref[-1]
    linhas = {}
    for ano in sorted(set(m.index.year)):
        refs = [pd.Timestamp(ano, mes, 1) for mes in meses_ref]
        if not all(r in m.index for r in refs):
            continue
        preco_ref = m[refs].mean()
        base = pd.Timestamp(ano, ultimo_ref, 1)
        linha = {}
        for k in range(1, horizonte + 1):
            mes = base + pd.DateOffset(months=k)
            if mes in m.index:
                linha[k] = m[mes] / preco_ref
        if len(linha) == horizonte:
            linhas[ano] = linha
    df = pd.DataFrame.from_dict(linhas, orient="index").sort_index()
    df.index.name = "ano"
    if anos is not None:
        df = df.tail(anos)
    return df


def nome_mes(mes_ref: int, k: int) -> str:
    """Nome do mês que fica k meses depois de mes_ref (1-12)."""
    return NOMES_MESES[(mes_ref - 1 + k) % 12]


def resumo(fatores: pd.DataFrame) -> pd.DataFrame:
    """Pior, mediana e melhor ano para cada mês à frente."""
    return pd.DataFrame(
        {
            "pior": fatores.min(),
            "mediana": fatores.median(),
            "melhor": fatores.max(),
            "anos_acima": (fatores > 1).sum(),
            "anos": fatores.count(),
        }
    )
