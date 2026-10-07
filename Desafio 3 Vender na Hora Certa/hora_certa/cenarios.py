"""Conta líquida de cada cenário de venda, em R$ por saca e por cabeça.

Cada cenário é avaliado contra todos os anos do histórico: aplicamos a
variação de preço que aconteceu em cada ano ao preço de hoje. O resultado é
uma faixa (pior, mediana, melhor ano), nunca uma previsão única.

Todo valor "líquido" já desconta o custo do dinheiro parado (juros do
financiamento ou o que o dinheiro renderia no CDI), então é comparável ao
preço recebido na colheita.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

DIAS_MES = 30.4
KG_ARROBA = 15.0


def fator_juros(taxa_aa: float, meses: float) -> float:
    """Juros compostos acumulados em `meses` para uma taxa anual (0.12 = 12%)."""
    return (1 + taxa_aa) ** (meses / 12) - 1


def juros_implicitos_adiantamento(desconto: float, meses: float) -> float:
    """Taxa anual embutida num adiantamento que paga (1 - desconto) do preço
    `meses` antes da entrega."""
    return (1 / (1 - desconto)) ** (12 / meses) - 1


# ---------------------------------------------------------------- arroz


@dataclass
class ParametrosArroz:
    sacas: float
    preco_colheita: float  # R$/saca hoje
    contas_colheita: float  # R$ que precisam ser pagos na colheita
    mes_alvo: int  # meses depois da colheita (1 = mês seguinte a abril)
    cdi_aa: float  # 0.1365 = 13,65% a.a.
    juros_financiamento_aa: float = 0.12
    percentual_financiavel: float = 0.70  # do valor do estoque
    armazenagem_mes: float = 1.00  # R$/saca/mês em armazém de terceiros
    recepcao_secagem: float = 3.00  # R$/saca, cobrado uma vez
    frete_armazem: float = 0.0  # R$/saca
    quebra_mes: float = 0.003  # fração perdida por mês armazenado
    custo_producao_saca: float | None = None
    parcela_colheita: float | None = None  # escalonada; None = só o das contas

    @property
    def valor_safra_colheita(self) -> float:
        return self.sacas * self.preco_colheita

    @property
    def fracao_para_contas(self) -> float:
        """Fração da safra que precisa ser vendida na colheita para pagar as contas."""
        if self.valor_safra_colheita <= 0:
            return 0.0
        return min(1.0, self.contas_colheita / self.valor_safra_colheita)


@dataclass
class Cenario:
    nome: str
    descricao: str
    liquido_saca: pd.Series  # R$/saca por ano do histórico
    caixa_colheita: float  # R$ que entra na colheita
    vendas: list[tuple[int, float]] = field(default_factory=list)  # (mês k, fração)
    paga_contas: bool = True

    def faixa(self) -> dict:
        s = self.liquido_saca
        return {"pior": s.min(), "mediana": s.median(), "melhor": s.max()}


def _liquido_guardado(
    p: ParametrosArroz, fator_preco: pd.Series, k: int, financiado_saca: float = 0.0
) -> pd.Series:
    """R$/saca líquido de guardar até o mês k e vender lá."""
    preco_venda = p.preco_colheita * fator_preco * (1 - p.quebra_mes * k)
    custos_fisicos = p.armazenagem_mes * k + p.recepcao_secagem + p.frete_armazem
    proprio_saca = p.preco_colheita - financiado_saca
    custo_dinheiro = financiado_saca * fator_juros(
        p.juros_financiamento_aa, k
    ) + proprio_saca * fator_juros(p.cdi_aa, k)
    return preco_venda - custos_fisicos - custo_dinheiro


def cenarios_arroz(p: ParametrosArroz, fatores: pd.DataFrame) -> list[Cenario]:
    """Os quatro cenários de arroz para o mês-alvo escolhido.

    fatores: saída de sazonalidade.fatores_por_ano para a colheita (mar/abr).
    """
    k = p.mes_alvo
    anos = fatores.index
    base = pd.Series(p.preco_colheita, index=anos)
    paga_sem_vender = p.contas_colheita <= 0

    tudo_colheita = Cenario(
        nome="Vender tudo na colheita",
        descricao="O que acontece hoje: toda a safra vendida em mar/abr.",
        liquido_saca=base,
        caixa_colheita=p.valor_safra_colheita,
        vendas=[(0, 1.0)],
    )

    guardar = Cenario(
        nome="Armazenar e vender depois",
        descricao="Toda a safra vai para armazém de terceiros e é vendida no "
        "mês-alvo, sem financiamento.",
        liquido_saca=_liquido_guardado(p, fatores[k], k),
        caixa_colheita=0.0,
        vendas=[(k, 1.0)],
        paga_contas=paga_sem_vender,
    )

    limite_financiamento = p.percentual_financiavel * p.valor_safra_colheita
    financiado = min(p.contas_colheita, limite_financiamento)
    financiar = Cenario(
        nome="Financiar a estocagem",
        descricao="Toda a safra fica armazenada; um financiamento de "
        "estocagem (FEE/EGF, CDA/WA) paga as contas da colheita.",
        liquido_saca=_liquido_guardado(p, fatores[k], k, financiado / p.sacas),
        caixa_colheita=financiado,
        vendas=[(k, 1.0)],
        paga_contas=financiado >= p.contas_colheita,
    )

    # Escalonada: vende na colheita o necessário para as contas (ou a parcela
    # escolhida) e divide o resto em duas vendas, no meio do caminho e no alvo.
    x0 = p.parcela_colheita if p.parcela_colheita is not None else p.fracao_para_contas
    x0 = min(max(x0, 0.0), 1.0)
    meio = max(1, math.ceil(k / 2))
    meses_resto = sorted({meio, k})
    fracao_cada = (1 - x0) / len(meses_resto)
    liquido_escalonado = base * x0
    for km in meses_resto:
        liquido_escalonado = liquido_escalonado + fracao_cada * _liquido_guardado(
            p, fatores[km], km
        )
    escalonada = Cenario(
        nome="Venda escalonada",
        descricao=f"Vende {x0:.0%} na colheita para as contas e o resto em "
        f"{len(meses_resto)} parcelas iguais.",
        liquido_saca=liquido_escalonado,
        caixa_colheita=x0 * p.valor_safra_colheita,
        vendas=[(0, x0)] + [(km, fracao_cada) for km in meses_resto],
        paga_contas=x0 * p.valor_safra_colheita >= p.contas_colheita - 0.01,
    )

    return [tudo_colheita, guardar, financiar, escalonada]


def tabela_resultados(p: ParametrosArroz, cenarios: list[Cenario]) -> pd.DataFrame:
    """Resumo de cada cenário em R$/saca e na safra, comparado com vender tudo
    na colheita."""
    linhas = []
    for c in cenarios:
        f = c.faixa()
        diff = c.liquido_saca - p.preco_colheita
        linhas.append(
            {
                "cenario": c.nome,
                "pior": f["pior"],
                "mediana": f["mediana"],
                "melhor": f["melhor"],
                "ganho_mediano_saca": diff.median(),
                "ganho_mediano_safra": diff.median() * p.sacas,
                "anos_melhor": int((diff > 0).sum()),
                "anos": int(diff.count()),
                "caixa_colheita": c.caixa_colheita,
                "paga_contas": c.paga_contas,
            }
        )
    return pd.DataFrame(linhas)


def recomendar(p: ParametrosArroz, cenarios: list[Cenario]) -> Cenario:
    """O cenário com maior ganho mediano entre os que pagam as contas.

    Só recomenda esperar se esperar ganhou na maioria dos anos; caso contrário
    fica com a venda na colheita.
    """
    viaveis = [c for c in cenarios if c.paga_contas]
    melhor = max(viaveis, key=lambda c: c.liquido_saca.median())
    ganhou = (melhor.liquido_saca > p.preco_colheita).mean()
    if melhor.liquido_saca.median() <= p.preco_colheita or ganhou <= 0.5:
        return cenarios[0]
    return melhor


def ganho_por_mes(p: ParametrosArroz, fatores: pd.DataFrame) -> pd.DataFrame:
    """Ganho líquido de guardar com estocagem financiada, para cada mês de
    venda possível. Serve para mostrar qual mês costuma compensar."""
    linhas = []
    limite = p.percentual_financiavel * p.valor_safra_colheita
    financiado_saca = min(p.contas_colheita, limite) / p.sacas
    for k in fatores.columns:
        diff = _liquido_guardado(p, fatores[k], k, financiado_saca) - p.preco_colheita
        linhas.append(
            {
                "k": k,
                "pior": diff.min(),
                "mediana": diff.median(),
                "melhor": diff.max(),
                "anos_melhor": int((diff > 0).sum()),
                "anos": int(diff.count()),
            }
        )
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------- gado


@dataclass
class ParametrosGado:
    cabecas: int
    peso_kg: float  # peso vivo hoje
    preco_arroba: float  # R$/@ hoje
    meses: int  # quanto tempo segurar
    ganho_kg_dia: float  # ganho de peso esperado
    custo_cabeca_mes: float  # sal, suplemento, sanidade, arrendamento
    cdi_aa: float
    rendimento_carcaca: float = 0.50
    contas_vencem: float = 0.0  # R$ que precisam ser pagos agora, do lote

    @property
    def valor_cabeca_hoje(self) -> float:
        return arrobas(self.peso_kg, self.rendimento_carcaca) * self.preco_arroba

    @property
    def valor_lote_hoje(self) -> float:
        return self.valor_cabeca_hoje * self.cabecas

    @property
    def fracao_para_contas(self) -> float:
        """Fração do lote que precisa ser vendida agora para pagar as contas."""
        if self.valor_lote_hoje <= 0:
            return 0.0
        return min(1.0, self.contas_vencem / self.valor_lote_hoje)

    @property
    def cabecas_para_contas(self) -> int:
        """Nº de cabeças (arredondado para cima) que cobre as contas."""
        return math.ceil(self.fracao_para_contas * self.cabecas) if self.contas_vencem > 0 else 0


def arrobas(peso_kg: float, rendimento: float) -> float:
    return peso_kg * rendimento / KG_ARROBA


def segurar_gado(p: ParametrosGado, fatores: pd.DataFrame) -> pd.DataFrame:
    """Resultado médio por cabeça de segurar o gado `meses` meses, ano a ano.

    Se `contas_vencem` > 0, a fração necessária do lote é vendida agora (ganho
    zero, por definição) para pagar as contas, e só o resto é segurado — o
    mesmo raciocínio da venda escalonada do arroz. `fatores` é a saída de
    fatores_por_ano para o boi com meses_ref=(mês atual,).
    """
    valor_hoje = p.valor_cabeca_hoje
    peso_futuro = p.peso_kg + p.ganho_kg_dia * DIAS_MES * p.meses
    preco_futuro = p.preco_arroba * fatores[p.meses]
    valor_futuro = arrobas(peso_futuro, p.rendimento_carcaca) * preco_futuro
    custo = p.custo_cabeca_mes * p.meses + valor_hoje * fator_juros(p.cdi_aa, p.meses)
    ganho_segurando = valor_futuro - custo - valor_hoje
    x0 = p.fracao_para_contas
    return pd.DataFrame(
        {
            "valor_hoje": valor_hoje,
            "valor_futuro": valor_futuro,
            "custo": custo,
            "ganho_cabeca": (1 - x0) * ganho_segurando,
        }
    )
