"""Configura o WhatsApp do Conta do Talhão na Evolution API.

  python configurar.py iniciar    cria o .env com segredos aleatórios
  python configurar.py conectar   cria a instância, liga o webhook e salva o QR code
  python configurar.py status     mostra se o WhatsApp está conectado
"""

from __future__ import annotations

import base64
import re
import secrets
import sys
from pathlib import Path

import httpx

PASTA = Path(__file__).resolve().parent
ENV = PASTA / ".env"


def ler_env() -> dict[str, str]:
    if not ENV.exists():
        sys.exit("Falta o .env. Rode primeiro: python configurar.py iniciar")
    brutos = {}
    for linha in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            brutos[k.strip()] = v.strip()
    # resolve ${VAR}
    return {k: re.sub(r"\$\{(\w+)\}", lambda m: brutos.get(m.group(1), ""), v) for k, v in brutos.items()}


def iniciar() -> None:
    if ENV.exists():
        print(f".env já existe em {ENV}; nada mudou.")
        return
    texto = (PASTA / ".env.example").read_text(encoding="utf-8")
    texto = re.sub(r"<gerado>", lambda _: secrets.token_hex(24), texto)
    # grava valores já resolvidos: ${VAR} vira o valor definido antes no arquivo
    vistos: dict[str, str] = {}
    linhas = []
    for linha in texto.splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            v = re.sub(r"\$\{(\w+)\}", lambda m: vistos.get(m.group(1), ""), v)
            vistos[k.strip()] = v
            linha = f"{k}={v}"
        linhas.append(linha)
    ENV.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"Criado {ENV}. Agora suba a Evolution: docker compose up -d")


def _cliente(env):
    return httpx.Client(base_url=env["EVOLUTION_URL"], headers={"apikey": env["EVOLUTION_APIKEY"]}, timeout=30)


def conectar() -> None:
    env = ler_env()
    inst = env["EVOLUTION_INSTANCIA"]
    with _cliente(env) as c:
        existentes = c.get("/instance/fetchInstances").raise_for_status().json()
        nomes = {i.get("name") or (i.get("instance") or {}).get("instanceName") for i in existentes}
        if inst not in nomes:
            c.post("/instance/create", json={
                "instanceName": inst, "integration": "WHATSAPP-BAILEYS", "qrcode": True,
                "groupsIgnore": True, "rejectCall": False, "readMessages": True,
            }).raise_for_status()
            print(f"Instância {inst} criada.")

        c.post(f"/webhook/set/{inst}", json={"webhook": {
            "enabled": True,
            "url": env["WHATSAPP_WEBHOOK_URL"],
            "headers": {"x-webhook-token": env["WHATSAPP_WEBHOOK_TOKEN"]},
            "byEvents": False,
            "base64": True,
            "events": ["MESSAGES_UPSERT"],
        }}).raise_for_status()
        print(f"Webhook ligado em {env['WHATSAPP_WEBHOOK_URL']}")

        estado = c.get(f"/instance/connectionState/{inst}").raise_for_status().json()
        if (estado.get("instance") or {}).get("state") == "open":
            print("WhatsApp já está conectado.")
            return
        qr = c.get(f"/instance/connect/{inst}").raise_for_status().json()
        b64 = (qr.get("base64") or "").split(",", 1)[-1]
        if not b64:
            sys.exit(f"A Evolution não devolveu QR code: {qr}")
        destino = PASTA / "qrcode.png"
        destino.write_bytes(base64.b64decode(b64))
        print(f"\nQR code salvo em {destino}")
        print("No celular: WhatsApp > Aparelhos conectados > Conectar um aparelho, e escaneie.")
        print("O QR expira em cerca de 1 minuto; se expirar, rode este comando de novo.")


def status() -> None:
    env = ler_env()
    with _cliente(env) as c:
        print(c.get(f"/instance/connectionState/{env['EVOLUTION_INSTANCIA']}").json())


if __name__ == "__main__":
    {"iniciar": iniciar, "conectar": conectar, "status": status}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__)
    )()
