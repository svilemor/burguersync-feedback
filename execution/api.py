"""
API Backend FastAPI - Avaliador de Feedback Hamburgueria BurguerSync Ourinhos
Coordena o fluxo de submissão de avaliações, integração de IA, persistência JSON e alertas.
"""
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path

from execution.storage import (
    init_db, save_feedback, get_feedbacks, mark_as_treated, get_stats
)
from execution.ai_analyzer import analyze_feedback
from execution.notifier import notify_manager_if_critical
from execution.config import BASE_DIR

# Inicializar Banco de Dados
init_db()

app = FastAPI(
    title="BurguerSync Ourinhos - Avaliador de Feedback API",
    description="Backend para coleta, análise de sentimento com IA, alertas gerenciais e dashboard administrativo.",
    version="1.0.0"
)

# Habilitar CORS para permitir chamadas do GitHub Pages e de origens locais
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas de Dados Pydantic
class FeedbackSubmission(BaseModel):
    nome: Optional[str] = Field(default="", description="Nome do cliente")
    contato: Optional[str] = Field(default="", description="Telefone / WhatsApp ou e-mail do cliente")
    pedido_id: Optional[str] = Field(default="", description="Código identificador do pedido (ex: OUR-102)")
    estrelas: Optional[int] = Field(default=5, ge=1, le=5, description="Nota de 1 a 5 estrelas")
    comentario: str = Field(..., min_length=2, description="Texto descritivo da avaliação")

class UpdateStatusRequest(BaseModel):
    tratado: bool = Field(..., description="Novo status de resolução do feedback")

# Endpoints da API REST
@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "sistema": "BurguerSync Feedback Analyzer",
        "cidade": "Ourinhos",
        "versao": "1.0.0"
    }

@app.post("/api/feedbacks", status_code=status.HTTP_201_CREATED)
def submit_feedback(dados: FeedbackSubmission):
    """
    Recebe o feedback do cliente, realiza a análise de sentimento e tags via IA,
    dispara alerta gerencial se o status for crítico e persiste no banco JSON.
    """
    # 1. Processamento via IA (Gemini ou contingência determinística)
    analise = analyze_feedback(dados.comentario, dados.estrelas)
    
    # 2. Estruturação do registro completo
    novo_registro = {
        "nome": dados.nome.strip() if dados.nome else "Cliente Ourinhos",
        "contato": dados.contato.strip() if dados.contato else "",
        "pedido_id": dados.pedido_id.strip() if dados.pedido_id else "N/A",
        "estrelas": dados.estrelas,
        "comentario": dados.comentario.strip(),
        "sentimento": analise.get("sentimento", "Neutro"),
        "tags": analise.get("tags", []),
        "resumo": analise.get("resumo", ""),
        "justificativa": analise.get("justificativa", ""),
        "provedor": analise.get("provedor", "Sistema"),
        "tratado": False
    }

    # 3. Alerta Automático em caso de feedback crítico
    alerta_info = notify_manager_if_critical(novo_registro)
    novo_registro["alerta_disparado"] = alerta_info.get("notificado", False)
    novo_registro["alerta_metodo"] = alerta_info.get("metodo", "nenhum")

    # 4. Gravação no Banco de Dados JSON estruturado
    registro_salvo = save_feedback(novo_registro)

    return {
        "sucesso": True,
        "mensagem": "Feedback recebido e processado com sucesso!",
        "feedback": registro_salvo
    }

@app.get("/api/feedbacks")
def list_feedbacks(
    sentimento: Optional[str] = Query(None, description="Filtrar por sentimento: Positivo, Neutro, Crítico"),
    tag: Optional[str] = Query(None, description="Filtrar por tag específica"),
    search: Optional[str] = Query(None, description="Busca textual livre"),
    tratado: Optional[bool] = Query(None, description="Filtrar por feedbacks tratados ou pendentes"),
    ordenacao: str = Query("desc", pattern="^(asc|desc)$", description="Ordenação por data de criação")
):
    """Retorna os feedbacks registrados com suporte a filtros e busca."""
    return get_feedbacks(
        filtro_sentimento=sentimento,
        filtro_tag=tag,
        search=search,
        tratado=tratado,
        ordenacao=ordenacao
    )

@app.patch("/api/feedbacks/{feedback_id}/status")
def update_feedback_status(feedback_id: str, payload: UpdateStatusRequest):
    """Atualiza o status de resolução (tratado/não tratado) de um feedback."""
    atualizado = mark_as_treated(feedback_id, payload.tratado)
    if not atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback com ID '{feedback_id}' não encontrado."
        )
    return {
        "sucesso": True,
        "mensagem": "Status atualizado com sucesso.",
        "feedback": atualizado
    }

@app.get("/api/stats")
def fetch_statistics():
    """Retorna dados agregados e métricas para o painel de controle."""
    return get_stats()

# Montar arquivos estáticos se o frontend existir localmente
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    @app.get("/")
    def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"mensagem": "BurguerSync API em execução. Frontend não encontrado."}

    @app.get("/dashboard")
    @app.get("/admin")
    def serve_dashboard():
        admin_file = FRONTEND_DIR / "dashboard.html"
        if admin_file.exists():
            return FileResponse(str(admin_file))
        return {"mensagem": "Dashboard não encontrado."}

    @app.get("/style.css")
    def serve_css():
        return FileResponse(str(FRONTEND_DIR / "style.css"), media_type="text/css")

    @app.get("/config.js")
    def serve_config_js():
        return FileResponse(str(FRONTEND_DIR / "config.js"), media_type="application/javascript")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
