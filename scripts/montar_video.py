"""
montar_video.py
───────────────
Monta o Short polêmico de futebol em formato 9:16 (1080×1920px).

Layout (fundo branco):
  ┌─────────────────────────────────┐
  │                                 │
  │  [LOGO] FUT ZONA                │ ← topo: logo + nome + @futzona2026 (preto)
  │         @futzona2026            │
  │                                 │
  │  TÍTULO POLÊMICO EM             │ ← título médio, sem fundo
  │  LETRAS MAIÚSCULAS?             │
  │                                 │
  │  ┌──────────────┬──────────────┐│
  │  │  IMG LADO A  │  IMG LADO B  ││ ← 2 imagens lado a lado estáticas
  │  │   (540px)    │   (540px)    ││
  │  └──────────────┴──────────────┘│
  │                                 │
  └─────────────────────────────────┘
"""

import os
import math
import textwrap
import subprocess
import tempfile
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─────────────────────────────────────────────────────────────────────────────
# Dimensões e constantes
# ─────────────────────────────────────────────────────────────────────────────
W, H         = 1080, 1920       # 9:16
FPS          = 30
DURACAO_S    = 10
N_FRAMES     = FPS * DURACAO_S  # 300 frames

# Paleta de cores
COR_BG          = (255, 255, 255)    # fundo branco puro
COR_TITULO      = (15,  15,  15)     # quase preto
COR_NOME_CANAL  = (10,  10,  10)     # preto
COR_ARROBA      = (50,  50,  50)     # cinza escuro

# Posições-chave (y) no layout
Y_HEADER_H    = 180    
Y_TITULO_TOP  = 220    
Y_TITULO_BOT  = 480    
Y_IMG_TOP     = 510    
Y_IMG_BOT     = 1080   


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de fonte
# ─────────────────────────────────────────────────────────────────────────────
def _carregar_fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    """Carrega a melhor fonte disponível no sistema (Linux/Ubuntu)."""
    caminhos = [
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if negrito else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if negrito else ''}.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if negrito else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if negrito else "C:/Windows/Fonts/calibri.ttf",
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def _texto_centralizado(draw: ImageDraw.Draw, texto: str, y: int, font: ImageFont.FreeTypeFont,
                         cor: tuple, largura: int = W, sombra: bool = False):
    """Desenha texto horizontalmente centralizado com sombra opcional."""
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    x = (largura - tw) // 2
    if sombra:
        draw.text((x + 3, y + 3), texto, fill=(0, 0, 0, 60), font=font)
    draw.text((x, y), texto, fill=cor, font=font)


# ─────────────────────────────────────────────────────────────────────────────
# Montagem do frame base (estático)
# ─────────────────────────────────────────────────────────────────────────────
def _criar_frame_base(
    titulo: str,
    img_a: Image.Image,
    img_b: Image.Image,
    nome_a: str,
    nome_b: str,
) -> Image.Image:
    """Cria o frame estático completo (sem animação)."""
    canvas = Image.new("RGB", (W, H), COR_BG)
    draw = ImageDraw.Draw(canvas)

    # ── Header (Apenas o Avatar e os Textos, sem faixa preta) ────────────────
    avatar_r = 60
    avatar_cx, avatar_cy = 90, 110  # Movido mais para baixo

    # Tenta carregar a imagem do avatar
    avatar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "avatar.jpg")
    usou_imagem = False
    
    if os.path.exists(avatar_path):
        try:
            img_avatar = Image.open(avatar_path).convert("RGBA")
            # Corta quadrado perfeito no centro antes de redimensionar
            min_side = min(img_avatar.width, img_avatar.height)
            left = (img_avatar.width - min_side) // 2
            top = (img_avatar.height - min_side) // 2
            img_avatar = img_avatar.crop((left, top, left + min_side, top + min_side))
            img_avatar = img_avatar.resize((avatar_r * 2, avatar_r * 2), Image.LANCZOS)
            
            mask = Image.new("L", (avatar_r * 2, avatar_r * 2), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar_r * 2, avatar_r * 2), fill=255)
            
            canvas.paste(img_avatar, (avatar_cx - avatar_r, avatar_cy - avatar_r), mask)
            
            # Opcional: Borda dourada ao redor do avatar
            draw.ellipse(
                [avatar_cx - avatar_r, avatar_cy - avatar_r,
                 avatar_cx + avatar_r, avatar_cy + avatar_r],
                outline=(255, 200, 0),
                width=3,
            )
            usou_imagem = True
        except Exception as e:
            print(f"⚠️  Erro ao carregar avatar.jpg: {e}")

    if not usou_imagem:
        # Círculo do avatar (simulado com gradiente dourado) fallback
        draw.ellipse(
            [avatar_cx - avatar_r, avatar_cy - avatar_r,
             avatar_cx + avatar_r, avatar_cy + avatar_r],
            fill=(255, 200, 0),
            outline=(255, 220, 50),
            width=4,
        )
        # "F" de FUT ZONA no avatar
        font_avatar = _carregar_fonte(52, negrito=True)
        # Ajusta posição manualmente pois _texto_centralizado centraliza em W
        bbox_f = draw.textbbox((0, 0), "F", font=font_avatar)
        fw = bbox_f[2] - bbox_f[0]
        draw.text((avatar_cx - fw // 2, avatar_cy - 26), "F",
                  fill=(10, 10, 10), font=font_avatar)

    # Nome e @ do canal
    font_nome = _carregar_fonte(44, negrito=True)
    font_arroba = _carregar_fonte(32, negrito=False)
    draw.text((175, 65), "FUT ZONA", fill=COR_NOME_CANAL, font=font_nome)
    draw.text((175, 120), "@futzona2026", fill=COR_ARROBA, font=font_arroba)

    # ── Caixa do título (agora apenas texto limpo) ───────────────────────────
    margem_titulo = 40
    # Texto do título quebrado em múltiplas linhas (fontes menores que antes)
    titulo_upper = titulo.upper()
    font_titulo_g = _carregar_fonte(48, negrito=True)
    font_titulo_m = _carregar_fonte(40, negrito=True)
    font_titulo_p = _carregar_fonte(34, negrito=True)

    # Determina tamanho ideal da fonte baseado no comprimento
    if len(titulo_upper) <= 40:
        font_t = font_titulo_g
    elif len(titulo_upper) <= 70:
        font_t = font_titulo_m
    else:
        font_t = font_titulo_p

    max_chars = max(22, int((W - 2 * margem_titulo - 40) / (font_t.size * 0.55)))
    linhas = textwrap.wrap(titulo_upper, width=max_chars)

    # Centraliza as linhas verticalmente na área do título
    line_h = font_t.size + 12
    total_h = len(linhas) * line_h
    y_text = Y_TITULO_TOP + 10 + ((Y_TITULO_BOT - Y_TITULO_TOP - 20) - total_h) // 2

    for i, linha in enumerate(linhas[:4]):  # Máximo 4 linhas
        _texto_centralizado(draw, linha, y_text + i * line_h, font_t,
                            COR_TITULO, sombra=False)

    # ── Imagens lado a lado ───────────────────────────────────────────────────
    img_h = Y_IMG_BOT - Y_IMG_TOP  # 570px
    img_a_res = img_a.resize((W // 2, img_h), Image.LANCZOS)
    img_b_res = img_b.resize((W // 2, img_h), Image.LANCZOS)
    canvas.paste(img_a_res, (0, Y_IMG_TOP))
    canvas.paste(img_b_res, (W // 2, Y_IMG_TOP))

    # Linha divisória central entre as imagens
    draw.rectangle([(W // 2 - 3, Y_IMG_TOP), (W // 2 + 3, Y_IMG_BOT)],
                   fill=(255, 255, 255))

    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# Composição do vídeo com FFmpeg
# ─────────────────────────────────────────────────────────────────────────────
def _frames_para_video(frames_dir: str, musica_path: str | None,
                        output_path: str, fps: int = FPS):
    """Combina frames PNG em MP4 com trilha sonora via FFmpeg."""
    pattern = os.path.join(frames_dir, "frame_%04d.jpg")

    if musica_path and os.path.exists(musica_path):
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", pattern,
            "-i", musica_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "128k",
            "-af", "volume=0.35",   # música bem baixinha para não abafar
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", pattern,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]

    print(f"🎬 Codificando vídeo com FFmpeg...")
    resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if resultado.returncode != 0:
        print(f"❌ Erro FFmpeg:\n{resultado.stderr[-2000:]}")
        raise RuntimeError("FFmpeg falhou ao gerar o vídeo")
    print(f"✅ Vídeo gerado: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def montar_video(
    dados: dict,
    img_a: Image.Image,
    img_b: Image.Image,
    musica_path: str | None,
    output_dir: str,
) -> str:
    """
    Monta o vídeo polêmico completo de 10 segundos.
    Agora estático, sem comentários e com cores mais limpas!
    """
    os.makedirs(output_dir, exist_ok=True)

    titulo   = dados.get("titulo", "POLÊMICA DO FUTEBOL!").upper()
    nome_a   = dados.get("lado_a_nome", "LADO A")
    nome_b   = dados.get("lado_b_nome", "LADO B")

    print(f"\n🎬 Montando vídeo: '{titulo}'")
    print(f"   {N_FRAMES} frames × {FPS}fps = {DURACAO_S}s")

    # Cria frame base (estático)
    print("   🖼️  Criando frame base (estático)...")
    frame_base = _criar_frame_base(titulo, img_a, img_b, nome_a, nome_b)
    frame_arr = np.array(frame_base)

    # Pasta temporária para frames
    with tempfile.TemporaryDirectory() as frames_dir:
        print(f"   🎞️  Gerando {N_FRAMES} frames...")
        
        # Como não tem mais animação, basta salvar a mesma imagem 300 vezes.
        # Mas para economizar espaço e tempo de escrita do disco, o FFmpeg aceita uma única imagem em loop.
        # Porém, para manter a lógica simples, vamos apenas salvar a mesma imagem 300 vezes (é rápido em SSD).
        frame_base.save(os.path.join(frames_dir, "frame_base.jpg"), "JPEG", quality=88)
        
        for i in range(N_FRAMES):
            # Otimização: apenas cria hard links ou copia o arquivo se necessário
            # Ou então vamos apenas salvar todos igual
            shutil.copy(os.path.join(frames_dir, "frame_base.jpg"), 
                        os.path.join(frames_dir, f"frame_{i:04d}.jpg"))

        # Monta vídeo final
        output_path = os.path.join(output_dir, "video_final.mp4")
        _frames_para_video(frames_dir, musica_path, output_path)

    tamanho = os.path.getsize(output_path) / 1024 / 1024
    print(f"✅ Vídeo final: {output_path} ({tamanho:.1f} MB)")
    return output_path


if __name__ == "__main__":
    # Teste local
    from PIL import Image
    img_teste = Image.new("RGB", (520, 580), (100, 100, 200))
    dados_teste = {
        "titulo": "NEYMAR É MELHOR QUE RODRYGO?",
        "lado_a_nome": "Neymar",
        "lado_b_nome": "Rodrygo",
    }
    video = montar_video(dados_teste, img_teste, img_teste, None, "output")
    print(f"Teste: {video}")
