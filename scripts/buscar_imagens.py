"""
buscar_imagens.py
─────────────────
Busca 2 imagens para os lados A e B da polêmica.

Estratégia em cascata:
  1. icrawler (GoogleImageCrawler) — tenta primeiro, sem chave de API
  2. Bing Image Search API (gratuita, 1000 req/mês) — fallback com BING_API_KEY
  3. Imagem placeholder colorida — último recurso (nunca falha)

As imagens são redimensionadas para 520×580px cada e salvas em output/.
"""

import os
import time
import shutil
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────────────────────────────────────────────────────────
# Configurações
# ─────────────────────────────────────────────────────────────────────────────
BING_API_KEY = os.environ.get("BING_API_KEY", "")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/search"

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
# Estratégia 1: icrawler (Google Images)
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_icrawler(termo: str, destino: str, prefixo: str) -> str | None:
    """Tenta baixar imagem via icrawler. Retorna caminho ou None."""
    try:
        from icrawler.builtin import GoogleImageCrawler

        tmp_dir = f"/tmp/icrawler_{prefixo}_{int(time.time())}"
        os.makedirs(tmp_dir, exist_ok=True)

        crawler = GoogleImageCrawler(
            storage={"root_dir": tmp_dir},
            downloader_threads=2,
        )
        crawler.crawl(
            keyword=termo,
            max_num=3,
            file_idx_offset=0,
            filters={"type": "photo", "size": "large"},
        )

        # Pega o primeiro arquivo encontrado
        arquivos = sorted(Path(tmp_dir).glob("*.*"))
        if arquivos:
            destino_final = os.path.join(destino, f"{prefixo}_icrawler.jpg")
            shutil.copy(str(arquivos[0]), destino_final)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            print(f"   ✅ icrawler OK para '{termo}'")
            return destino_final

        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"   ⚠️  icrawler: nenhuma imagem encontrada para '{termo}'")
        return None

    except Exception as e:
        print(f"   ⚠️  icrawler falhou: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 2: Bing Image Search API
# ─────────────────────────────────────────────────────────────────────────────
def _buscar_bing(termo: str, destino: str, prefixo: str) -> str | None:
    """Busca imagem via Bing Image Search API. Retorna caminho ou None."""
    if not BING_API_KEY:
        print(f"   ⚠️  BING_API_KEY não configurada, pulando Bing")
        return None

    try:
        params = {
            "q":          termo,
            "count":      5,
            "imageType":  "Photo",
            "size":       "Large",
            "safeSearch": "Moderate",
        }
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}

        resp = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        resultados = resp.json().get("value", [])

        for item in resultados:
            url_img = item.get("contentUrl", "")
            if not url_img:
                continue
            try:
                r = requests.get(url_img, headers=HEADERS_BROWSER, timeout=20, stream=True)
                r.raise_for_status()
                destino_final = os.path.join(destino, f"{prefixo}_bing.jpg")
                with open(destino_final, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                # Valida que é uma imagem real
                Image.open(destino_final).verify()
                print(f"   ✅ Bing OK para '{termo}'")
                return destino_final
            except Exception:
                if os.path.exists(destino_final):
                    os.remove(destino_final)
                continue

        print(f"   ⚠️  Bing: nenhuma imagem válida para '{termo}'")
        return None

    except Exception as e:
        print(f"   ⚠️  Bing falhou: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 3: Placeholder colorido (nunca falha)
# ─────────────────────────────────────────────────────────────────────────────
def _criar_placeholder(nome: str, destino: str, prefixo: str, cor: tuple) -> str:
    """Cria uma imagem placeholder com o nome do personagem. Nunca falha."""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=cor)
    draw = ImageDraw.Draw(img)

    # Tenta usar uma fonte do sistema
    font_size = 48
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Texto centralizado
    linhas = nome.upper().split()
    y_start = IMG_HEIGHT // 2 - (len(linhas) * (font_size + 10)) // 2
    for i, linha in enumerate(linhas):
        bbox = draw.textbbox((0, 0), linha, font=font)
        w = bbox[2] - bbox[0]
        x = (IMG_WIDTH - w) // 2
        y = y_start + i * (font_size + 10)
        draw.text((x + 2, y + 2), linha, fill=(0, 0, 0, 100), font=font)  # sombra
        draw.text((x, y), linha, fill=(255, 255, 255), font=font)

    # Ícone de bola de futebol (texto emoji simulado)
    draw.ellipse(
        [IMG_WIDTH//2 - 40, 30, IMG_WIDTH//2 + 40, 110],
        fill=(255, 255, 255, 200),
        outline=(200, 200, 200),
        width=3,
    )

    caminho = os.path.join(destino, f"{prefixo}_placeholder.jpg")
    img.save(caminho, "JPEG", quality=95)
    print(f"   🎨 Placeholder criado para '{nome}'")
    return caminho


# ─────────────────────────────────────────────────────────────────────────────
# Processamento final da imagem
# ─────────────────────────────────────────────────────────────────────────────
def _processar_imagem(caminho: str) -> Image.Image:
    """Abre, converte para RGB e redimensiona para IMG_WIDTH x IMG_HEIGHT."""
    img = Image.open(caminho).convert("RGB")

    # Crop inteligente: mantém proporção e centraliza
    ratio_target = IMG_WIDTH / IMG_HEIGHT
    ratio_orig   = img.width / img.height

    if ratio_orig > ratio_target:
        # Mais larga que o target → crop horizontal
        novo_w = int(img.height * ratio_target)
        left   = (img.width - novo_w) // 2
        img    = img.crop((left, 0, left + novo_w, img.height))
    else:
        # Mais alta que o target → crop vertical
        novo_h = int(img.width / ratio_target)
        top    = (img.height - novo_h) // 2
        img    = img.crop((0, top, img.width, top + novo_h))

    return img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def buscar_imagens(
    termo_a: str,
    nome_a:  str,
    termo_b: str,
    nome_b:  str,
    output_dir: str,
) -> tuple[Image.Image, Image.Image]:
    """
    Busca e processa as imagens dos dois lados da polêmica.

    Retorna uma tupla (img_a, img_b) como objetos PIL.Image prontos
    para compor o layout 9:16.
    """
    os.makedirs(output_dir, exist_ok=True)

    CORES = {
        "a": (20, 40, 80),    # Azul escuro (lado A)
        "b": (120, 20, 20),   # Vermelho escuro (lado B)
    }

    caminhos = {}
    for lado, termo, nome, cor_key in [
        ("a", termo_a, nome_a, "a"),
        ("b", termo_b, nome_b, "b"),
    ]:
        print(f"\n🔍 Buscando imagem para [{nome}]: '{termo}'")

        # Cascata: icrawler → Bing → placeholder
        caminho = (
            _buscar_icrawler(termo, output_dir, f"img_{lado}")
            or _buscar_bing(termo, output_dir, f"img_{lado}")
            or _criar_placeholder(nome, output_dir, f"img_{lado}", CORES[cor_key])
        )

        caminhos[lado] = caminho
        time.sleep(1)  # Pequena pausa entre requisições

    img_a = _processar_imagem(caminhos["a"])
    img_b = _processar_imagem(caminhos["b"])

    print(f"\n✅ Imagens processadas: {IMG_WIDTH}x{IMG_HEIGHT}px cada")
    return img_a, img_b


if __name__ == "__main__":
    img_a, img_b = buscar_imagens(
        termo_a="Messi Barcelona camisa 10",
        nome_a="Messi",
        termo_b="Neymar Bola de Ouro 2015",
        nome_b="Neymar",
        output_dir="output",
    )
    img_a.save("output/teste_img_a.jpg")
    img_b.save("output/teste_img_b.jpg")
    print("Teste OK!")
