"""
Módulo de Integração com Google Gemini (Análise de Sentimentos e Extração de Tags)
Implementa retries com backoff exponencial e contingência determinística local.
"""
import os
import json
import time
import requests
from typing import Dict, Any, List
from execution.config import GEMINI_API_KEY, GEMINI_MODELS, TMP_DIR

SYSTEM_INSTRUCTION = """Você é um especialista em análise de satisfação de clientes de hamburguerias artesanais.
Sua missão é analisar o feedback recebido e retornar estritamente um objeto JSON com:
- "sentimento": escolha exatamente um entre "Positivo", "Neutro" ou "Crítico".
  * "Crítico": qualquer insatisfação severa, comida fria, crua ou queimada, atraso excessivo, grosseria, erro no pedido, intoxicação, higiene ou frustração grave.
  * "Neutro": observações gerais, sugestões construtivas sem tom exaltado, ou avaliações medianas (ex: 3 estrelas).
  * "Positivo": elogios ao sabor, agilidade, atendimento, embalagem ou experiência agradável.
- "tags": lista com 1 a 4 tags aplicáveis dentre: ["Sabor", "Entrega", "Atendimento", "Preço", "Embalagem", "Tempo de Espera", "Higiene", "Montagem do Lanche", "Batata Frita", "Bebida", "Geral"].
- "resumo": resumo executivo de 1 frase destacando o ponto central.
- "justificativa": breve explicação técnica do porquê da classificação atribuída.
"""

def _analyze_with_gemini_api(comentario: str, estrelas: int = None) -> Dict[str, Any]:
    """Tenta realizar a análise via API do Google Gemini com fallback entre modelos."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada no ambiente.")

    prompt = f"""Analise o seguinte feedback de cliente de hamburgueria:
Comentário do Cliente: "{comentario}"
Nota em estrelas (se fornecida): {estrelas if estrelas is not None else "Não informada"}

Responda ESTRITAMENTE em formato JSON com o seguinte schema:
{{
  "sentimento": "Positivo | Neutro | Crítico",
  "tags": ["Tag1", "Tag2"],
  "resumo": "Resumo em 1 frase",
  "justificativa": "Explicação do sentimento e tags"
}}"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_INSTRUCTION + "\n\n" + prompt}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    }

    # Salvar log temporário de requisição
    req_log_file = TMP_DIR / "gemini_last_request.json"
    with open(req_log_file, "w", encoding="utf-8") as f:
        json.dump({"comentario": comentario, "estrelas": estrelas, "timestamp": time.time()}, f, ensure_ascii=False, indent=2)

    last_error = None

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        # 3 tentativas com backoff exponencial
        for attempt in range(1, 4):
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        
                        # Salvar resposta temporária
                        resp_log_file = TMP_DIR / "gemini_last_response.json"
                        with open(resp_log_file, "w", encoding="utf-8") as f:
                            f.write(raw_text)

                        parsed = json.loads(raw_text)
                        
                        # Normalizar campos
                        sentimento = str(parsed.get("sentimento", "Neutro")).strip().capitalize()
                        if sentimento not in ["Positivo", "Neutro", "Crítico"]:
                            if "crit" in sentimento.lower():
                                sentimento = "Crítico"
                            elif "pos" in sentimento.lower():
                                sentimento = "Positivo"
                            else:
                                sentimento = "Neutro"

                        tags = parsed.get("tags", [])
                        if not isinstance(tags, list):
                            tags = [str(tags)]

                        return {
                            "sentimento": sentimento,
                            "tags": tags,
                            "resumo": parsed.get("resumo", comentario[:100]),
                            "justificativa": parsed.get("justificativa", "Classificação gerada via Gemini API"),
                            "provedor": f"Gemini ({model})",
                            "status": "sucesso"
                        }
                elif response.status_code == 429:
                    # Rate limit - aguardar antes de retentar
                    time.sleep(1.5 * attempt)
                    continue
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            except Exception as e:
                last_error = str(e)
                time.sleep(1.0 * attempt)

    raise RuntimeError(f"Falha em todos os modelos Gemini. Último erro: {last_error}")

def _fallback_deterministic_analysis(comentario: str, estrelas: int = None) -> Dict[str, Any]:
    """
    Contingência determinística local caso a API do Gemini esteja sem cota ou indisponível.
    Utiliza análise léxica com termos de domínio de hamburgueria.
    """
    texto = comentario.lower()
    
    termos_criticos = [
        "frio", "fria", "demorou", "atraso", "atrasado", "horrível", "pessimo", "péssimo",
        "ruim", "cru", "crua", "queimado", "queimada", "errado", "faltou", "sujo", "suja",
        "barata", "cabelo", "gosto ruim", "seco", "seca", "nausea", "estragado", "mofado",
        "decepcionado", "decepção", "nunca mais", "vergonha", "gelado"
    ]
    
    termos_positivos = [
        "excelente", "ótimo", "otimo", "delicioso", "maravilhoso", "perfeito", "saboroso",
        "parabéns", "parabens", "rápido", "rapido", "quentinho", "quente", "crocante",
        "melhor", "top", "muito bom", "adorei", "amei", "recomendo", "suculento", "atencioso"
    ]
    
    pontos_criticos = sum(1 for termo in termos_criticos if termo in texto)
    pontos_positivos = sum(1 for termo in termos_positivos if termo in texto)
    
    # Considerar estrelas caso informadas
    if estrelas is not None:
        if estrelas <= 2:
            pontos_criticos += 3
        elif estrelas >= 4:
            pontos_positivos += 2

    if pontos_criticos > pontos_positivos or (estrelas is not None and estrelas <= 2):
        sentimento = "Crítico"
    elif pontos_positivos > pontos_criticos or (estrelas is not None and estrelas >= 4):
        sentimento = "Positivo"
    else:
        sentimento = "Neutro"

    # Extração de tags por domínio
    tags: List[str] = []
    if any(k in texto for k in ["entrega", "motoboy", "demor", "atras", "espera", "tempo", "chegou"]):
        tags.append("Entrega")
    if any(k in texto for k in ["sabor", "gosto", "carne", "queijo", "molho", "bacon", "tempero", "delici", "salgado", "doce"]):
        tags.append("Sabor")
    if any(k in texto for k in ["atendimento", "atendente", "educa", "garçom", "whatsapp", "suporte", "equipe"]):
        tags.append("Atendimento")
    if any(k in texto for k in ["embalagem", "sacola", "embrulho", "vazou", "amassado", "caixa"]):
        tags.append("Embalagem")
    if any(k in texto for k in ["preço", "preco", "caro", "barato", "valor", "promoção", "cupom"]):
        tags.append("Preço")
    if any(k in texto for k in ["batata", "frita", "fritas", "crocante", "murcha"]):
        tags.append("Batata Frita")
        
    if not tags:
        tags.append("Geral")

    return {
        "sentimento": sentimento,
        "tags": tags,
        "resumo": f"Feedback classificado localmente como {sentimento}",
        "justificativa": "Análise determinística de contingência local por regras léxicas e estrelas",
        "provedor": "Contingência Determinística Local",
        "status": "fallback"
    }

def analyze_feedback(comentario: str, estrelas: int = None) -> Dict[str, Any]:
    """
    Função principal de análise. Tenta a API do Gemini com fallback automático
    para a contingência determinística local em caso de qualquer falha.
    """
    if not comentario or not comentario.strip():
        return {
            "sentimento": "Neutro",
            "tags": ["Geral"],
            "resumo": "Feedback vazio recebido",
            "justificativa": "Sem conteúdo textual suficiente",
            "provedor": "Sistema",
            "status": "vazio"
        }

    try:
        return _analyze_with_gemini_api(comentario, estrelas)
    except Exception as err:
        print(f"[AVISO] Falha ao consultar Gemini API ({err}). Ativando contingência determinística local.")
        return _fallback_deterministic_analysis(comentario, estrelas)
