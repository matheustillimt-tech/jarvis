#!/usr/bin/env python3
"""Como está o mercado agora, numa linha só: dólar, euro, bitcoin, Ibovespa, S&P 500 e Nasdaq.

Uso:  python3 atalhos/mercado.py

Fontes grátis, sem chave: AwesomeAPI (moedas) e Yahoo Finance (bolsas).
A variação é em relação ao fechamento anterior.
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

MOEDAS = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-BRL"
BOLSAS = {"Ibovespa": "%5EBVSP", "S&P 500": "%5EGSPC", "Nasdaq": "%5EIXIC"}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


def br(numero, casas=2):
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor):
    return ("+" if valor >= 0 else "") + br(valor) + "%"


def moedas():
    d = baixar(MOEDAS)
    saida = []
    for chave, nome, casas in (("USDBRL", "dólar", 2), ("EURBRL", "euro", 2), ("BTCBRL", "bitcoin", 0)):
        if chave in d:
            item = d[chave]
            saida.append(f"{nome} R$ {br(float(item['bid']), casas)} ({pct(float(item['pctChange']))} hoje)")
    hora = d.get("USDBRL", {}).get("create_date", "")[11:16]
    return saida, hora


def bolsa(nome, simbolo):
    meta = baixar(f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}?range=1d&interval=1d")["chart"]["result"][0]["meta"]
    atual = meta.get("regularMarketPrice")
    anterior = meta.get("chartPreviousClose") or meta.get("previousClose")
    if not atual or not anterior:
        return None
    casas = 0 if nome == "Ibovespa" else 2
    return f"{nome} {br(atual, casas)} pontos ({pct((atual / anterior - 1) * 100)} no dia)"


def main():
    partes, hora = [], ""
    with ThreadPoolExecutor(max_workers=4) as grupo:
        futuro_moedas = grupo.submit(moedas)
        futuros = [grupo.submit(bolsa, n, s) for n, s in BOLSAS.items()]
        try:
            m, hora = futuro_moedas.result()
            partes += m
        except Exception as erro:
            partes.append(f"moedas indisponíveis agora ({erro.__class__.__name__})")
        for f in futuros:
            try:
                r = f.result()
                if r:
                    partes.append(r)
            except Exception:
                pass
    if not partes:
        sys.exit("Não consegui buscar o mercado agora.")
    print(" | ".join(partes) + (f" | cotação das {hora}" if hora else ""))


if __name__ == "__main__":
    main()
