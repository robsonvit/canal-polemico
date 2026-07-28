"""
montar_video.py
───────────────
Monta o Short polêmico de futebol em formato 9:16 (1080×1920px).

Layout (fundo branco):
  ┌─────────────────────────────────┐
  │  [LOGO] FUT ZONA                │ ← topo: logo + nome + @futzona2026
  │         @futzona2026            │
  │                                 │
  │  ╔═══════════════════════════╗  │
  │  ║  TÍTULO POLÊMICO EM       ║  │ ← título grande em negrito
  │  ║  LETRAS MAIÚSCULAS?       ║  │
  │  ╚═══════════════════════════╝  │
  │                                 │
  │  ┌──────────────┬──────────────┐│
  │  │  IMG LADO A  │  IMG LADO B  ││ ← 2 imagens lado a lado
  │  │   (540px)    │   (540px)    ││
  │  └──────────────┴──────────────┘│
  │                                 │
  │  💬 Comentário 1 (aparece)      │ ← comentários animados
  │  💬 Comentário 2 (aparece)      │
  │  💬 Comentário 3 (aparece)      │
  │                                 │
  │  👇 COMENTE ABAIXO!             │ ← call-to-action final
  └─────────────────────────────────┘

Animação (~10s):
  0.0-1.5s  → header (logo + nome) aparece com fade
  1.5-3.0s  → título aparece com slide-up
  3.0-5.5s  → imagens aparecem com slide-in da esquerda/direita
  5.5-9.0s  → 3 comentários aparecem um a um (1.17s cada)
  9.0-10.0s → call-to-action pulsante
"""

import os
import math
import textwrap
import subprocess
import tempfile
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
COR_HEADER_BG   = (10,  10,  10)    # faixa preta no topo
COR_NOME_CANAL  = (255, 255, 255)    # branco no header escuro
COR_ARROBA      = (255, 200, 0)      # dourado para @futzona2026
COR_CAIXA_TITULO= (240, 240, 240)   # cinza claro para caixa do título
COR_BORDA_TITULO= (220, 50,  50)    # vermelho para borda da caixa
COR_COMENTARIO  = (30,  30,  30)    # texto dos comentários
COR_BALAO       = (248, 248, 248)   # balão de comentário
COR_CTA         = (220, 50,  50)    # call-to-action vermelho

# Posições-chave (y) no layout
Y_HEADER_H    = 180    # altura da faixa do header
Y_TITULO_TOP  = 220    # topo da caixa de título
Y_TITULO_BOT  = 480    # fundo da caixa de título
Y_IMG_TOP     = 510    # topo das imagens
Y_IMG_BOT     = 1080   # fundo das imagens (570px de altura)
Y_COMENT_TOP  = 1110   # início dos comentários
Y_CTA         = 1800   # call-to-action


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de fonte
# ─────────────────────────────────────────────────────────────────────────────
def _carregar_fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    """Carrega a melhor fonte disponível no sistema (Linux/Ubuntu)."""
    caminhos = [
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if negrito else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if negrito else ''}.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if negrito else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Windows (caso rode localmente)
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

    # ── Header (faixa preta no topo) ─────────────────────────────────────────
    draw.rectangle([(0, 0), (W, Y_HEADER_H)], fill=COR_HEADER_BG)

    # Círculo do avatar (simulado com gradiente dourado)
    avatar_r = 60
    avatar_cx, avatar_cy = 90, 90
    draw.ellipse(
        [avatar_cx - avatar_r, avatar_cy - avatar_r,
         avatar_cx + avatar_r, avatar_cy + avatar_r],
        fill=(255, 200, 0),
        outline=(255, 220, 50),
        width=4,
    )
    # "F" de FUT ZONA no avatar
    font_avatar = _carregar_fonte(52, negrito=True)
    _texto_centralizado(draw, "F", avatar_cy - 30, font_avatar,
                        (10, 10, 10), largura=W)
    # Ajusta posição manualmente pois _texto_centralizado centraliza em W
    bbox_f = draw.textbbox((0, 0), "F", font=font_avatar)
    fw = bbox_f[2] - bbox_f[0]
    draw.text((avatar_cx - fw // 2, avatar_cy - 26), "F",
              fill=(10, 10, 10), font=font_avatar)

    # Nome e @ do canal
    font_nome = _carregar_fonte(44, negrito=True)
    font_arroba = _carregar_fonte(32, negrito=False)
    draw.text((175, 38), "FUT ZONA", fill=COR_NOME_CANAL, font=font_nome)
    draw.text((175, 95), "@futzona2026", fill=COR_ARROBA, font=font_arroba)

    # Linha separadora dourada abaixo do header
    draw.rectangle([(0, Y_HEADER_H), (W, Y_HEADER_H + 5)], fill=(255, 200, 0))

    # ── Caixa do título ───────────────────────────────────────────────────────
    margem_titulo = 40
    draw.rounded_rectangle(
        [(margem_titulo, Y_TITULO_TOP + 10),
         (W - margem_titulo, Y_TITULO_BOT - 10)],
        radius=16,
        fill=COR_CAIXA_TITULO,
        outline=COR_BORDA_TITULO,
        width=5,
    )

    # Texto do título quebrado em múltiplas linhas
    titulo_upper = titulo.upper()
    font_titulo_g = _carregar_fonte(58, negrito=True)
    font_titulo_m = _carregar_fonte(50, negrito=True)
    font_titulo_p = _carregar_fonte(44, negrito=True)

    # Determina tamanho ideal da fonte baseado no comprimento
    if len(titulo_upper) <= 35:
        font_t = font_titulo_g
    elif len(titulo_upper) <= 60:
        font_t = font_titulo_m
    else:
        font_t = font_titulo_p

    max_chars = max(18, int((W - 2 * margem_titulo - 40) / (font_t.size * 0.55)))
    linhas = textwrap.wrap(titulo_upper, width=max_chars)

    # Centraliza as linhas verticalmente na caixa
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

    # Labels dos lados (VS no centro, nomes nas laterais)
    font_label = _carregar_fonte(36, negrito=True)
    font_vs     = _carregar_fonte(52, negrito=True)

    # Faixas de nome nas imagens
    for lado_x, nome in [(0, nome_a.upper()), (W // 2, nome_b.upper())]:
        # Fundo semitransparente
        overlay = Image.new("RGBA", (W // 2, 60), (0, 0, 0, 160))
        canvas.paste(Image.new("RGB", (W // 2, 60), (0, 0, 0)),
                     (lado_x, Y_IMG_BOT - 60),
                     mask=overlay.split()[3])
        # Trunca se necessário
        nome_curto = nome[:14] + "..." if len(nome) > 14 else nome
        bbox_l = draw.textbbox((0, 0), nome_curto, font=font_label)
        lw = bbox_l[2] - bbox_l[0]
        draw.text(
            (lado_x + (W // 2 - lw) // 2, Y_IMG_BOT - 50),
            nome_curto,
            fill=(255, 255, 255),
            font=font_label,
        )

    # VS central (círculo vermelho com "VS")
    vs_cx, vs_cy = W // 2, (Y_IMG_TOP + Y_IMG_BOT) // 2
    vs_r = 50
    draw.ellipse(
        [vs_cx - vs_r, vs_cy - vs_r, vs_cx + vs_r, vs_cy + vs_r],
        fill=(220, 30, 30),
        outline=(255, 255, 255),
        width=4,
    )
    bbox_vs = draw.textbbox((0, 0), "VS", font=font_vs)
    vsw, vsh = bbox_vs[2] - bbox_vs[0], bbox_vs[3] - bbox_vs[1]
    draw.text((vs_cx - vsw // 2, vs_cy - vsh // 2 - 4), "VS",
              fill=(255, 255, 255), font=font_vs)

    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# Geração de frames animados
# ─────────────────────────────────────────────────────────────────────────────
def _ease_in_out(t: float) -> float:
    """Função de easing suave (0→1)."""
    return t * t * (3 - 2 * t)


def _gerar_frame(
    frame_idx: int,
    frame_base: Image.Image,
    comentarios: list[str],
    titulo: str,
    img_a: Image.Image,
    img_b: Image.Image,
    nome_a: str,
    nome_b: str,
) -> np.ndarray:
    """Gera um único frame animado a partir do frame base."""
    t = frame_idx / N_FRAMES  # 0.0 → 1.0
    t_s = frame_idx / FPS     # tempo em segundos

    canvas = frame_base.copy()
    draw = ImageDraw.Draw(canvas)

    # ── Fase 1 (0.0-1.5s): Header aparece com fade ────────────────────────────
    # (já está no frame_base, nada a fazer — o header é sempre visível)

    # ── Fase 2 (1.5-3.0s): Título slide-up ────────────────────────────────────
    if t_s < 1.5:
        # Antes do título aparecer: cobre a caixa com retângulo branco
        margem = 40
        canvas_arr = np.array(canvas)
        canvas_arr[Y_TITULO_TOP:Y_TITULO_BOT, margem:W-margem] = [255, 255, 255]
        canvas = Image.fromarray(canvas_arr)
        draw = ImageDraw.Draw(canvas)
    elif t_s < 3.0:
        alpha_t = _ease_in_out((t_s - 1.5) / 1.5)
        # Efeito: caixa do título "sobe" e fica mais opaca
        # Implementado sobrepondo retângulo branco com transparência decrescente
        overlay_h = int((1.0 - alpha_t) * (Y_TITULO_BOT - Y_TITULO_TOP))
        if overlay_h > 0:
            overlay = Image.new("RGB", (W - 80, overlay_h), (255, 255, 255))
            canvas.paste(overlay, (40, Y_TITULO_TOP))

    # ── Fase 3 (3.0-5.5s): Imagens slide-in ──────────────────────────────────
    if t_s < 3.0:
        # Cobre área das imagens com branco
        canvas_arr = np.array(canvas)
        canvas_arr[Y_IMG_TOP:Y_IMG_BOT, 0:W] = [255, 255, 255]
        canvas = Image.fromarray(canvas_arr)
        draw = ImageDraw.Draw(canvas)
    elif t_s < 5.5:
        alpha_img = _ease_in_out((t_s - 3.0) / 2.5)
        img_h = Y_IMG_BOT - Y_IMG_TOP
        img_w = W // 2

        # Imagem A vem da esquerda
        offset_a = int((1 - alpha_img) * (-img_w))
        img_a_res = img_a.resize((img_w, img_h), Image.LANCZOS)
        # Recorta para não vazar para fora do canvas
        x_a = offset_a
        if x_a < 0:
            crop_left = -x_a
            img_a_crop = img_a_res.crop((crop_left, 0, img_w, img_h))
            canvas.paste(img_a_crop, (0, Y_IMG_TOP))
        else:
            canvas.paste(img_a_res, (x_a, Y_IMG_TOP))

        # Imagem B vem da direita
        offset_b = int((1 - alpha_img) * img_w)
        img_b_res = img_b.resize((img_w, img_h), Image.LANCZOS)
        x_b = img_w + offset_b
        if x_b + img_w > W:
            crop_right = (x_b + img_w) - W
            img_b_crop = img_b_res.crop((0, 0, img_w - crop_right, img_h))
            canvas.paste(img_b_crop, (x_b, Y_IMG_TOP))
        else:
            canvas.paste(img_b_res, (x_b, Y_IMG_TOP))

        # Reaplica VS e labels (desenha sobre as imagens)
        draw = ImageDraw.Draw(canvas)
        _reaplicar_overlays_imagem(draw, nome_a, nome_b, alpha_img)

    # ── Fase 4 (5.5-9.0s): Comentários aparecem um a um ─────────────────────
    if t_s >= 5.5:
        draw = ImageDraw.Draw(canvas)
        dur_total_coment = 3.5  # segundos para todos os comentários
        n_coment = min(3, len(comentarios))
        dur_por_coment = dur_total_coment / max(n_coment, 1)

        for i in range(n_coment):
            t_inicio = 5.5 + i * dur_por_coment
            t_fim    = t_inicio + dur_por_coment

            if t_s >= t_inicio:
                alpha_c = min(1.0, _ease_in_out((t_s - t_inicio) / 0.4))
                _desenhar_comentario(draw, comentarios[i], i, alpha_c)

    # ── Fase 5 (9.0-10.0s): Call-to-action pulsante ──────────────────────────
    if t_s >= 9.0:
        draw = ImageDraw.Draw(canvas)
        pulso = 0.5 + 0.5 * math.sin((t_s - 9.0) * math.pi * 4)  # 2 pulsos/s
        r = int(pulso * 30) + 200
        g = int(pulso * 10) + 30
        b = int(pulso * 10) + 30
        alpha_cta = min(1.0, (t_s - 9.0) / 0.5)

        font_cta = _carregar_fonte(52, negrito=True)
        cta_texto = "👇 COMENTE ABAIXO!"
        bbox_cta = draw.textbbox((0, 0), cta_texto, font=font_cta)
        cw = bbox_cta[2] - bbox_cta[0]
        draw.text(
            ((W - cw) // 2, Y_CTA),
            cta_texto,
            fill=(r, g, b),
            font=font_cta,
        )

    return np.array(canvas)


def _reaplicar_overlays_imagem(draw: ImageDraw.Draw, nome_a: str, nome_b: str, alpha: float):
    """Reaplica os overlays de texto nas imagens (VS, nomes) após animação."""
    font_label = _carregar_fonte(36, negrito=True)
    font_vs     = _carregar_fonte(52, negrito=True)

    if alpha < 0.6:
        return

    # Labels dos nomes
    for lado_x, nome in [(0, nome_a.upper()), (W // 2, nome_b.upper())]:
        nome_curto = nome[:14] + "..." if len(nome) > 14 else nome
        bbox_l = draw.textbbox((0, 0), nome_curto, font=font_label)
        lw = bbox_l[2] - bbox_l[0]
        draw.text(
            (lado_x + (W // 2 - lw) // 2, Y_IMG_BOT - 50),
            nome_curto,
            fill=(255, 255, 255),
            font=font_label,
        )

    # VS central
    if alpha > 0.7:
        vs_cx, vs_cy = W // 2, (Y_IMG_TOP + Y_IMG_BOT) // 2
        vs_r = 50
        draw.ellipse(
            [vs_cx - vs_r, vs_cy - vs_r, vs_cx + vs_r, vs_cy + vs_r],
            fill=(220, 30, 30),
            outline=(255, 255, 255),
            width=4,
        )
        bbox_vs = draw.textbbox((0, 0), "VS", font=font_vs)
        vsw, vsh = bbox_vs[2] - bbox_vs[0], bbox_vs[3] - bbox_vs[1]
        draw.text((vs_cx - vsw // 2, vs_cy - vsh // 2 - 4), "VS",
                  fill=(255, 255, 255), font=font_vs)


def _desenhar_comentario(draw: ImageDraw.Draw, texto: str, idx: int, alpha: float):
    """Desenha um balão de comentário no canvas."""
    font_coment = _carregar_fonte(30)
    font_pequeno = _carregar_fonte(24)

    # Posição Y de cada comentário
    y_base = Y_COMENT_TOP + idx * 200
    x_borda = 40
    balao_w = W - 80
    balao_h = 170

    # Fundo do balão
    draw.rounded_rectangle(
        [(x_borda, y_base), (x_borda + balao_w, y_base + balao_h)],
        radius=16,
        fill=(245, 245, 245),
        outline=(220, 220, 220),
        width=2,
    )

    # Avatar simulado (círculo colorido com inicial)
    cores_avatar = [(52, 152, 219), (231, 76, 60), (46, 204, 113), (155, 89, 182)]
    cor_av = cores_avatar[idx % len(cores_avatar)]
    av_r = 28
    av_x, av_y = x_borda + 18 + av_r, y_base + balao_h // 2
    draw.ellipse(
        [av_x - av_r, av_y - av_r, av_x + av_r, av_y + av_r],
        fill=cor_av,
    )
    font_av = _carregar_fonte(26, negrito=True)
    draw.text((av_x - 9, av_y - 14), "F", fill=(255, 255, 255), font=font_av)

    # Texto do comentário (quebra em até 2 linhas)
    texto_limpo = texto[:100]
    max_chars = 45
    linhas = textwrap.wrap(texto_limpo, width=max_chars)

    x_texto = av_x + av_r + 20
    y_texto = y_base + 30
    for i, linha in enumerate(linhas[:2]):
        draw.text((x_texto, y_texto + i * 38), linha,
                  fill=COR_COMENTARIO, font=font_coment)

    # "Curtidas" simuladas
    draw.text(
        (x_texto, y_base + balao_h - 45),
        f"❤️ {(idx + 1) * 847 + 123:,}   👍 {(idx + 1) * 312:,}",
        fill=(150, 150, 150),
        font=font_pequeno,
    )


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

    Parâmetros:
      dados       → dict com titulo, lado_a_nome, lado_b_nome, comentarios
      img_a       → PIL.Image do lado A (já processada por buscar_imagens)
      img_b       → PIL.Image do lado B (já processada por buscar_imagens)
      musica_path → caminho do MP3 (ou None)
      output_dir  → pasta de saída

    Retorna o caminho do MP4 gerado.
    """
    os.makedirs(output_dir, exist_ok=True)

    titulo   = dados.get("titulo", "POLÊMICA DO FUTEBOL!").upper()
    nome_a   = dados.get("lado_a_nome", "LADO A")
    nome_b   = dados.get("lado_b_nome", "LADO B")
    comentarios = dados.get("comentarios", [
        "🔥 Que polêmica demais!",
        "😂 Isso aí é lenda!",
        "💥 Precisava de mais?",
    ])

    print(f"\n🎬 Montando vídeo: '{titulo}'")
    print(f"   {N_FRAMES} frames × {FPS}fps = {DURACAO_S}s")

    # Cria frame base (estático)
    print("   🖼️  Criando frame base...")
    frame_base = _criar_frame_base(titulo, img_a, img_b, nome_a, nome_b)

    # Pasta temporária para frames
    with tempfile.TemporaryDirectory() as frames_dir:
        print(f"   🎞️  Gerando {N_FRAMES} frames animados...")

        for i in range(N_FRAMES):
            frame_arr = _gerar_frame(i, frame_base, comentarios, titulo,
                                      img_a, img_b, nome_a, nome_b)
            frame_img = Image.fromarray(frame_arr)
            frame_img.save(
                os.path.join(frames_dir, f"frame_{i:04d}.jpg"),
                "JPEG", quality=88,
            )
            if i % 30 == 0:
                print(f"   ⏳ Frame {i}/{N_FRAMES} ({i*100//N_FRAMES}%)")

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
        "titulo": "MESSI ROUBOU A BOLA DE OURO DO NEYMAR EM 2015?",
        "lado_a_nome": "Messi",
        "lado_b_nome": "Neymar",
        "comentarios": [
            "🔥 Com certeza! O Neymar estava melhor!",
            "😂 O Messi merecia sim, foi o melhor do ano",
            "💥 Esse assunto até hoje divide opiniões!",
        ],
    }
    video = montar_video(dados_teste, img_teste, img_teste, None, "output")
    print(f"Teste: {video}")
