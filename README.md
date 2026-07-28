# 🔥 Canal Polêmico — FUT ZONA (@futzona2026)

Automação completa para geração de Shorts virais de futebol no YouTube.

## ⚡ Como funciona

```
Apps Script (3x/dia)
    ↓ chama GitHub API
GitHub Actions
    ↓
1. Groq AI (llama-3.3-70b) → pesquisa polêmica viral do futebol
2. icrawler + Bing → busca 2 imagens dos lados da polêmica
3. FFmpeg → baixa trecho 10s de música viral royalty-free
4. Pillow + FFmpeg → monta layout 9:16 branco com animações
5. YouTube Data API v3 → publica no @futzona2026
```

## 📱 Layout do vídeo (1080×1920 — 9:16)

```
┌─────────────────────────────────┐
│  [F]  FUT ZONA  @futzona2026    │  ← header preto/dourado
├─────────────────────────────────┤
│  ┌─────────────────────────┐    │
│  │ MESSI ROUBOU A BOLA DE  │    │  ← título polêmico
│  │ OURO DO NEYMAR EM 2015? │    │
│  └─────────────────────────┘    │
│  ┌──────────────┬────────────┐  │
│  │   IMG MESSI  │ IMG NEYMAR │  │  ← 2 imagens lado a lado
│  │              │     VS     │  │
│  │   [MESSI]    │  [NEYMAR]  │  │
│  └──────────────┴────────────┘  │
│  💬 "Com certeza o Messi..."    │  ← comentários animados
│  💬 "Neymar era melhor em..."   │
│  💬 "Polêmica demais! 🔥"       │
│                                 │
│       👇 COMENTE ABAIXO!        │  ← CTA pulsante
└─────────────────────────────────┘
```

**Animação (10s):**
- 0-1.5s: Header aparece
- 1.5-3s: Título surge com slide-up
- 3-5.5s: Imagens entram da esquerda/direita
- 5.5-9s: Comentários aparecem um a um
- 9-10s: Call-to-action pulsante

## 🔐 Secrets necessários no GitHub

| Secret | Descrição |
|--------|-----------|
| `GROQ_API_KEY` | Chave da API Groq (groq.com) |
| `BING_API_KEY` | Azure Cognitive Services — Bing Image Search (gratuito: 1000 req/mês) |
| `YOUTUBE_CLIENT_ID` | OAuth 2.0 Client ID do canal @futzona2026 |
| `YOUTUBE_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | Refresh Token do canal @futzona2026 |
| `WORKFLOW_TRIGGER_TOKEN` | GitHub PAT (para o Apps Script acionar o workflow) |

## 🚀 Setup inicial

### 1. Criar repositório público no GitHub
```bash
# No GitHub, crie um repositório público chamado "canal-polemico"
# Depois, no terminal:
git init
git add .
git commit -m "🔥 Initial commit — Canal Polêmico FUT ZONA"
git remote add origin https://github.com/SEU_USUARIO/canal-polemico.git
git push -u origin main
```

### 2. Configurar Secrets no GitHub
```
Repositório > Settings > Secrets and variables > Actions > New repository secret
```

### 3. Configurar o Apps Script
1. Acesse [script.google.com](https://script.google.com)
2. Crie um novo projeto
3. Cole o conteúdo de `appscript_trigger.gs`
4. Em **Configurações do projeto > Propriedades de script**, adicione:
   - `GITHUB_TOKEN` = seu PAT com permissão `repo`
   - `GITHUB_OWNER` = seu usuário GitHub
   - `GITHUB_REPO` = `canal-polemico`
5. Execute a função `configurarAcionadores()` **uma única vez** para criar os 3 acionadores diários

### 4. Testar manualmente
```
GitHub > Repositório > Actions > "Gerar Short Polêmico" > Run workflow
```

## 📁 Estrutura

```
CANAL POLEMICO/
├── .github/workflows/main.yml    # GitHub Actions
├── scripts/
│   ├── pipeline.py               # Orquestrador
│   ├── gerar_conteudo.py         # Groq AI
│   ├── buscar_imagens.py         # icrawler + Bing
│   ├── baixar_musica.py          # Música viral
│   ├── montar_video.py           # Layout + animações
│   └── upload_youtube.py         # YouTube API
├── data/polemica_usadas.json     # Tracking
├── requirements.txt
└── appscript_trigger.gs          # Apps Script
```

## 🎵 Músicas (royalty-free)
- Trap/hip-hop instrumentais de [chosic.com](https://www.chosic.com) (CC)
- Fallback: archive.org (domínio público)
- Recortadas para exatamente 10s com FFmpeg (fade-in/out)

---

Canal: **FUT ZONA** — [@futzona2026](https://youtube.com/@futzona2026)
