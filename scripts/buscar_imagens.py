"""
buscar_imagens.py
─────────────────
Busca 2 imagens para os lados A e B da polêmica.

Estratégia:
  1. DuckDuckGo Search (muito preciso, busca imagens exatas)
  2. Wikipedia API Direta (sempre funciona e sem rate limit, ótimo fallback)
  3. Placeholder colorido (último recurso)
"""

import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont

IMG_WIDTH  = 520
IMG_HEIGHT = 580

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 1: DuckDuckGo
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_duckduckgo(termo: str, destino: str, prefixo: str) -> str | None:
    try:
        from duckduckgo_search import DDGS
        print(f"   🔎 Pesquisando DDG: '{termo}'")
        
        resultados = DDGS().images(termo, max_results=3)
        if not resultados:
            return None
            
        for i, res in enumerate(resultados):
            url = res.get('image')
            if not url: continue
            
            try:
                print(f"   📥 Baixando imagem {i+1}...")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    caminho = os.path.join(destino, f"{prefixo}_ddg.jpg")
                    with open(caminho, 'wb') as f:
                        f.write(r.content)
                    Image.open(caminho).verify()
                    print(f"   ✅ DuckDuckGo Image OK")
                    return caminho
            except Exception:
                continue
        return None
    except Exception as e:
        print(f"   ⚠️  DuckDuckGo falhou: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 2: Wikipedia Direta (via requests)
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_wikipedia(termo: str, destino: str, prefixo: str) -> str | None:
    try:
        print(f"   🔎 Pesquisando na Wikipedia (fallback): '{termo}'")
        search_url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={termo}&utf8=&format=json"
        r = requests.get(search_url, timeout=10)
        data = r.json()
        if not data.get("query", {}).get("search"):
            return None
            
        title = data["query"]["search"][0]["title"]
        img_url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages&format=json&pithumbsize=1000"
        r2 = requests.get(img_url, timeout=10)
        pages = r2.json().get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                url = page_data["thumbnail"]["source"]
                print(f"   📥 Baixando foto oficial da Wikipedia: {title}")
                r3 = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if r3.status_code == 200:
                    caminho = os.path.join(destino, f"{prefixo}_wiki.jpg")
                    with open(caminho, 'wb') as f:
                        f.write(r3.content)
                    Image.open(caminho).verify()
                    print(f"   ✅ Wikipedia Image OK")
                    return caminho
        return None
    except Exception as e:
        print(f"   ⚠️  Wikipedia falhou: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 3: Placeholder
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
# Processamento final
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
        
        caminho = (
            _buscar_duckduckgo(termo, output_dir, f"img_{lado}")
            or _buscar_wikipedia(termo, output_dir, f"img_{lado}")
            or _criar_placeholder(nome, output_dir, f"img_{lado}", CORES[cor_key])
        )

        caminhos[lado] = caminho
        time.sleep(1)

    img_a = _processar_imagem(caminhos["a"])
    img_b = _processar_imagem(caminhos["b"])
    print(f"\n✅ Imagens processadas: {IMG_WIDTH}x{IMG_HEIGHT}px cada")
    return img_a, img_b
