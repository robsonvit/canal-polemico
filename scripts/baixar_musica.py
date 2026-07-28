"""
baixar_musica.py
────────────────
Baixa um trecho de 10s de música viral/em alta (trap, funk, hip-hop)
royalty-free para usar como trilha dos vídeos polêmicos de futebol.

Fontes:
  - Free Music Archive (FMA) — Creative Commons
  - ccMixter — Creative Commons Attribution
  - archive.org — domínio público / CC

O trecho é cortado para exatamente 10s com fade-in e fade-out usando FFmpeg.
"""

import os
import random
import subprocess
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Biblioteca de músicas royalty-free com estilo viral (trap/hip-hop/funk)
# ─────────────────────────────────────────────────────────────────────────────
MUSICAS_VIRAIS = [
    # Trap / Hip-hop instrumental — estilo vídeos virais de futebol
    {
        "nome": "Trap Beat 1",
        "url": "https://www.chosic.com/wp-content/uploads/2021/09/Aggressive-Trap-Music.mp3",
        "inicio": 10,
    },
    {
        "nome": "Hip Hop Energy",
        "url": "https://www.chosic.com/wp-content/uploads/2023/05/Hip-Hop-Short-Version-Sports.mp3",
        "inicio": 5,
    },
    {
        "nome": "Sport Trap",
        "url": "https://www.chosic.com/wp-content/uploads/2023/04/Sport-Trap-Beat.mp3",
        "inicio": 8,
    },
    {
        "nome": "Trap Suspense",
        "url": "https://archive.org/download/trap-beat-loop-pack/trap_beat_1.mp3",
        "inicio": 0,
    },
    {
        "nome": "Epic Football",
        "url": "https://www.chosic.com/wp-content/uploads/2022/09/extreme-sport-logo.mp3",
        "inicio": 0,
    },
    # Músicas épicas/dramáticas para polêmica
    {
        "nome": "Drama Sting",
        "url": "https://www.chosic.com/wp-content/uploads/2022/02/Tense-Cinematic.mp3",
        "inicio": 5,
    },
    {
        "nome": "Action Beat",
        "url": "https://www.chosic.com/wp-content/uploads/2022/12/Action-Sport-Intro.mp3",
        "inicio": 0,
    },
]

# Fallback garantido (sempre disponível — Archive.org domínio público)
FALLBACKS = [
    "https://archive.org/download/78_shake-rattle-and-roll_bill-haley-and-his-comets-charles-calhoun_gbia0001502a/01%20-%20Shake%2C%20Rattle%20and%20Roll%20-%20Bill%20Haley%20and%20His%20Comets.mp3",
    "https://upload.wikimedia.org/wikipedia/commons/3/3b/Johann_Sebastian_Bach_-_Toccata_and_Fugue_in_D_Minor.ogg",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.chosic.com/",
}

DURACAO_VIDEO = 10  # segundos


def _tem_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def _baixar_arquivo(url: str, destino: str) -> bool:
    """Tenta baixar um arquivo. Retorna True se sucesso."""
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        tamanho = os.path.getsize(destino)
        if tamanho < 5000:  # Menos de 5KB = provavelmente erro HTML
            os.remove(destino)
            return False
        return True
    except Exception as e:
        print(f"   ⚠️  Falha ao baixar: {e}")
        if os.path.exists(destino):
            os.remove(destino)
        return False


def _recortar_audio(entrada: str, saida: str, inicio: int = 0, duracao: int = 10) -> bool:
    """Recorta o áudio para exatamente `duracao` segundos com fade-in e fade-out."""
    if not _tem_ffmpeg():
        print("   ⚠️  FFmpeg não encontrado, usando áudio sem recorte")
        import shutil
        shutil.copy(entrada, saida)
        return True

    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(inicio),
            "-i", entrada,
            "-t", str(duracao),
            "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={duracao-0.5}:d=0.5",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            saida,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=60)
        print(f"   ✅ Áudio recortado: {duracao}s com fade in/out")
        return True
    except Exception as e:
        print(f"   ⚠️  Erro ao recortar: {e}")
        import shutil
        shutil.copy(entrada, saida)
        return True


def baixar_musica(output_dir: str = "output") -> str:
    """
    Baixa e prepara um trecho de 10s de música viral/trap para o vídeo polêmico.

    Retorna o caminho do arquivo MP3 recortado pronto para uso.
    """
    os.makedirs(output_dir, exist_ok=True)
    destino_final = os.path.join(output_dir, "musica_bg.mp3")

    # Se já existe do run anterior, usa sem baixar novamente
    if os.path.exists(destino_final) and os.path.getsize(destino_final) > 10000:
        print(f"🎵 Música já disponível: {destino_final}")
        return destino_final

    tmp_bruto = os.path.join(output_dir, "musica_bruta.mp3")

    # Embaralha as músicas para variar a cada execução
    musicas_shuffled = MUSICAS_VIRAIS.copy()
    random.shuffle(musicas_shuffled)

    for musica in musicas_shuffled:
        print(f"🎵 Tentando baixar: '{musica['nome']}'...")
        if _baixar_arquivo(musica["url"], tmp_bruto):
            _recortar_audio(tmp_bruto, destino_final, musica.get("inicio", 0), DURACAO_VIDEO)
            if os.path.exists(destino_final):
                os.remove(tmp_bruto) if os.path.exists(tmp_bruto) else None
                print(f"✅ Música viral pronta: {destino_final}")
                return destino_final

    # Fallback
    print("⚠️  Tentando fallbacks...")
    for url_fallback in FALLBACKS:
        print(f"🎵 Fallback: {url_fallback[:60]}...")
        if _baixar_arquivo(url_fallback, tmp_bruto):
            _recortar_audio(tmp_bruto, destino_final, 0, DURACAO_VIDEO)
            if os.path.exists(destino_final):
                os.remove(tmp_bruto) if os.path.exists(tmp_bruto) else None
                return destino_final

    print("⚠️  Nenhuma música disponível. Prosseguindo sem trilha sonora.")
    return None


if __name__ == "__main__":
    resultado = baixar_musica("output")
    print(f"Música: {resultado}")
