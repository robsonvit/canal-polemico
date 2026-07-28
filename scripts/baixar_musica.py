"""
baixar_musica.py
────────────────
Baixa um trecho de 10s de música viral usando yt-dlp para pesquisar no SoundCloud (scsearch) 
que é mais imune a bloqueios de bots do que o YouTube. Fallback para arquivo direto garantido.
"""

import os
import subprocess
import tempfile
import random
import requests

DURACAO_VIDEO = 10  # segundos

TERMOS_BUSCA = [
    "instrumental trap beat short no copyright",
    "phonk beat no copyright short",
    "hip hop instrumental fast no copyright",
    "suspense beat no copyright",
]

# MP3 garantido para caso TODAS as ferramentas falhem, não deixando o vídeo mudo
URL_FALLBACK = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

def _tem_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False

def baixar_musica(output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    destino_final = os.path.join(output_dir, "musica_bg.mp3")

    if os.path.exists(destino_final) and os.path.getsize(destino_final) > 10000:
        print(f"🎵 Música já disponível: {destino_final}")
        return destino_final

    print(f"🎵 Buscando música viral no SoundCloud usando yt-dlp...")
    termo = random.choice(TERMOS_BUSCA)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_bruto = os.path.join(tmp_dir, "bruto.mp3")
        
        # Tentativa 1: SoundCloud via yt-dlp
        cmd_ytdlp = [
            "yt-dlp",
            f"scsearch1:{termo}",
            "-x",
            "--audio-format", "mp3",
            "-o", tmp_bruto,
            "--max-downloads", "1"
        ]

        try:
            print(f"   > yt-dlp scsearch: {termo}")
            subprocess.run(cmd_ytdlp, capture_output=True, check=True)
        except Exception as e:
            print(f"   ⚠️  Erro yt-dlp: {e}")
            
        # Tentativa 2: Fallback MP3 garantido (URL Direta)
        if not os.path.exists(tmp_bruto):
            print("   ⚠️  Tentando Fallback Garantido de Áudio (URL direta)...")
            try:
                r = requests.get(URL_FALLBACK, stream=True, timeout=15)
                r.raise_for_status()
                with open(tmp_bruto, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            except Exception as e2:
                print(f"   ⚠️  Erro Fallback: {e2}")
                return None
            
        print("   ✅ Áudio baixado, recortando para 10s...")
        if _tem_ffmpeg():
            cmd_ffmpeg = [
                "ffmpeg", "-y",
                "-ss", "10",  # Pula os primeiros 10s
                "-i", tmp_bruto,
                "-t", str(DURACAO_VIDEO),
                "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={DURACAO_VIDEO-0.5}:d=0.5",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                destino_final,
            ]
            try:
                subprocess.run(cmd_ffmpeg, capture_output=True, check=True)
                print(f"   ✅ Áudio final pronto: {destino_final}")
                return destino_final
            except Exception:
                import shutil
                shutil.copy(tmp_bruto, destino_final)
                return destino_final
        else:
            import shutil
            shutil.copy(tmp_bruto, destino_final)
            return destino_final

if __name__ == "__main__":
    resultado = baixar_musica("output")
    print(f"Música: {resultado}")
