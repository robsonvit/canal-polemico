"""
buscar_imagens.py
─────────────────
Busca 2 imagens para os lados A e B da polêmica.

Estratégia:
  1. DuckDuckGo Search (via ddgs) - muito confiável e não requer chave de API.
  2. Wikipedia API (pesquisa de páginas e imagens) - Excelente fallback, bloqueio raríssimo.
  3. Placeholder colorido - último recurso (nunca falha).
"""

import os
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IMG_WIDTH  = 520
IMG_HEIGHT = 580

HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 1: DuckDuckGo Search
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_ddg(termo: str, destino: str, prefixo: str) -> str | None:
    try:
        from duckduckgo_search import DDGS
        print(f"   🔎 Pesquisando no DuckDuckGo: '{termo}'")
        
        results = DDGS().images(termo, max_results=3)
        
        for item in results:
            url_img = item.get("image", "")
            if not url_img:
                continue
            try:
                r = requests.get(url_img, headers=HEADERS_BROWSER, timeout=15, stream=True)
                r.raise_for_status()
                destino_final = os.path.join(destino, f"{prefixo}_ddg.jpg")
                with open(destino_final, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                Image.open(destino_final).verify()
                print(f"   ✅ DuckDuckGo OK para '{termo}'")
                return destino_final
            except Exception:
                if os.path.exists(destino_final):
                    os.remove(destino_final)
                continue
        return None
    except Exception as e:
        print(f"   ⚠️  DuckDuckGo falhou: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 2: Wikipedia API
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_wikipedia(termo: str, destino: str, prefixo: str) -> str | None:
    """Busca a imagem da página da Wikipedia do termo (muito bom para famosos)."""
    try:
        print(f"   🔎 Pesquisando na Wikipedia: '{termo}'")
        # 1. Pesquisa a página
        url_search = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={termo}&format=json"
        r = requests.get(url_search, timeout=10)
        data = r.json()
        if not data['query']['search']: return None
        pageid = data['query']['search'][0]['pageid']
        
        # 2. Pega as imagens da página
        url_images = f"https://pt.wikipedia.org/w/api.php?action=query&prop=images&pageids={pageid}&format=json"
        r2 = requests.get(url_images, timeout=10)
        data2 = r2.json()
        images = data2['query']['pages'][str(pageid)].get('images', [])
        for img in images:
            title = img['title']
            if not title.lower().endswith(('.jpg', '.jpeg', '.png')): 
                continue
            
            # 3. Pega a URL da imagem
            url_file = f"https://pt.wikipedia.org/w/api.php?action=query&titles={title}&prop=imageinfo&iiprop=url&format=json"
            r3 = requests.get(url_file, timeout=10)
            data3 = r3.json()
            pages = data3['query']['pages']
            img_url = list(pages.values())[0]['imageinfo'][0]['url']
            
            # 4. Faz o download
            r4 = requests.get(img_url, headers=HEADERS_BROWSER, stream=True, timeout=15)
            r4.raise_for_status()
            destino_final = os.path.join(destino, f"{prefixo}_wiki.jpg")
            with open(destino_final, 'wb') as f:
                for chunk in r4.iter_content(8192):
                    f.write(chunk)
            Image.open(destino_final).verify()
            print(f"   ✅ Wikipedia OK para '{termo}'")
            return destino_final
        return None
    except Exception as e:
        print(f"   ⚠️  Wikipedia falhou: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 3: Placeholder colorido (nunca falha)
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
        
        # Sequência robusta: DDGS -> Wikipedia -> Placeholder
        caminho = (
            _buscar_ddg(termo, output_dir, f"img_{lado}")
            or _buscar_wikipedia(nome, output_dir, f"img_{lado}") # Busca pelo nome na Wiki que é mais certeiro
            or _criar_placeholder(nome, output_dir, f"img_{lado}", CORES[cor_key])
        )

        caminhos[lado] = caminho
        time.sleep(1)

    img_a = _processar_imagem(caminhos["a"])
    img_b = _processar_imagem(caminhos["b"])
    print(f"\n✅ Imagens processadas: {IMG_WIDTH}x{IMG_HEIGHT}px cada")
    return img_a, img_b
