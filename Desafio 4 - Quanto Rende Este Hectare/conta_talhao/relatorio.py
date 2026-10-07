"""Relatório em PDF para levar ao gerente do banco: custo e produtividade por área."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .motor import CATEGORIAS_CUSTO

VERDE_AGUA = (31, 95, 107)
CINZA = (90, 100, 98)


def _rs(v: float | None, casas: int = 0) -> str:
    if v is None:
        return "-"
    s = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + "R$ " + s


def _n(v: float, casas: int = 0) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


class _PDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", size=8)
        self.set_text_color(*CINZA)
        self.cell(0, 6, f"Conta do Talhão  |  gerado em {date.today():%d/%m/%Y}  |  página {self.page_no()}", align="R")


def gerar(painel: dict, nome_fazenda: str = "Propriedade de demonstração", safra: str = "2025/26") -> bytes:
    pdf = _PDF(format="A4")
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_margins(16, 16, 16)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*VERDE_AGUA)
    pdf.cell(0, 10, "Custo e resultado por área", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, f"{nome_fazenda}, safra {safra}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    f = painel["fazenda"]
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(
        0, 5.5,
        f"Lavoura de arroz irrigado com {_n(f['area_ha'])} ha e {_n(f['sacas'])} sacas colhidas "
        f"({_n(f['sacas'] / f['area_ha'])} sc/ha). Custo médio de {_rs(f['custo_ha'])}/ha, "
        f"ou {_rs(f['custo_saca'], 2)} por saca. Os valores vêm de notas fiscais, contas de luz e romaneios "
        "registrados durante a safra; a energia de cada bomba é dividida entre os talhões que ela irriga "
        "e os gastos gerais são divididos por área.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(4)

    def tabela(titulo, cab, linhas, larguras, alinhar):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*VERDE_AGUA)
        pdf.cell(0, 8, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", size=9)
        with pdf.table(col_widths=larguras, text_align=alinhar, line_height=6.5,
                       headings_style=_cab_estilo(), borders_layout="HORIZONTAL_LINES") as t:
            r = t.row()
            for c in cab:
                r.cell(c)
            for linha in linhas:
                r = t.row()
                for c in linha:
                    r.cell(c)
        pdf.ln(5)

    tabela(
        "Talhões",
        ["Talhão", "Área (ha)", "sc/ha", "Custo/ha", "Custo/saca", "Preço médio", "Margem/ha"],
        [[t["nome"], _n(t["area_ha"]), _n(t["sacas_ha"]), _rs(t["custo_ha"]), _rs(t["custo_saca"], 2),
          _rs(t["preco_medio"], 2), _rs(t["margem_ha"])] for t in painel["talhoes"]]
        + [["Fazenda", _n(f["area_ha"]), _n(f["sacas"] / f["area_ha"]), _rs(f["custo_ha"]), _rs(f["custo_saca"], 2),
            _rs(f["receita"] / f["sacas"] if f["sacas"] else None, 2), _rs(f["margem"] / f["area_ha"])]],
        (44, 18, 14, 24, 24, 24, 24), ("LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"),
    )

    cats = [(CATEGORIAS_CUSTO[c], v) for c, v in sorted(f["media_categoria_ha"].items(), key=lambda kv: -kv[1]) if v]
    tabela(
        "Composição do custo da lavoura",
        ["Item", "R$/ha", "% do custo"],
        [[nome, _rs(v), f"{v / f['custo_ha']:.0%}"] for nome, v in cats],
        (90, 44, 38), ("LEFT", "RIGHT", "RIGHT"),
    )

    if painel["lotes"]:
        tabela(
            "Pecuária",
            ["Lote", "Cabeças", "Custo/cabeça", "Receita", "Resultado/cabeça"],
            [[lt["nome"], _n(lt["cabecas"]), _rs(lt["custo_cabeca"]), _rs(lt["receita"]), _rs(lt["resultado_cabeca"])]
             for lt in painel["lotes"]],
            (56, 22, 32, 32, 36), ("LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"),
        )

    if painel["alertas"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*VERDE_AGUA)
        pdf.cell(0, 8, "Pontos de atenção e o que está sendo feito", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", size=9.5)
        for a in painel["alertas"]:
            pdf.multi_cell(0, 5.2, "- " + a["texto"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    return bytes(pdf.output())


def _cab_estilo():
    from fpdf.fonts import FontFace
    return FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=VERDE_AGUA)
