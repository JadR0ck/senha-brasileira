#!/usr/bin/env python3
"""
gerar.py — gera senhas brasileiras memoráveis a partir de bancos.json.

Mesma lógica do site, mas na linha de comando. Usa o módulo `secrets`
(gerador criptográfico do Python, equivalente ao crypto.getRandomValues
do navegador) — nada de random.random(), que é previsível.

Uso:
    python3 gerar.py                    # 1 senha
    python3 gerar.py -n 5               # 5 senhas
    python3 gerar.py --site instagram   # com prefixo de 2 letras do site
    python3 gerar.py -n 5 --site nubank
"""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

BANCOS = Path(__file__).resolve().parent / "bancos.json"


def carregar() -> dict:
    if not BANCOS.exists():
        raise SystemExit(
            "bancos.json não encontrado. Rode antes:  python3 atualizar_bancos.py"
        )
    return json.loads(BANCOS.read_text("utf-8"))


def compor(banco: dict) -> str:
    """{símbolo}{referência}-{verboCONJUGADO}{número} — cada peça sorteada."""
    sp = secrets.choice(banco["specials"])
    rf = secrets.choice(banco["refs"])
    vb = secrets.choice(banco["verbs"])
    nm = secrets.choice(banco["nums"])
    sep = "-" if secrets.randbelow(2) else ""
    return f"{sp}{rf}{sep}{vb}{nm}"


def prefixo(site: str) -> str:
    letras = "".join(c for c in site if c.isalpha())
    return (letras[:2] or "XX").upper()


def forca(senha: str) -> str:
    classes = sum([
        any(c.islower() for c in senha),
        any(c.isupper() for c in senha),
        any(c.isdigit() for c in senha),
        any(not c.isalnum() for c in senha),
    ])
    if len(senha) >= 20 and classes >= 3:
        return "Excelente"
    if len(senha) >= 14 and classes >= 3:
        return "Forte"
    return "Boa"


def main() -> int:
    ap = argparse.ArgumentParser(description="Gerador de senhas brasileiras.")
    ap.add_argument("-n", type=int, default=1, help="quantas senhas gerar")
    ap.add_argument("--site", help="prefixa a senha com 2 letras do site")
    args = ap.parse_args()

    banco = carregar()
    pfx = prefixo(args.site) if args.site else ""

    print(f"# fonte: {banco['fonte']}  ·  atualizado: {banco['gerado_em']}")
    for _ in range(max(1, args.n)):
        senha = pfx + compor(banco)
        print(f"{senha:<40}  [{len(senha)} car · {forca(senha)}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
