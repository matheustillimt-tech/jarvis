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
| Segurar **espaço** | Fala com ele. Apertar de novo enquanto ele fala ou pensa **interrompe** na hora |
| **T** | Digita em vez de falar |
| **N** | Começa uma conversa nova |
| **H** | Mostra ou esconde os detalhes (o que você falou, a resposta escrita, o que ele está usando). Por padrão a tela fica só com a esfera |

Clique na janela não liga o microfone: só a barra de espaço. A gravação para sozinha em 30 segundos e também quando você troca de janela. Se você apertar o espaço com ele no meio de uma resposta, ele cala e cancela o que estava fazendo, sem perder o fio da conversa.

### Configurações (a engrenagem)

Mexa o mouse e aparece uma engrenagem no canto de cima. Nela você escolhe a voz do JARVIS (8 vozes em português, 4 masculinas e 4 femininas, com botão pra ouvir cada uma) e a velocidade da fala. Vale a partir da próxima resposta e fica salvo em `.estado/preferencias.json`, que vale mais que o `.env`.

A lista de vozes fica em `vozes.json`: troque ou adicione qualquer voz da Voice Library do ElevenLabs (o ID e uma descrição curta). Algumas vozes da biblioteca só funcionam depois de clicar em **Add to my voices** no site.

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

Pergunta que se repete fica mais rápida com um script que já devolve a resposta pronta, numa linha só. A pasta `atalhos/` tem três exemplos:

- `mercado.py`: dólar, euro, bitcoin, Ibovespa, S&P 500 e Nasdaq com a variação do dia (fontes grátis, sem chave).
- `redes_resumo.py` (precisa da Zernio): Instagram, TikTok ou YouTube num dia (`--dia ontem`), na semana (`--ultimos 7`) ou num período (`--de 2026-10-01 --ate 2026-10-21`): posts, views, alcance, comentários, seguidores, o melhor post e o mais comentado.
- `isca_resumo.py` (precisa da Zernio): quantas pessoas comentaram a palavra e pediram a isca no direct, quantas receberam o link, quantas clicaram e qual isca puxou mais.

Crie os seus e conte no `persona.md` quando usar cada um. Diga também que período se pede numa chamada só: sem isso, o modelo tende a chamar o atalho dia por dia (uma pergunta de 21 dias levou 31 s assim e 3 s numa chamada).

Atalho lento pode rodar quando o JARVIS abre: coloque em `JARVIS_AQUECER_ATALHOS` (ex.: `isca_resumo.py --dia ontem`) e o resultado de ontem fica guardado.

### Pré-busca (gatilhos.json)

Pra pergunta que você já sabe que vai fazer, o JARVIS nem precisa decidir rodar o atalho: em `gatilhos.json`, cada palavra aponta pra um atalho ("dólar", "bolsa" → `mercado.py`; "posts", "comentários" → `redes_resumo.py`, com o período que você falou: hoje, ontem, semana ou mês). O servidor roda o atalho na hora e manda o dado junto com a pergunta, e o Claude só precisa responder. Corta a ida e volta da ferramenta.

## Velocidade

Pergunta simples sai em 1 a 2 segundos. Pergunta que precisa de dado sai em 3 a 6. Se uma busca demorar, ele avisa ("Um instante, Senhor.") e volta com o resultado; pergunta simples não tem aviso. A resposta é falada assim que o texto fica pronto, sem esperar o Claude fechar a rodada. O que mais ajuda:

- **Contexto enxuto (`JARVIS_CONTEXTO=leve`, o padrão).** O Claude abre numa pasta vazia com a sua pasta anexada, então não carrega o CLAUDE.md e a memória dela a cada pergunta. Medido: resposta simples em ~1 s, contra 2 a 6 s abrindo direto num vault grande. Use `completo` só com pasta pequena (como uma pasta só pra gravar um vídeo, com um CLAUDE.md curto dizendo o que ele vai responder).
- Atalhos e pré-busca pras perguntas frequentes.
- `JARVIS_MODELO=sonnet` e `JARVIS_ESFORCO=low` (o padrão).
- Bloquear conectores que ele não usa em `JARVIS_BLOQUEAR_FERRAMENTAS`.
- `JARVIS_MODELO_VOZ=eleven_flash_v2_5` começa a falar cerca de 1 segundo antes, com voz um pouco pior.
- `JARVIS_VELOCIDADE_VOZ=1.1` deixa a fala 10% mais rápida (vai de 0.7 a 1.2), ou ajuste na engrenagem.
- `JARVIS_PERSONA` escolhe outro arquivo de persona (ex.: um modo só pra gravar vídeo).

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
vozes.json           as vozes que aparecem na engrenagem
gatilhos.json        palavras que já disparam um atalho (pré-busca)
atalhos/             scripts de resposta rápida
.estado/             log de cada pedido, com os tempos (não vai pro git)
```

## Licença

MIT.
