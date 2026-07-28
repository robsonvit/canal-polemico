"""
gerar_conteudo.py
─────────────────
Usa a IA Groq (llama-3.3-70b) para pesquisar e gerar uma polêmica viral
do futebol com título chamativo, dois lados da polêmica para imagens e
comentários realistas que gerem engajamento.

Retorna um dict JSON com:
  titulo           — "MESSI ROUBOU A BOLA DE OURO DO NEYMAR EM 2015?"
  lado_a_nome      — "Messi"
  lado_b_nome      — "Neymar"
  termo_busca_a    — "Messi Barcelona 2015 camisa blaugrana"
  termo_busca_b    — "Neymar Bola de Ouro 2015 triste"
  termo_busca_b    — "Neymar Bola de Ouro 2015 triste"
  titulo_youtube   — título formatado para o YouTube (máx 100 chars)
  descricao_yt     — descrição para o vídeo (máx 400 chars)
  tags             — lista de tags para SEO
"""

import os
import json
import random
from groq import Groq

# ─────────────────────────────────────────────────────────────────────────────
# Exemplos de polêmicas para guiar o modelo (few-shot)
# ─────────────────────────────────────────────────────────────────────────────
EXEMPLOS_POLEMICA = [
    "Messi roubou a Bola de Ouro do Neymar em 2015?",
    "Cristiano Ronaldo deveria estar no Hall da Fama do futebol?",
    "Neymar foi expulso injustamente na Copa do Mundo 2018?",
    "Mbappé traiu o PSG para ir ao Real Madrid?",
    "Flamengo comprou árbitros na Copa do Brasil 2022?",
    "Vini Jr sofre racismo ou provoca demais?",
    "Ronaldo Fenômeno era melhor que Messi?",
    "Corinthians foi rebaixado por culpa do técnico ou dos jogadores?",
    "O VAR prejudicou o futebol brasileiro?",
    "Pelé ou Messi: quem é o maior de todos os tempos?",
]

# Times e jogadores para variar as polêmicas
PERSONAGENS = [
    "Messi", "Cristiano Ronaldo", "Neymar Jr", "Mbappé", "Vini Jr",
    "Ronaldo Fenômeno", "Pelé", "Zidane", "Ronaldinho", "Haaland",
    "Flamengo", "Corinthians", "Palmeiras", "São Paulo", "Grêmio",
    "Real Madrid", "Barcelona", "Manchester City", "PSG", "Liverpool",
    "Rodrygo", "Casemiro", "Endrick", "Pedro", "Gabigol",
]


def gerar_conteudo() -> dict:
    """
    Chama o Groq AI para gerar uma polêmica viral de futebol.
    Retorna dict com todos os dados necessários para montar o vídeo.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Seleciona alguns personagens aleatórios para inspirar o modelo
    personagens_amostra = random.sample(PERSONAGENS, k=6)
    exemplos_str = "\n".join(f"- {e}" for e in random.sample(EXEMPLOS_POLEMICA, k=4))

    prompt = f"""Você é um especialista em criar conteúdo viral de futebol para o canal CANAL POLÊMICO no YouTube.
Seu trabalho é criar UMA polêmica real e famosa do futebol que gere muita discussão, engajamento e comentários.

INSTRUÇÕES:
1. Escolha uma polêmica REAL e FAMOSA do futebol (pode ser sobre jogadores como: {', '.join(personagens_amostra)})
2. O TÍTULO deve ser uma pergunta polêmica que faça as pessoas quererem comentar (ex: "MESSI ROUBOU A BOLA DE OURO DO NEYMAR?")
3. Identifique os DOIS LADOS da polêmica (ex: Lado A = Messi, Lado B = Neymar)
3. Identifique os DOIS LADOS da polêmica (ex: Lado A = Messi, Lado B = Neymar)

Exemplos de polêmicas para inspirar (mas crie uma DIFERENTE):
{exemplos_str}

Responda APENAS com JSON válido no formato abaixo, sem markdown, sem texto antes ou depois:
{{
  "titulo": "TÍTULO POLÊMICO EM MAIÚSCULAS COM PONTO DE INTERROGAÇÃO?",
  "lado_a_nome": "Nome do Personagem/Time A",
  "lado_b_nome": "Nome do Personagem/Time B",
  "termo_busca_a": "termo específico para buscar imagem no Google do lado A",
  "termo_busca_b": "termo específico para buscar imagem no Google do lado B",
  "titulo_youtube": "Título formatado para YouTube com emojis (máx 90 chars)",
  "descricao_yt": "Descrição curta do vídeo para YouTube com hashtags de futebol (máx 350 chars)",
  "tags": ["futebol", "polemica", "shorts", "futzona"]
}}"""

    print("🤖 Consultando Groq AI para gerar polêmica viral...")

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=1500,
    )

    texto = resposta.choices[0].message.content.strip()

    # Remove eventuais blocos de código markdown
    if "```json" in texto:
        texto = texto.split("```json")[1].split("```")[0].strip()
    elif "```" in texto:
        texto = texto.split("```")[1].split("```")[0].strip()

    dados = json.loads(texto)

    # Garantias de formato
    dados["titulo"] = dados.get("titulo", "MESSI OU CRISTIANO: QUEM É O MAIOR?").upper()

    # Garante tags essenciais
    tags_base = ["futebol", "polemica", "shorts", "futzona", "futebol2026",
                 "Shorts", "#futebol", "#polemica"]
    tags_existentes = dados.get("tags", [])
    dados["tags"] = list(set(tags_existentes + tags_base))[:25]

    print(f"✅ Polêmica gerada: {dados['titulo']}")
    print(f"   Lado A: {dados['lado_a_nome']} | Lado B: {dados['lado_b_nome']}")

    return dados


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    dados = gerar_conteudo()
    print(json.dumps(dados, ensure_ascii=False, indent=2))
