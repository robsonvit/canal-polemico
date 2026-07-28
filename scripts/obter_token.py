import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json

# Escopos necessarios para ler/gravar no YouTube
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def main():
      print("=================================================================")
      print("GERADOR DE REFRESH TOKEN DO YOUTUBE OAUTH 2.0")
      print("=================================================================")

    # Procurar por client_secret.json na pasta raiz ou em scripts
      secrets_file = "client_secret.json"
      if not os.path.exists(secrets_file):
                secrets_file = os.path.join("scripts", "client_secret.json")

    if not os.path.exists(secrets_file):
              print("Erro: Arquivo client_secret.json nao encontrado!")
              print("   Para obter o refresh token, voce precisa baixar as credenciais OAuth")
              print("   do Google Cloud Console para o canal @futzona2026 e salvar como")
              print("   client_secret.json na raiz do projeto.")
              sys.exit(1)

    print(f"Usando credenciais de: {secrets_file}")

    # Configurar o fluxo de autenticacao local
    try:
              flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
              # Executa o servidor local para pegar o codigo de autorizacao
              print("\nUm navegador sera aberto para voce fazer login no canal @futzona2026.")
              print("Se estiver rodando sem interface grafica, siga o link exibido no terminal.")
              creds = flow.run_local_server(port=8080, prompt="select_account")

        # Salvar as credenciais obtidas
              token_data = {
                  "token": creds.token,
                  "refresh_token": creds.refresh_token,
                  "token_uri": creds.token_uri,
                  "client_id": creds.client_id,
                  "client_secret": creds.client_secret,
                  "scopes": creds.scopes
              }

        output_file = "refresh_token.json"
        with open(output_file, "w") as f:
                      json.dump(token_data, f, indent=4)

        print("\n" + "="*65)
        print("AUTENTICACAO REALIZADA COM SUCESSO!")
        print("="*65)
        print(f"Os dados de autenticacao foram salvos em: {output_file}")
        print("\nCopie os seguintes valores para os Secrets do seu Repositorio no GitHub:")
        print(f"   - YOUTUBE_CLIENT_ID: {creds.client_id}")
        print(f"   - YOUTUBE_CLIENT_SECRET: {creds.client_secret}")
        print(f"   - YOUTUBE_REFRESH_TOKEN: {creds.refresh_token}")
        print("="*65)

except Exception as e:
        print(f"Erro durante o fluxo de autenticacao: {e}")

if __name__ == "__main__":
      main()
