"""
buscar_imagens.py
─────────────────
Busca 2 imagens para os lados A e B da polêmica.

Estratégia:
  1. DuckDuckGo Search (novo pacote 'ddgs' com bypass anti-bot)
  2. Wikipedia API Direta (com encoding de URL e User-Agent, robusto)
  3. Aborta o script caso não encontre (evita postar placeholders).
"""

import os
import time
import requests
import urllib.parse
from PIL import Image

IMG_WIDTH  = 520
IMG_HEIGHT = 580

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 1: DuckDuckGo (via pacote 'ddgs')
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_duckduckgo(termo: str, destino: str, prefixo: str) -> str | None:
    try:
        from ddgs import DDGS
        print(f"   🔎 Pesquisando DuckDuckGo: '{termo}'")
        
        resultados = DDGS().images(termo, max_results=3)
        if not resultados:
            return None
            
        for i, res in enumerate(resultados):
            thumb_url = res.get('thumbnail')
            img_url = res.get('image')
            
            url = None
            if thumb_url and "bing.net" in thumb_url:
                parsed = urllib.parse.urlparse(thumb_url)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'id' in qs:
                    url = f"https://ts1.mm.bing.net/th?id={qs['id'][0]}&w=800&h=800"
            
            # Se não conseguiu extrair do bing, tenta usar a original
            if not url:
                url = img_url
                
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
        search_url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(termo)}&utf8=&format=json"
        
        headers = {"User-Agent": "BotCanalPolemico/1.0 (robsonvit@github.com)"}
        r = requests.get(search_url, headers=headers, timeout=10)
        data = r.json()
        if not data.get("query", {}).get("search"):
            return None
            
        title = data["query"]["search"][0]["title"]
        img_url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=1000"
        
        r2 = requests.get(img_url, headers=headers, timeout=10)
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
    caminhos = {}
    
    for lado, termo, nome in [("a", termo_a, nome_a), ("b", termo_b, nome_b)]:
        print(f"\n🔍 Buscando imagem para [{nome}]: '{termo}'")
        
        caminho = (
            _buscar_duckduckgo(termo, output_dir, f"img_{lado}")
            or _buscar_wikipedia(termo, output_dir, f"img_{lado}")
        )
        
        if not caminho:
            raise Exception(f"❌ ERRO CRÍTICO: Não foi possível encontrar a imagem para '{nome}'. O pipeline deve abortar para não gerar um vídeo vazio ou com placeholder falso.")

        caminhos[lado] = caminho
        time.sleep(1)

    img_a = _processar_imagem(caminhos["a"])
    img_b = _processar_imagem(caminhos["b"])
    print(f"\n✅ Imagens processadas: {IMG_WIDTH}x{IMG_HEIGHT}px cada")
    return img_a, img_b
