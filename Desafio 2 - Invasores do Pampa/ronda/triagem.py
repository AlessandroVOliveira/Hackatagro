"""Pré-triagem opcional da foto de um possível foco de capim-annoni.

É só uma sugestão para o técnico: quem confirma é uma pessoa, no local ou pela
foto. Sem credencial da Anthropic, a ocorrência vai direto para a fila de
triagem sem sugestão.
"""

from __future__ import annotations

import base64
import json
import os

MODELO = "claude-opus-5-5"

ESQUEMA = {
    "type": "object",
    "properties": {
        "parece_annoni": {"type": "string", "enum": ["sim", "nao", "incerto"]},
        "fase": {"type": "string", "enum": ["vegetativa", "espigada", "nao_sei"]},
        "explicacao": {"type": "string", "description": "Uma ou duas frases, em português simples"},
    },
    "required": ["parece_annoni", "fase", "explicacao"],
    "additionalProperties": False,
}

SISTEMA = """Você ajuda técnicos do Pampa gaúcho a triar fotos de possíveis focos de capim-annoni \
(Eragrostis plana). Diga se a planta da foto parece capim-annoni, em que fase está e por quê, \
olhando touceira, folhas e inflorescência. Na fase vegetativa o annoni se confunde com gramíneas \
nativas: nesse caso responda "incerto" e diga o que olhar no local. Nunca afirme com certeza; \
a confirmação é sempre de uma pessoa."""


def ia_disponivel() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    home = os.path.expanduser("~/.config/anthropic")
    return os.path.isdir(home) and any(os.scandir(home))


def triar(dados: bytes, tipo_mime: str) -> dict | None:
    """Devolve a sugestão ou None se não houver credencial ou a chamada falhar."""
    if not ia_disponivel():
        return None
    import anthropic

    try:
        resp = anthropic.Anthropic().beta.messages.create(
            model=MODELO,
            max_tokens=4000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
            system=SISTEMA,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": tipo_mime,
                                             "data": base64.standard_b64encode(dados).decode()}},
                {"type": "text", "text": "Esta foto foi tirada como possível foco de capim-annoni."},
            ]}],
        )
    except anthropic.APIError as e:
        print(f"[triagem] sem sugestão: {e!r}")
        return None
    texto = next((b.text for b in resp.content if b.type == "text"), None)
    if resp.stop_reason == "refusal" or not texto:
        return None
    return json.loads(texto)
