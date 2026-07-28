"""
pipeline.py
───────────
Orquestrador principal do Canal Polêmico — FUT ZONA (@futzona2026).
Executa os passos em sequência:

  1. Gerar polêmica viral via Groq AI
  2. Buscar imagens dos 2 lados (icrawler → Bing → placeholder)
  3. Baixar música viral royalty-free (10s)
  4. Montar Short 1080×1920 com animações (10s exatos)
  5. Upload para o YouTube @futzona2026
  6. Salvar tracking de polêmicas usadas

Uso:
    python scripts/pipeline.py
"""

import os
import sys
import json
import traceback
from datetime import datetime, timezone

# Força UTF-8 no stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
DATA_DIR   = os.path.join(ROOT_DIR, "data")
sys.path.insert(0, ROOT_DIR)


def _titulo(passo: int, total: int, descricao: str):
    print(f"\n{'─'*65}")
    print(f" PASSO {passo}/{total}: {descricao}")
    print(f"{'─'*65}")


def _salvar_tracking(dados: dict):
    """Registra a polêmica gerada para evitar repetições."""
    tracking_path = os.path.join(DATA_DIR, "polemica_usadas.json")
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        with open(tracking_path, "r", encoding="utf-8") as f:
            historico = json.load(f)
    except Exception:
        historico = []

    historico.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "titulo": dados.get("titulo", ""),
        "lado_a": dados.get("lado_a_nome", ""),
        "lado_b": dados.get("lado_b_nome", ""),
    })

    # Mantém apenas os últimos 200 registros
    historico = historico[-200:]

    with open(tracking_path, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    print(f"   📊 Tracking: {len(historico)} polêmicas registradas")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    print("\n" + "═"*65)
    print("  🔥  CANAL POLÊMICO — FUT ZONA (@futzona2026)")
    print("  📱  Pipeline de Shorts de Futebol")
    print("═"*65)

    # ──────────────────────────────────────────────────────────────────────────
    # PASSO 1 — Gerar polêmica viral via Groq AI
    # ──────────────────────────────────────────────────────────────────────────
    _titulo(1, 5, "Gerando polêmica viral com Groq AI (llama-3.3-70b)...")
    from scripts.gerar_conteudo import gerar_conteudo

    dados = gerar_conteudo()
    conteudo_json = os.path.join(OUTPUT_DIR, "conteudo.json")

    print(f"✅ Polêmica  : {dados['titulo']}")
    print(f"   Lado A    : {dados['lado_a_nome']}")
    print(f"   Lado B    : {dados['lado_b_nome']}")
    print(f"   Comentários: {len(dados['comentarios'])} gerados")

    with open(conteudo_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────────────────────────────────────
    # PASSO 2 — Buscar imagens dos 2 lados da polêmica
    # ──────────────────────────────────────────────────────────────────────────
    _titulo(2, 5, f"Buscando imagens: '{dados['lado_a_nome']}' vs '{dados['lado_b_nome']}'...")
    from scripts.buscar_imagens import buscar_imagens

    img_a, img_b = buscar_imagens(
        termo_a=dados.get("termo_busca_a", dados["lado_a_nome"] + " futebol"),
        nome_a=dados["lado_a_nome"],
        termo_b=dados.get("termo_busca_b", dados["lado_b_nome"] + " futebol"),
        nome_b=dados["lado_b_nome"],
        output_dir=OUTPUT_DIR,
    )
    print(f"✅ Imagens prontas: {img_a.size} cada")

    # ──────────────────────────────────────────────────────────────────────────
    # PASSO 3 — Baixar música viral royalty-free
    # ──────────────────────────────────────────────────────────────────────────
    _titulo(3, 5, "Baixando música viral/trap royalty-free (10s)...")
    from scripts.baixar_musica import baixar_musica

    musica_path = baixar_musica(OUTPUT_DIR)
    if musica_path:
        print(f"✅ Música    : {musica_path}")
    else:
        print("⚠️  Sem música de fundo (continuando sem trilha)")

    # ──────────────────────────────────────────────────────────────────────────
    # PASSO 4 — Montar Short 1080×1920 com animações
    # ──────────────────────────────────────────────────────────────────────────
    _titulo(4, 5, "Montando Short 1080×1920 com animações (10s)...")
    from scripts.montar_video import montar_video

    video_final = montar_video(
        dados=dados,
        img_a=img_a,
        img_b=img_b,
        musica_path=musica_path,
        output_dir=OUTPUT_DIR,
    )
    tamanho_mb = os.path.getsize(video_final) / 1024 / 1024
    print(f"✅ Vídeo    : {video_final} ({tamanho_mb:.1f} MB)")

    # ──────────────────────────────────────────────────────────────────────────
    # PASSO 5 — Upload para o YouTube @futzona2026
    # ──────────────────────────────────────────────────────────────────────────
    _titulo(5, 5, "Publicando Short no YouTube (@futzona2026)...")

    _salvar_tracking(dados)

    if not os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        print("⚠️  YOUTUBE_REFRESH_TOKEN não configurado.")
        print("   Configure os secrets no GitHub para ativar o upload.")
        print(f"\n   ✅ Short salvo localmente em: {video_final}")
    else:
        try:
            from scripts.upload_youtube import upload_youtube
            video_id = upload_youtube(video_final, dados)
            print(f"\n🎉 SHORT PUBLICADO!")
            print(f"   📱 https://www.youtube.com/shorts/{video_id}")
        except Exception as e:
            erro_str = str(e)
            print(f"\n⚠️  Upload para o YouTube falhou: {erro_str[:200]}")
            if "invalid_client" in erro_str or "OAuth" in erro_str:
                print("")
                print("   📋 SOLUÇÃO: As credenciais OAuth precisam ser do canal @futzona2026.")
                print("   1. Acesse Google Cloud Console → Credentials")
                print("   2. Crie um OAuth 2.0 Client ID para o canal @futzona2026")
                print("   3. Execute: python scripts/obter_token.py")
                print("   4. Atualize os secrets YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET")
                print("      e YOUTUBE_REFRESH_TOKEN no GitHub Actions")
            print(f"\n   ✅ Short gerado com sucesso! Salvo no artefato do workflow.")
            print(f"   📁 {video_final}")
            # NÃO levanta exceção — o vídeo foi gerado, só o upload falhou

    # ── Resumo final ──────────────────────────────────────────────────────────
    print("\n" + "═"*65)
    print("  📁 Arquivos gerados:")
    for arq in ["conteudo.json"]:
        caminho = os.path.join(OUTPUT_DIR, arq)
        if os.path.exists(caminho):
            kb = os.path.getsize(caminho) / 1024
            print(f"     {arq:<28} {kb:.0f} KB")
    for arq in os.listdir(OUTPUT_DIR):
        if arq.endswith(".mp4"):
            caminho = os.path.join(OUTPUT_DIR, arq)
            mb = os.path.getsize(caminho) / 1024 / 1024
            print(f"     {arq:<28} {mb:.1f} MB")
    print("═"*65 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        sys.exit(1)
