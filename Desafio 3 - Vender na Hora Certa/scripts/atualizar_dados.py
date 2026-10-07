"""Baixa as séries do CEPEA e as taxas do Banco Central para a pasta data/.

Uso: python scripts/atualizar_dados.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hora_certa.dados import atualizar_tudo  # noqa: E402

if __name__ == "__main__":
    atualizar_tudo()
