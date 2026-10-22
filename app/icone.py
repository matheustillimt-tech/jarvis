#!/usr/bin/env python3
"""Desenha o ícone do JARVIS.app (esfera de pontos branca num quadrado preto).

Uso: python3 app/icone.py saida.png   (precisa do Pillow: pip3 install pillow)
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter

T = 2048                      # desenha grande e reduz no fim (bordas lisas)
MARGEM = 200                  # grade de ícone do macOS: 824 de 1024
LADO = T - 2 * MARGEM
RAIO_CANTO = int(LADO * 0.2237)


def mascara_quadrado():
    m = Image.new("L", (T, T), 0)
    ImageDraw.Draw(m).rounded_rectangle([MARGEM, MARGEM, T - MARGEM, T - MARGEM], RAIO_CANTO, fill=255)
    return m


def fundo():
    # gradiente radial: cinza quase preto no centro, preto nas bordas
    g = Image.radial_gradient("L").resize((T, T), Image.LANCZOS)  # 0 no centro, 255 na borda
    cor = Image.new("RGBA", (T, T))
    claro, escuro = (30, 30, 33), (0, 0, 0)
    px = g.load()
    saida = cor.load()
    for y in range(T):
        for x in range(T):
            t = min(1.0, px[x, y] / 200)
            saida[x, y] = tuple(int(claro[i] + (escuro[i] - claro[i]) * t) for i in range(3)) + (255,)
    return cor


def brilho(cx, cy, raio, intensidade):
    camada = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for i in range(60, 0, -1):
        r = raio * i / 60
        a = int(intensidade * (1 - i / 60) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, a))
    return camada.filter(ImageFilter.GaussianBlur(raio * 0.15))


def esfera(cx, cy, R, n=2600):
    pontos = []
    rot, inc = 0.6, 0.42
    cr, sr, ci, si = math.cos(rot), math.sin(rot), math.cos(inc), math.sin(inc)
    for i in range(n):
        y = 1 - (i / (n - 1)) * 2
        r = math.sqrt(1 - y * y)
        th = i * 2.399963229728653
        x, z = math.cos(th) * r, math.sin(th) * r
        x1, z1 = x * cr + z * sr, -x * sr + z * cr
        y1, z2 = y * ci - z1 * si, y * si + z1 * ci
        prof = (z2 + 1) / 2
        esc = 1 / (1 - z2 * 0.16)  # o lado da frente fica um pouco maior
        pontos.append((prof, cx + x1 * R * esc * 0.9, cy + y1 * R * esc * 0.9))
    camada = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for prof, px, py in sorted(pontos):
        raio = 2.0 + 5.2 * prof
        alfa = int(255 * max(0.06, min(1.0, 0.04 + 0.96 * prof ** 1.8)))
        d.ellipse([px - raio, py - raio, px + raio, py + raio], fill=(255, 255, 255, alfa))
    return camada


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else "icone.png"
    mascara = mascara_quadrado()

    sombra = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 120), (0, 28), mascara)
    sombra = sombra.filter(ImageFilter.GaussianBlur(36))

    cx = cy = T // 2
    conteudo = fundo()
    conteudo = Image.alpha_composite(conteudo, brilho(cx, cy, 760, 95))
    conteudo = Image.alpha_composite(conteudo, esfera(cx, cy, 500))

    borda = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    ImageDraw.Draw(borda).rounded_rectangle(
        [MARGEM + 2, MARGEM + 2, T - MARGEM - 2, T - MARGEM - 2], RAIO_CANTO, outline=(255, 255, 255, 34), width=4)
    conteudo = Image.alpha_composite(conteudo, borda)

    icone = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    icone = Image.alpha_composite(icone, sombra)
    icone.paste(conteudo, (0, 0), mascara)
    icone.resize((1024, 1024), Image.LANCZOS).save(saida)
    print(saida)


if __name__ == "__main__":
    main()
