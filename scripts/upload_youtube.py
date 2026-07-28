"""
upload_youtube.py
─────────────────
Faz upload do Short polêmico para o canal FUT ZONA (@futzona2026)
via YouTube Data API v3 com publicação imediata.

Secrets necessários no GitHub:
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN  (do canal @futzona2026)
"""

import os
import re
import json

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def _obter_credenciais() -> Credentials:
    """Constrói credenciais OAuth 2.0 a partir dos secrets do ambiente."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    return creds


def _sanitizar_nome(titulo: str) -> str:
    nome = re.sub(r'[\\/*?:"<>|#]', '', titulo)
    nome = re.sub(r'\s+', '_', nome.strip())
    nome = re.sub(r'_{2,}', '_', nome)
    return nome[:80].rstrip('_') + ".mp4"


def upload_youtube(video_path: str, dados: dict) -> str:
    """
    Faz upload do Short para o YouTube com publicação imediata.

    video_path → caminho do MP4 (1080×1920)
    dados      → dict com titulo_youtube, descricao_yt, tags, lado_a_nome, lado_b_nome
    Retorna o ID do vídeo publicado.
    """
    creds   = _obter_credenciais()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    # ── Metadados ─────────────────────────────────────────────────────────────
    titulo = dados.get("titulo_youtube", dados.get("titulo", "Polêmica do Futebol! 🔥 #Shorts"))
    titulo = titulo[:100]

    descricao = dados.get("descricao_yt", "")[:450]
    descricao += (
        f"\n\n#FutZona #Futebol #Polemica #Shorts #futzona2026"
        f"\n\nCanal: @futzona2026"
    )
    descricao = descricao[:500]

    tags = dados.get("tags", [])
    tags_essenciais = [
        "futebol", "polemica", "Shorts", "futzona", "futzona2026",
        "futebol2026", "noticias futebol", "shorts futebol",
        dados.get("lado_a_nome", ""), dados.get("lado_b_nome", ""),
    ]
    tags = list(set(tags + [t for t in tags_essenciais if t]))[:30]

    # ── Renomeia o arquivo MP4 ────────────────────────────────────────────────
    if os.path.exists(video_path):
        novo_nome = _sanitizar_nome(titulo)
        novo_path = os.path.join(os.path.dirname(video_path), novo_nome)
        if novo_path != video_path:
            if os.path.exists(novo_path):
                os.remove(novo_path)
            os.rename(video_path, novo_path)
            video_path = novo_path
        print(f"   📁 Arquivo: {os.path.basename(video_path)}")

    # ── Body da requisição ────────────────────────────────────────────────────
    body = {
        "snippet": {
            "title":                titulo,
            "description":          descricao,
            "tags":                 tags,
            "categoryId":           "17",       # Sports — ideal para futebol
            "defaultLanguage":      "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    # ── Upload ────────────────────────────────────────────────────────────────
    print(f"\n📤 Enviando para YouTube (@futzona2026)...")
    print(f"   Título    : {titulo}")
    print(f"   Categoria : Sports (17)")
    print(f"   Tags      : {len(tags)} tags")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   Upload: {pct}%", end="\r")

    video_id = response.get("id", "")
    print(f"\n🎉 SHORT PUBLICADO!")
    print(f"   📱 https://www.youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    with open("output/conteudo.json", encoding="utf-8") as f:
        dados = json.load(f)
    upload_youtube("output/video_final.mp4", dados)
