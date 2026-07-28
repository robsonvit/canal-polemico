"""
obter_token.py
──────────────
Script para gerar o YOUTUBE_REFRESH_TOKEN do canal @futzona2026.

Execute UMA VEZ na sua máquina local:
  python scripts/obter_token.py

Pré-requisito: ter o client_secret.json do canal @futzona2026
(baixado do Google Cloud Console → Credentials → OAuth 2.0 Client IDs)

Depois copie o refresh_token e configure nos secrets do GitHub:
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configurações — preencha com os dados do canal @futzona2026
# ─────────────────────────────────────────────────────────────────────────────

# Opção 1: coloque o client_secret.json do canal @futzona2026 na raiz
CLIENT_SECRET_FILE = "client_secret_futzona.json"

# Opção 2: coloque diretamente aqui (se não tiver o arquivo)
CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

REDIRECT_URI  = "http://localhost:8080"
SCOPE         = "https://www.googleapis.com/auth/youtube.upload"
AUTH_URL      = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL     = "https://oauth2.googleapis.com/token"

# ─────────────────────────────────────────────────────────────────────────────


def _carregar_credenciais():
    """Carrega client_id e client_secret do arquivo ou variáveis."""
    global CLIENT_ID, CLIENT_SECRET

    if os.path.exists(CLIENT_SECRET_FILE):
        with open(CLIENT_SECRET_FILE) as f:
            dados = json.load(f)
        chave = "installed" if "installed" in dados else "web"
        CLIENT_ID     = dados[chave]["client_id"]
        CLIENT_SECRET = dados[chave]["client_secret"]
        print(f"✅ Credenciais carregadas de: {CLIENT_SECRET_FILE}")
    elif CLIENT_ID and CLIENT_SECRET:
        print("✅ Credenciais carregadas das variáveis de ambiente")
    else:
        print("\n❌ ERRO: Credenciais não encontradas!")
        print(f"\nCrie o arquivo '{CLIENT_SECRET_FILE}' com o OAuth do canal @futzona2026")
        print("(Baixe em: Google Cloud Console → APIs → Credentials → seu OAuth Client)")
        print("\nOU configure as variáveis de ambiente:")
        print("  set YOUTUBE_CLIENT_ID=seu_client_id")
        print("  set YOUTUBE_CLIENT_SECRET=seu_client_secret")
        raise SystemExit(1)


class _CallbackHandler(BaseHTTPRequestHandler):
    """Servidor HTTP local para capturar o código de autorização."""
    code = None

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            _CallbackHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
            <html><body style="font-family:sans-serif;text-align:center;padding:50px">
            <h1>&#10003; Autorizado com sucesso!</h1>
            <p>Volte ao terminal para copiar o refresh_token.</p>
            <script>setTimeout(()=>window.close(),2000)</script>
            </body></html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, *args):
        pass  # Silencia os logs do servidor


def obter_refresh_token():
    """Abre o browser, faz o fluxo OAuth e retorna o refresh_token."""
    _carregar_credenciais()

    # 1. Monta URL de autorização
    auth_params = (
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    url = AUTH_URL + auth_params

    print(f"\n🌐 Abrindo o browser para autorização...")
    print(f"   Se não abrir automaticamente, acesse: {url[:80]}...")
    webbrowser.open(url)

    # 2. Aguarda callback no localhost:8080
    print("\n⏳ Aguardando autorização no browser...")
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    server.handle_request()

    code = _CallbackHandler.code
    if not code:
        print("\n❌ Nenhum código de autorização recebido.")
        raise SystemExit(1)

    print("✅ Código de autorização recebido!")

    # 3. Troca o código pelo refresh_token
    resp = requests.post(TOKEN_URL, data={
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    resp.raise_for_status()
    tokens = resp.json()

    refresh_token = tokens.get("refresh_token", "")

    if not refresh_token:
        print("\n❌ Refresh token não recebido. Tente novamente.")
        raise SystemExit(1)

    # 4. Salva em arquivo local
    saida = {
        "refresh_token":  refresh_token,
        "client_id":      CLIENT_ID,
        "client_secret":  CLIENT_SECRET,
    }
    with open("refresh_token_futzona.json", "w") as f:
        json.dump(saida, f, indent=2)

    print("\n" + "═"*60)
    print("  ✅ TOKENS GERADOS COM SUCESSO!")
    print("═"*60)
    print(f"\n  Configure estes 3 secrets no GitHub:")
    print(f"\n  YOUTUBE_CLIENT_ID:")
    print(f"  {CLIENT_ID}")
    print(f"\n  YOUTUBE_CLIENT_SECRET:")
    print(f"  {CLIENT_SECRET}")
    print(f"\n  YOUTUBE_REFRESH_TOKEN:")
    print(f"  {refresh_token}")
    print("\n" + "═"*60)
    print(f"\n  Arquivo salvo: refresh_token_futzona.json")
    print("  (NÃO faça commit deste arquivo!)")

    return refresh_token


if __name__ == "__main__":
    obter_refresh_token()
