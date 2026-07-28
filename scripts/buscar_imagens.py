"""
buscar_imagens.py
─────────────────
Busca 2 imagens para os lados A e B da polêmica.

Estratégia:
  1. Bing Image Downloader - extremamente robusto contra bloqueios.
  2. Placeholder colorido - último recurso (nunca falha).
"""

import os
import time
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IMG_WIDTH  = 520
IMG_HEIGHT = 580

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 1: Bing Image Downloader
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_bing(termo: str, destino: str, prefixo: str) -> str | None:
    try:
        from bing_image_downloader import downloader
        print(f"   🔎 Pesquisando no Bing: '{termo}'")
        
        tmp_dir = os.path.join(destino, "tmp_bing")
        
        downloader.download(
            termo, 
            limit=1, 
            output_dir=tmp_dir, 
            adult_filter_off=True, 
            force_replace=False, 
            timeout=15, 
            verbose=False
        )
        
        # A biblioteca cria uma subpasta com o nome do termo
        pasta_termo = os.path.join(tmp_dir, termo)
        if not os.path.exists(pasta_termo):
            return None
            
        arquivos = list(Path(pasta_termo).glob("*.*"))
        if not arquivos:
            return None
            
        arquivo_baixado = str(arquivos[0])
        destino_final = os.path.join(destino, f"{prefixo}_bing.jpg")
        
        shutil.copy(arquivo_baixado, destino_final)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
        # Valida que é uma imagem real
        Image.open(destino_final).verify()
        print(f"   ✅ Bing Image OK para '{termo}'")
        return destino_final

    except Exception as e:
        print(f"   ⚠️  Bing Image falhou: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 2: Placeholder colorido (nunca falha)
# ─────────────────────────────────────────────────────────────────────────────
def _criar_placeholder(nome: str, destino: str, prefixo: str, cor: tuple) -> str:
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=cor)
    draw = ImageDraw.Draw(img)

    font_size = 48
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    linhas = nome.upper().split()
    y_start = IMG_HEIGHT // 2 - (len(linhas) * (font_size + 10)) // 2
    for i, linha in enumerate(linhas):
        bbox = draw.textbbox((0, 0), linha, font=font)
        w = bbox[2] - bbox[0]
        x = (IMG_WIDTH - w) // 2
        y = y_start + i * (font_size + 10)
        draw.text((x + 2, y + 2), linha, fill=(0, 0, 0, 100), font=font)
        draw.text((x, y), linha, fill=(255, 255, 255), font=font)

    draw.ellipse([IMG_WIDTH//2 - 40, 30, IMG_WIDTH//2 + 40, 110], fill=(255, 255, 255, 200), outline=(200, 200, 200), width=3)
    caminho = os.path.join(destino, f"{prefixo}_placeholder.jpg")
    img.save(caminho, "JPEG", quality=95)
    print(f"   🎨 Placeholder criado para '{nome}'")
    return caminho

# ─────────────────────────────────────────────────────────────────────────────
# Processamento final da imagem
# ─────────────────────────────────────────────────────────────────────────────
def _processar_imagem(caminho: str) -> Image.Image:
    img = Image.open(caminho).convert("RGB")
    ratio_target = IMG_WIDTH / IMG_HEIGHT
    ratio_orig   = img.width / img.height

    if ratio_orig > ratio_target:
        novo_w = int(img.height * ratio_target)
        left   = (img.width - novo_w) // 2
        img    = img.crop((left, 0, left + novo_w, img.height))
    else:
        novo_h = int(img.width / ratio_target)
        top    = (img.height - novo_h) // 2
        img    = img.crop((0, top, img.width, top + novo_h))

    return img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)

# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def buscar_imagens(termo_a: str, nome_a: str, termo_b: str, nome_b: str, output_dir: str) -> tuple[Image.Image, Image.Image]:
    os.makedirs(output_dir, exist_ok=True)
    CORES = {"a": (20, 40, 80), "b": (120, 20, 20)}
    caminhos = {}
    for lado, termo, nome, cor_key in [("a", termo_a, nome_a, "a"), ("b", termo_b, nome_b, "b")]:
        print(f"\n🔍 Buscando imagem para [{nome}]: '{termo}'")
        
        # Sequência blindada: Bing (sem API key) -> Placeholder
        caminho = (
            _buscar_bing(termo, output_dir, f"img_{lado}")
            or _criar_placeholder(nome, output_dir, f"img_{lado}", CORES[cor_key])
        )

        caminhos[lado] = caminho
        time.sleep(1)

    img_a = _processar_imagem(caminhos["a"])
    img_b = _processar_imagem(caminhos["b"])
    print(f"\n✅ Imagens processadas: {IMG_WIDTH}x{IMG_HEIGHT}px cada")
    return img_a, img_b
