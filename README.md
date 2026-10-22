# JARVIS com Claude Code

Um assistente de voz que **executa** em vez de só conversar. Você segura a barra de espaço, fala, e ele usa o Claude Code dentro da sua pasta de trabalho (o seu segundo cérebro) pra consultar, anotar e agir nas suas ferramentas. Depois responde em voz alta.

```
você fala → transcrição → Claude Code na sua pasta (skills, memória, conectores) → resposta falada → esfera pulsa
```

- **Ouvido:** whisper rodando no seu computador (grátis) ou ElevenLabs Scribe.
- **Cérebro:** uma sessão do Claude Code que fica aberta e lembra da conversa.
- **Memória:** o `CLAUDE.md` e as notas da sua pasta.
- **Mãos:** tudo que o seu Claude Code já usa (conectores MCP, skills, scripts).
- **Boca:** ElevenLabs.
- **Rosto:** só uma esfera de pontos na tela, que reage à sua voz e à dele. Sem texto.
- **Jeito de JARVIS:** te chama de "Senhor", é sério com uma pitada de deboche e, quando precisa buscar alguma coisa, avisa na hora ("Um instante, Senhor.") e volta com a resposta.
- **Trava:** o que publica, envia mensagem ou apaga só acontece depois que você diz "confirma".

## O que você precisa

- [Claude Code](https://claude.com/claude-code) instalado e logado (comando `claude` no terminal).
- Python 3.9 ou mais novo. Não precisa instalar nenhuma biblioteca.
- Uma chave do [ElevenLabs](https://elevenlabs.io) (o plano grátis serve pra testar).
- Opcional: `ffmpeg` e o whisper local, pra transcrição grátis e rápida.

Testado no Mac. No Windows deve funcionar com Python e ffmpeg instalados, mas ainda não foi testado.

## Instalar

```bash
git clone <este repositório> jarvis
cd jarvis
cp .env.example .env
cp persona.example.md persona.md
```

1. No `.env`, coloque em `JARVIS_PASTA` a pasta que o Claude Code deve abrir (seu vault ou projeto) e em `ELEVENLABS_API_KEY` a sua chave.
2. Escolha a voz: na Voice Library do ElevenLabs, clique em **Add to my voices** e copie o ID pra `JARVIS_VOZ`.
3. No `persona.md`, preencha a parte **Sobre o dono**: quem é você, onde fica cada coisa na pasta e quais ferramentas estão ligadas. Quanto mais claro, mais rápido ele acerta.

### Whisper local (opcional, recomendado no Mac)

```bash
brew install whisper-cpp ffmpeg
mkdir -p ~/.cache/whisper-models
curl -L -o ~/.cache/whisper-models/ggml-large-v3-turbo.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
whisper-server -m ~/.cache/whisper-models/ggml-large-v3-turbo.bin --host 127.0.0.1 --port 8178 -l pt
```

Sem o whisper, ele usa o ElevenLabs Scribe sozinho (`JARVIS_TRANSCRICAO=auto`).

## Usar

```bash
python3 server.py
```

Abre no navegador em `http://localhost:8790`. Na primeira vez, libere o microfone.

| Tecla | O que faz |
|---|---|
| Segurar **espaço** (ou segurar o clique na esfera) | Fala com ele |
| **T** | Digita em vez de falar |
| **N** | Começa uma conversa nova |
| **H** | Mostra ou esconde os detalhes (o que você falou, a resposta escrita, o que ele está usando). Por padrão a tela fica só com a esfera |

## App de Mac (opcional)

Pra abrir o JARVIS como um aplicativo, com ícone próprio, pelo Spotlight ou pelo Dock:

```bash
bash app/montar.sh
```

Ele compila o `JARVIS.app` e instala em Aplicativos. O app liga o servidor sozinho, abre a esfera numa janela própria e desliga tudo quando você fecha (⌘Q). Na primeira vez que você segurar o espaço, o Mac pede permissão pro microfone. **⌘R** recarrega e **⌃⌘F** coloca em tela cheia.

Precisa das ferramentas de desenvolvedor da Apple (`xcode-select --install`) e do Pillow (`pip3 install pillow`) pra desenhar o ícone. O app guarda o caminho desta pasta: se mudar a pasta de lugar, rode o `montar.sh` de novo. O log do servidor fica em `.estado/app.log`.

## A trava

Antes de cada ação, o arquivo `hooks/trava.py` decide:

- **Passa direto:** ler arquivos, buscar, pesquisar, consultar conectores (tudo que lista, busca ou mostra).
- **Precisa de confirmação:** ação de conector que cria, envia, salva, apaga ou publica; escrever fora da pasta de trabalho; comandos de terminal que apagam, movem, publicam ou mandam dados pra fora.

Quando a trava barra, ele diz o que vai fazer e pergunta "Confirma?". Só depois de você responder "confirma", "pode" ou "sim" a ação passa, e só naquele pedido.

É uma lista de proteção, não uma caixa de areia. Leia o `hooks/trava.py` antes de ligar ferramentas novas e ajuste se precisar.

## Atalhos

Pergunta que se repete fica mais rápida com um script que já devolve a resposta pronta. A pasta `atalhos/` tem dois exemplos que usam a Zernio:

- `redes_resumo.py`: um dia (`--dia ontem`) ou um período inteiro (`--de 2026-10-01 --ate 2026-10-21`) no Instagram, TikTok ou YouTube, numa linha só (posts, views, alcance, comentários, seguidores, melhor post).
- `isca_resumo.py`: quantas pessoas comentaram a palavra e pediram a isca no direct, quantas receberam o link, quantas clicaram e qual isca puxou mais.

Atalho lento pode rodar quando o JARVIS abre: coloque em `JARVIS_AQUECER_ATALHOS` (ex.: `isca_resumo.py --dia ontem`) e o resultado de ontem fica guardado pra resposta sair na hora.

Crie os seus e conte no `persona.md` quando usar cada um. Diga também que período se pede numa chamada só: sem isso, o modelo tende a chamar o atalho dia por dia (uma pergunta de 21 dias levou 31 s assim e 3 s numa chamada).

## Velocidade

Quando a pergunta exige buscar alguma coisa, ele fala um aviso curto em 1 a 3 segundos e a resposta chega em 4 a 8. O aviso vem do próprio Claude; se ele for direto trabalhar sem avisar, o JARVIS toca uma frase pronta ("Deixa comigo, Senhor."), gravada quando o app abre. A resposta é falada assim que o texto fica pronto, sem esperar o Claude fechar a rodada. O que mais ajuda:

- `JARVIS_MODELO=sonnet` e `JARVIS_ESFORCO=low` (o padrão).
- Atalhos pras perguntas frequentes.
- Bloquear conectores que ele não usa em `JARVIS_BLOQUEAR_FERRAMENTAS` (menos coisa pra carregar).
- `JARVIS_MODELO_VOZ=eleven_flash_v2_5` começa a falar cerca de 1 segundo antes, com voz um pouco pior.
- `JARVIS_VELOCIDADE_VOZ=1.1` deixa a fala 10% mais rápida (vai de 0.7 a 1.2).

## Custos

- **Claude Code:** usa o seu plano. Cada pergunta é uma mensagem.
- **ElevenLabs:** cobra por caractere falado. Uma resposta curta tem uns 150 caracteres.
- **Whisper local:** grátis.

O plano pessoal do Claude é pro seu uso. Se for montar isso pra cliente pagante, use uma chave de API.

## Arquivos

```
server.py            servidor local: microfone, transcrição, Claude Code, voz
hooks/trava.py       a trava de confirmação
web/index.html       a tela da esfera
app/                 o app de Mac (montar.sh compila e instala)
persona.example.md   instruções do assistente (copie pra persona.md)
atalhos/             scripts de resposta rápida
.estado/             log de cada pedido, com os tempos (não vai pro git)
```

## Licença

MIT.
