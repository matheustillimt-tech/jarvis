#!/usr/bin/env bash
# Monta o JARVIS.app (Mac) e instala em Aplicativos.
# Uso: bash app/montar.sh            (instala em /Applications ou ~/Applications)
#      bash app/montar.sh ~/Desktop  (instala onde você quiser)
# Precisa: Xcode ou Command Line Tools (xcode-select --install) e Pillow (pip3 install pillow).
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/.." && pwd)"
DESTINO="${1:-/Applications}"
[ -w "$DESTINO" ] || DESTINO="$HOME/Applications"
mkdir -p "$DESTINO"

PORTA="$(grep -E '^JARVIS_PORTA=' "$RAIZ/.env" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)"
PORTA="${PORTA:-8790}"

ALVO="$DESTINO/JARVIS.app"
if [ -d "$ALVO" ]; then
  ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$ALVO/Contents/Info.plist" 2>/dev/null || true)"
  if [ "$ID" != "local.jarvis.claude-code" ]; then
    echo "Já existe outro app chamado JARVIS em $DESTINO ($ID). Não vou sobrescrever." >&2
    exit 1
  fi
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/JARVIS.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "Compilando..."
xcrun swiftc -O -swift-version 5 -target "$(uname -m)-apple-macos12.0" \
  -o "$APP/Contents/MacOS/JARVIS" "$AQUI/JarvisApp.swift" -framework Cocoa -framework WebKit

sed -e "s#__PASTA__#$RAIZ#" -e "s#__PORTA__#$PORTA#" "$AQUI/Info.plist" > "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"

echo "Desenhando o ícone..."
python3 "$AQUI/icone.py" "$TMP/icone.png" >/dev/null
ICONES="$TMP/AppIcon.iconset"
mkdir -p "$ICONES"
for t in 16 32 128 256 512; do
  sips -z $t $t "$TMP/icone.png" --out "$ICONES/icon_${t}x${t}.png" >/dev/null
  d=$((t * 2))
  sips -z $d $d "$TMP/icone.png" --out "$ICONES/icon_${t}x${t}@2x.png" >/dev/null
done
iconutil -c icns "$ICONES" -o "$APP/Contents/Resources/AppIcon.icns"

# Assinatura local (ad-hoc): o Mac lembra da permissão do microfone.
codesign --force --sign - "$APP" >/dev/null 2>&1

rm -rf "$ALVO"
cp -R "$APP" "$ALVO"
touch "$ALVO"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$ALVO" >/dev/null 2>&1 || true

echo "Pronto: $ALVO"
echo "Abra pelo Spotlight (⌘ espaço, digite JARVIS) ou arraste pro Dock."
