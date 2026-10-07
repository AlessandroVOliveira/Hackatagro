"""Download e leitura das séries de preço (CEPEA) e de juros (Banco Central)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"

# Séries diárias do CEPEA, preço à vista em R$.
SERIES_CEPEA = {
    # Indicador do arroz em casca CEPEA/IRGA-RS, R$ por saca de 50 kg.
    "arroz": "https://www.cepea.org.br/br/indicador/series/arroz.aspx?id=91",
    # Indicador do boi gordo CEPEA/ESALQ (SP), R$ por arroba. Usado como
    # referência de sazonalidade para o RS até termos a série do NESPRO.
    "boi": "https://www.cepea.org.br/br/indicador/series/boi-gordo.aspx?id=2",
}

# Séries do SGS/Banco Central, em % ao ano.
SERIES_BCB = {"selic": 432, "cdi": 4389}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130 Safari/537.36"
)


def ler_planilha_cepea(conteudo: bytes) -> pd.DataFrame:
    """Converte a planilha .xls do CEPEA em DataFrame com colunas data e preco."""
    # As planilhas do CEPEA vêm com um defeito de estrutura que o xlrd recusa
    # por padrão; o conteúdo em si é válido.
    bruto = pd.read_excel(
        io.BytesIO(conteudo),
        header=None,
        engine="xlrd",
        engine_kwargs={"ignore_workbook_corruption": True},
    )
    datas = pd.to_datetime(bruto[0], format="%d/%m/%Y", errors="coerce")
    precos = pd.to_numeric(bruto[1], errors="coerce")
    df = pd.DataFrame({"data": datas, "preco": precos}).dropna()
    return df.sort_values("data").reset_index(drop=True)


def baixar_cepea(produto: str) -> pd.DataFrame:
    import requests

    resp = requests.get(
        SERIES_CEPEA[produto], headers={"User-Agent": USER_AGENT}, timeout=60
    )
    resp.raise_for_status()
    return ler_planilha_cepea(resp.content)


def baixar_juros() -> dict:
    import requests

    juros = {}
    for nome, codigo in SERIES_BCB.items():
        url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}"
            "/dados/ultimos/1?formato=json"
        )
        ultimo = requests.get(url, timeout=30).json()[-1]
        juros[nome] = {"data": ultimo["data"], "taxa_aa": float(ultimo["valor"])}
    return juros


def atualizar_tudo(pasta: Path = PASTA_DADOS) -> None:
    """Baixa todas as séries e salva em data/ para o app funcionar offline."""
    pasta.mkdir(parents=True, exist_ok=True)
    for produto in SERIES_CEPEA:
        df = baixar_cepea(produto)
        df.to_csv(pasta / f"{produto}_cepea.csv", index=False)
        print(f"{produto}: {len(df)} cotações até {df['data'].max():%d/%m/%Y}")
    juros = baixar_juros()
    (pasta / "juros.json").write_text(json.dumps(juros, indent=2), encoding="utf-8")
    print("juros:", juros)


def carregar_precos(produto: str, pasta: Path = PASTA_DADOS) -> pd.DataFrame:
    return pd.read_csv(pasta / f"{produto}_cepea.csv", parse_dates=["data"])


def carregar_juros(pasta: Path = PASTA_DADOS) -> dict:
    return json.loads((pasta / "juros.json").read_text(encoding="utf-8"))
