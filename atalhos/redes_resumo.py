#!/usr/bin/env python3
"""Resumo das redes (via Zernio) numa linha só, pro JARVIS falar rápido.

Uso:
  python3 atalhos/redes_resumo.py                                  # ontem, Instagram
  python3 atalhos/redes_resumo.py --dia hoje
  python3 atalhos/redes_resumo.py --dia 2026-10-21 --plataforma tiktok
  python3 atalhos/redes_resumo.py --de 2026-10-01 --ate 2026-10-21 # período inteiro, uma chamada

Precisa do zernio.py da skill publicar-agendar-posts (caminho em JARVIS_ZERNIO).
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

ZERNIO = Path(os.environ.get(
    "JARVIS_ZERNIO", "~/.claude/skills/publicar-agendar-posts/materiais/scripts/zernio.py")).expanduser()
FUSO = os.environ.get("JARVIS_FUSO", "America/Sao_Paulo")
POR_PAGINA = 100  # máximo que a Zernio aceita


def data(texto, hoje):
    if texto == "hoje":
        return hoje
    if texto == "ontem":
        return hoje - dt.timedelta(days=1)
    return dt.date.fromisoformat(texto)


def num(v):
    return v if isinstance(v, (int, float)) else 0


def pagina(plataforma, de, ate, n):
    caminho = f"/analytics?limit={POR_PAGINA}&page={n}&platform={plataforma}&fromDate={de}&toDate={ate}"
    saida = subprocess.run([sys.executable, str(ZERNIO), "api", "GET", caminho],
                           capture_output=True, text=True, timeout=90)
    try:
        return json.loads(saida.stdout)
    except ValueError:
        sys.exit("Zernio não respondeu: " + (saida.stderr or saida.stdout)[:300])


def buscar(plataforma, de, ate):
    """Todas as páginas do período; a 1ª diz quantas são e o resto vem em paralelo."""
    primeira = pagina(plataforma, de, ate, 1)
    posts = list(primeira.get("posts", []))
    paginas = int((primeira.get("pagination") or {}).get("pages") or 1)
    if paginas > 1:
        with ThreadPoolExecutor(max_workers=min(6, paginas - 1)) as grupo:
            for resto in grupo.map(lambda n: pagina(plataforma, de, ate, n), range(2, paginas + 1)):
                posts.extend(resto.get("posts", []))
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", default="ontem", help="hoje | ontem | AAAA-MM-DD")
    ap.add_argument("--de", help="início do período (AAAA-MM-DD, hoje ou ontem)")
    ap.add_argument("--ate", help="fim do período (AAAA-MM-DD, hoje ou ontem). Padrão: hoje")
    ap.add_argument("--plataforma", default="instagram")
    args = ap.parse_args()

    fuso = ZoneInfo(FUSO) if ZoneInfo else dt.timezone(dt.timedelta(hours=-3))
    hoje = dt.datetime.now(fuso).date()
    if args.de or args.ate:
        inicio = data(args.de, hoje) if args.de else data(args.ate, hoje)
        fim = data(args.ate, hoje) if args.ate else hoje
        if fim < inicio:
            inicio, fim = fim, inicio
    else:
        inicio = fim = data(args.dia, hoje)

    # um dia de folga em cada ponta por causa do fuso (a Zernio guarda em UTC)
    brutos = buscar(args.plataforma, inicio - dt.timedelta(days=1), fim + dt.timedelta(days=1))
    posts, vistos = [], set()
    for p in brutos:
        quando = p.get("publishedAt")
        if not quando or p.get("_id") in vistos:
            continue
        vistos.add(p.get("_id"))
        local = dt.datetime.fromisoformat(quando.replace("Z", "+00:00")).astimezone(fuso).date()
        if inicio <= local <= fim:
            p["_dia"] = local
            posts.append(p)

    rotulo = str(inicio) if inicio == fim else f"{inicio} a {fim}"
    if not posts:
        print(f"{rotulo} | {args.plataforma} | nenhum post publicado nesse período")
        return

    a = [p.get("analytics") or {} for p in posts]
    views = sum(num(x.get("views")) for x in a)
    alcance = sum(num(x.get("reach")) for x in a)
    seguidores = sum(num(x.get("follows")) for x in a)
    comentarios = sum(num(x.get("comments")) for x in a)
    melhor = max(posts, key=lambda p: num((p.get("analytics") or {}).get("views")))
    titulo = " ".join((melhor.get("content") or "").split())[:110]
    linha = (
        f"{rotulo} | {args.plataforma} | {len(posts)} posts | views {views} | alcance {alcance} | "
        f"comentários {comentarios} | seguidores vindos dos posts {seguidores}"
    )

    if inicio != fim:
        por_dia = {}
        for p in posts:
            d = por_dia.setdefault(p["_dia"], {"seg": 0, "views": 0, "posts": 0})
            an = p.get("analytics") or {}
            d["seg"] += num(an.get("follows"))
            d["views"] += num(an.get("views"))
            d["posts"] += 1
        dia_seg = max(por_dia, key=lambda d: por_dia[d]["seg"])
        dia_views = max(por_dia, key=lambda d: por_dia[d]["views"])
        linha += (
            f" | dias com post {len(por_dia)} | melhor dia em seguidores {dia_seg} ({por_dia[dia_seg]['seg']}) | "
            f"melhor dia em views {dia_views} ({por_dia[dia_views]['views']})"
        )

    linha += f" | melhor post: {num((melhor.get('analytics') or {}).get('views'))} views em {melhor['_dia']}, \"{titulo}\""
    print(linha)


if __name__ == "__main__":
    main()
