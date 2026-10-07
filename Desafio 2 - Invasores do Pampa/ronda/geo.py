"""Contas de distância no plano. A vizinhança cabe num quadrado de ~20 km,
então uma projeção simples (equiretangular) em quilômetros basta.
"""

from __future__ import annotations

import math

# Canto sudoeste do mapa da vizinhança (interior de Alegrete/RS).
LAT0, LON0 = -29.900, -55.960
LARGURA_KM, ALTURA_KM = 16.0, 11.0
KM_LAT = 110.574
KM_LON = 111.320 * math.cos(math.radians(LAT0))


def para_km(lat: float, lon: float) -> tuple[float, float]:
    return ((lon - LON0) * KM_LON, (lat - LAT0) * KM_LAT)


def para_latlon(x: float, y: float) -> tuple[float, float]:
    return (round(LAT0 + y / KM_LAT, 6), round(LON0 + x / KM_LON, 6))


def no_mapa(x: float, y: float) -> bool:
    return 0 <= x <= LARGURA_KM and 0 <= y <= ALTURA_KM


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dist_segmento(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return dist(p, (a[0] + t * dx, a[1] + t * dy))


def dist_linha(p, linha) -> float:
    return min(dist_segmento(p, linha[i], linha[i + 1]) for i in range(len(linha) - 1))


def dentro(p, poligono) -> bool:
    x, y = p
    d = False
    j = len(poligono) - 1
    for i in range(len(poligono)):
        xi, yi = poligono[i]
        xj, yj = poligono[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            d = not d
        j = i
    return d


def dist_poligono(p, poligono) -> float:
    """Zero dentro; fora, a distância até a borda."""
    if dentro(p, poligono):
        return 0.0
    return dist_linha(p, list(poligono) + [poligono[0]])


def celula(p, lado: float = 1.0) -> tuple[int, int]:
    return (int(p[0] // lado), int(p[1] // lado))
