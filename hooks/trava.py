#!/usr/bin/env python3
"""Trava do JARVIS: roda antes de cada ferramenta que o Claude usa.

Ler, buscar e consultar passa direto. Publicar, enviar mensagem, apagar,
mexer em cliente ou escrever fora da pasta de trabalho só passa se você
confirmou por voz (o servidor cria o arquivo .estado/confirmado durante
aquele pedido). Sem confirmação, a ação é barrada e o Claude é orientado a
perguntar "Confirma?".

Não é uma caixa de areia: é uma lista de proteção. Leia antes de liberar
ferramentas novas.
"""
import json
import os
import re
import sys
from pathlib import Path

LIVRES = {
    "Read", "Glob", "Grep", "LS", "WebSearch", "WebFetch", "TodoWrite", "Skill", "Task", "Agent",
    "ToolSearch", "ListMcpResourcesTool", "ReadMcpResourceTool", "BashOutput", "KillShell",
}

# Palavras no nome da ferramenta de um conector (MCP)
MCP_ARRISCADO = re.compile(
    r"(send|enviar|envio|criar|create|salvar|save|update|atualizar|anotar|delete|excluir|trash|apagar|"
    r"publicar|publish|tirar_do_ar|arquivar|cancelar|editar|edit|upload|move|mover|share|reply|forward|"
    r"draft|label|spam|respond|transfer|provision|set_|add_|remove|apply|dub|duplicate|generate|reencode|"
    r"schedule|rename|enable|disable|finish|start_|onboarding|import|write|copy|merge|comment|resolve)",
    re.I,
)
MCP_LEITURA = re.compile(
    r"(list|listar|get|ver|buscar|search|read|ficha|metricas|quem_sou|quadro|assinantes|"
    r"suggest|count|status|show|preview|who_am_i|find|info|help|query|fetch|download_file_content)",
    re.I,
)

# Comandos de terminal que mudam coisas fora (ou apagam)
BASH_ARRISCADO = [
    r"\brm\b", r"\bmv\b", r"\bsudo\b", r"\bkill(all)?\b", r"\bpkill\b", r"\bchmod\b", r"\bchown\b",
    r"\bgit\s+(push|reset|clean|checkout|rebase|commit|merge)\b",
    r"\bcurl\b.*\s-X\s*(POST|PUT|PATCH|DELETE)\b", r"\bcurl\b.*\s(-d|--data\S*|-F|--form|-T|--upload-file)\b",
    r"\bnpm\s+publish\b", r"\bvercel\b", r"\bsupabase\b.*\b(delete|reset|push)\b",
    r"\bgh\s+\w+\s+(create|delete|merge|edit|close|comment)\b", r"\bosascript\b", r"\bdd\b", r"\btee\b",
]
# Zernio (redes sociais): só consulta passa direto
ZERNIO_LEITURA = {"check", "status", "accounts", "yt-playlists", "tiktok-info", "li-orgs", "posts",
                  "post-get", "autos", "auto-get", "auto-logs"}


def barrar(oque):
    sys.stderr.write(
        f"TRAVA DO JARVIS: {oque} precisa da confirmação do dono por voz. Não execute agora e não tente "
        "outro caminho pra fazer a mesma coisa. Responda em uma frase dizendo exatamente o que vai fazer "
        "e termine com 'Confirma?'."
    )
    sys.exit(2)


def redireciona_pra_arquivo(cmd):
    for alvo in re.findall(r"(?<![0-9&<])>{1,2}\s*([^\s;&|]+)", cmd):
        if alvo not in ("/dev/null", "&1", "&2"):
            return True
    return False


def zernio_arriscado(cmd):
    m = re.search(r"zernio\.py\s+(\S+)(?:\s+(\S+))?", cmd)
    if not m:
        return False
    sub, metodo = m.group(1), (m.group(2) or "").upper()
    if sub == "api":
        return metodo != "GET"
    return sub not in ZERNIO_LEITURA


def dentro_da_pasta(caminho, pasta):
    if not caminho or not pasta:
        return False
    real = os.path.realpath(os.path.expanduser(caminho))
    return real == pasta or real.startswith(pasta + os.sep)


def main():
    try:
        dados = json.load(sys.stdin)
    except ValueError:
        return
    nome = dados.get("tool_name", "")
    entrada = dados.get("tool_input") or {}
    estado = Path(os.environ.get("JARVIS_ESTADO", ""))
    pasta = os.path.realpath(os.environ.get("JARVIS_PASTA", "")) if os.environ.get("JARVIS_PASTA") else ""
    confirmado = bool(os.environ.get("JARVIS_ESTADO")) and (estado / "confirmado").exists()

    if nome in LIVRES or confirmado:
        return

    if nome.startswith("mcp__"):
        acao = nome.split("__")[-1]
        if MCP_ARRISCADO.search(acao) or not MCP_LEITURA.search(acao):
            barrar(f"a ação '{acao}'")
        return

    if nome in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        caminho = entrada.get("file_path") or entrada.get("notebook_path") or ""
        if not dentro_da_pasta(caminho, pasta):
            barrar("escrever fora da pasta de trabalho")
        return

    if nome == "Bash":
        cmd = entrada.get("command", "")
        if zernio_arriscado(cmd):
            barrar("publicar, agendar ou mudar algo nas redes sociais")
        if any(re.search(p, cmd) for p in BASH_ARRISCADO) or redireciona_pra_arquivo(cmd):
            barrar("esse comando de terminal")
        return


if __name__ == "__main__":
    main()
