#!/usr/bin/env python3
"""Quantas pessoas pediram a isca no direct do Instagram num dia (automações da Zernio).

Conta, em todas as automações de "comenta a palavra e recebe no direct":
quem comentou a palavra, quem recebeu o link e quem clicou. Também diz qual
isca puxou mais gente.

Uso:
  python3 atalhos/isca_resumo.py                 # ontem
  python3 atalhos/isca_resumo.py --dia hoje
  python3 atalhos/isca_resumo.py --dia 2026-10-21

Dia fechado fica guardado em .estado/isca/ (o JARVIS calcula "ontem" quando abre,
então a pergunta responde na hora). Precisa de ZERNIO_API_KEY (em ~/.zernio.env).
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

BASE = "https://zernio.com/api/v1"
RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / ".estado" / "isca"
FUSO = os.environ.get("JARVIS_FUSO", "America/Sao_Paulo")
POR_PAGINA = 200


def chave():
    if os.environ.get("ZERNIO_API_KEY"):
        return os.environ["ZERNIO_API_KEY"]
    arquivo = Path.home() / ".zernio.env"
    if arquivo.exists():
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            if linha.startswith("ZERNIO_API_KEY="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("Sem ZERNIO_API_KEY (coloque em ~/.zernio.env).")


CHAVE = chave()


def get(caminho, **query):
    url = BASE + caminho + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {CHAVE}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def quando(texto):
    return dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))


def registros_do_dia(automacao, inicio, fim):
    """Lê do mais novo pro mais antigo e para quando passa do começo do dia."""
    achados, pulo = [], 0
    while True:
        dados = get(f"/comment-automations/{automacao['id']}/logs", limit=POR_PAGINA, skip=pulo)
        logs = dados.get("logs", [])
        for log in logs:
            momento = quando(log["createdAt"])
            if inicio <= momento < fim:
                achados.append(log)
        if not logs or quando(logs[-1]["createdAt"]) < inicio or not (dados.get("pagination") or {}).get("hasMore"):
            return automacao, achados
        pulo += POR_PAGINA


def tema(nome):
    # "73MXU - Trilha IBM de IA grátis" -> "Trilha IBM de IA grátis"
    return nome.split(" - ", 1)[1].strip() if " - " in (nome or "") else (nome or "sem nome")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", default="ontem", help="hoje | ontem | AAAA-MM-DD")
    args = ap.parse_args()

    fuso = ZoneInfo(FUSO) if ZoneInfo else dt.timezone(dt.timedelta(hours=-3))
    hoje = dt.datetime.now(fuso).date()
    dia = {"hoje": hoje, "ontem": hoje - dt.timedelta(days=1)}.get(args.dia) or dt.date.fromisoformat(args.dia)
    guardado = CACHE / f"{dia}.txt"
    if dia < hoje and guardado.exists():
        print(guardado.read_text(encoding="utf-8").strip())
        return

    inicio = dt.datetime.combine(dia, dt.time(0), fuso)
    fim = inicio + dt.timedelta(days=1)
    automacoes = get("/comment-automations").get("automations", [])
    # Só olha quem já mandou alguma coisa, existia no dia e teve movimento desde então.
    candidatas = [a for a in automacoes
                  if (a.get("stats") or {}).get("triggered")
                  and quando(a["createdAt"]) < fim
                  and quando(a.get("updatedAt") or a["createdAt"]) >= inicio]

    with ThreadPoolExecutor(max_workers=12) as grupo:
        resultados = list(grupo.map(lambda a: registros_do_dia(a, inicio, fim), candidatas))

    pessoas, recebeu, clicou = set(), set(), set()
    por_isca = []
    for automacao, logs in resultados:
        if not logs:
            continue
        quem = {l.get("commenterId") or l.get("id") for l in logs}
        pessoas |= quem
        recebeu |= {l.get("commenterId") or l.get("id") for l in logs if l.get("status") == "sent"}
        clicou |= {l.get("commenterId") or l.get("id") for l in logs if (l.get("clickCount") or 0) > 0}
        por_isca.append((len(quem), tema(automacao.get("name"))))

    if not pessoas:
        linha = f"{dia} | isca no direct do Instagram | ninguém comentou palavra de isca nesse dia"
    else:
        por_isca.sort(reverse=True)
        top = "; ".join(f"{n} em \"{t}\"" for n, t in por_isca[:3])
        linha = (f"{dia} | isca no direct do Instagram | {len(pessoas)} pessoas comentaram a palavra e pediram a isca | "
                 f"{len(recebeu)} receberam o link no direct | {len(clicou)} clicaram no link | "
                 f"{len(por_isca)} iscas com pedido | mais pedidas: {top}")
    if dia < hoje:
        CACHE.mkdir(parents=True, exist_ok=True)
        guardado.write_text(linha + "\n", encoding="utf-8")
    print(linha)


if __name__ == "__main__":
    main()
