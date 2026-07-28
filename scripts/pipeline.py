import os
from scripts.gerar_conteudo import gerar_conteudo_com_ia
from scripts.buscar_imagens import buscar_imagens
from scripts.baixar_musica import baixar_musica
from scripts.montar_video import montar_video
import json

def main():
      print("INICIANDO PIPELINE - CANAL POLEMICO")
      print("="*65)

    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # -- 1. Gerar Conteudo -----------------------------------------------------
    print("\n[1/5] Gerando conteudo com IA...")
    dados = gerar_conteudo_com_ia()
    if not dados:
              print("Erro ao gerar conteudo.")
              return
          print(f"Tema escolhido: {dados['titulo']}")

    # -- 2. Buscar Imagens -----------------------------------------------------
    print("\n[2/5] Buscando imagens para:")
    print(f"    Lado A: {dados['lado_a']}")
    print(f"    Lado B: {dados['lado_b']}")
    img_a, img_b = buscar_imagens(dados["lado_a"], dados["lado_b"])
    print(f"Imagens prontas.")

    # -- 3. Baixar Musica ------------------------------------------------------
    print("\n[3/5] Baixando musica viral (10s)...")
    musica = baixar_musica()
    if not musica:
              print("Erro ao baixar musica.")
              return
          print(f"Musica salva em: {musica}")

    # -- 4. Montar Video -------------------------------------------------------
    print("\n[4/5] Montando video (Pillow + FFmpeg)...")
    video_final = montar_video(dados, img_a, img_b, musica)
    if not video_final:
              print("Erro na montagem do video.")
              return
          print(f"Video finalizado: {video_final}")

    # -- 5. Upload YouTube -----------------------------------------------------
    print("\n[5/5] Fazendo upload para o YouTube...")
    if not os.environ.get("YOUTUBE_REFRESH_TOKEN"):
              print("YOUTUBE_REFRESH_TOKEN nao configurado.")
              print("   Configure os secrets no GitHub para ativar o upload.")
              print(f"\n   Short salvo localmente em: {video_final}")
else:
          try:
                        from scripts.upload_youtube import upload_youtube
                        video_id = upload_youtube(video_final, dados)
                        print(f"\nSHORT PUBLICADO!")
                        print(f"   https://www.youtube.com/shorts/{video_id}")
except Exception as e:
            erro_str = str(e)
            print(f"\nUpload para o YouTube falhou: {erro_str[:200]}")
            if "invalid_client" in erro_str or "OAuth" in erro_str:
                              print("\n   SOLUCAO: As credenciais OAuth precisam ser do canal @futzona2026.")
                              print("   1. Acesse Google Cloud Console -> Credentials")
                              print("   2. Crie um OAuth 2.0 Client ID para o canal @futzona2026")
                              print("   3. Execute: python scripts/obter_token.py")
                              print("   4. Atualize os secrets YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET")
                              print("      e YOUTUBE_REFRESH_TOKEN no GitHub Actions")
                          print(f"\n   Short gerado com sucesso! Salvo no artefato do workflow.")
            print(f"   {video_final}")

    print("\n" + "="*65)
    print("PIPELINE CONCLUIDO COM SUCESSO!")
    print("="*65)

if __name__ == "__main__":
      main()
