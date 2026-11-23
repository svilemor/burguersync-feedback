"""
Módulo de Armazenamento Determinístico (JSON)
Responsável por todas as operações de I/O no banco de dados feedbacks.json.
"""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from execution.config import DATABASE_FILE, DATA_DIR

def init_db() -> None:
    """Garante a inicialização do arquivo de banco de dados se não existir."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATABASE_FILE.exists():
        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def _read_all() -> List[Dict[str, Any]]:
    """Lê todos os feedbacks do arquivo JSON."""
    init_db()
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _write_all(feedbacks: List[Dict[str, Any]]) -> None:
    """Grava todos os feedbacks atomicamente no arquivo JSON."""
    init_db()
    temp_file = DATABASE_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    temp_file.replace(DATABASE_FILE)

def save_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insere um novo feedback com metadados estruturados.
    """
    feedbacks = _read_all()
    
    # Gerar ID único e timestamp caso não existam
    if "id" not in feedback_data or not feedback_data["id"]:
        feedback_data["id"] = str(uuid.uuid4())
    
    if "data_criacao" not in feedback_data or not feedback_data["data_criacao"]:
        feedback_data["data_criacao"] = datetime.now().isoformat()
    
    # Garantir status 'tratado' padrão
    if "tratado" not in feedback_data:
        feedback_data["tratado"] = False
        
    feedbacks.append(feedback_data)
    _write_all(feedbacks)
    return feedback_data

def get_feedbacks(
    filtro_sentimento: Optional[str] = None,
    filtro_tag: Optional[str] = None,
    search: Optional[str] = None,
    tratado: Optional[bool] = None,
    ordenacao: str = "desc"
) -> List[Dict[str, Any]]:
    """
    Retorna a lista de feedbacks aplicando filtros opcionais e ordenação.
    """
    feedbacks = _read_all()
    resultado = feedbacks

    # Filtro por sentimento (Positivo, Neutro, Crítico)
    if filtro_sentimento and filtro_sentimento.lower() != "todos":
        resultado = [
            f for f in resultado 
            if f.get("sentimento", "").lower() == filtro_sentimento.lower()
        ]

    # Filtro por tag
    if filtro_tag and filtro_tag.lower() != "todas":
        tag_alvo = filtro_tag.lower()
        resultado = [
            f for f in resultado
            if any(t.lower() == tag_alvo for t in f.get("tags", []))
        ]

    # Filtro por status tratado
    if tratado is not None:
        resultado = [f for f in resultado if f.get("tratado") == tratado]

    # Busca textual (nome, comentario, tags, pedido_id)
    if search:
        termo = search.lower().strip()
        resultado = [
            f for f in resultado
            if (
                termo in f.get("nome", "").lower() or
                termo in f.get("comentario", "").lower() or
                termo in f.get("pedido_id", "").lower() or
                termo in f.get("contato", "").lower() or
                any(termo in t.lower() for t in f.get("tags", []))
            )
        ]

    # Ordenação por data_criacao
    reverse = (ordenacao.lower() == "desc")
    resultado = sorted(
        resultado, 
        key=lambda x: x.get("data_criacao", ""), 
        reverse=reverse
    )

    return resultado

def mark_as_treated(feedback_id: str, status: bool = True) -> Optional[Dict[str, Any]]:
    """Atualiza o status de 'tratado' de um feedback pelo ID."""
    feedbacks = _read_all()
    item_atualizado = None
    
    for f in feedbacks:
        if f.get("id") == feedback_id:
            f["tratado"] = status
            f["data_tratamento"] = datetime.now().isoformat() if status else None
            item_atualizado = f
            break
            
    if item_atualizado:
        _write_all(feedbacks)
        
    return item_atualizado

def get_stats() -> Dict[str, Any]:
    """Calcula estatísticas consolidadas para o Dashboard Administrativo."""
    feedbacks = _read_all()
    total = len(feedbacks)
    
    positivos = sum(1 for f in feedbacks if f.get("sentimento") == "Positivo")
    neutros = sum(1 for f in feedbacks if f.get("sentimento") == "Neutro")
    criticos = sum(1 for f in feedbacks if f.get("sentimento") == "Crítico")
    tratados = sum(1 for f in feedbacks if f.get("tratado") is True)
    pendentes = total - tratados
    
    # Contagem de tags
    tag_counter: Dict[str, int] = {}
    for f in feedbacks:
        for t in f.get("tags", []):
            if t:
                tag_counter[t] = tag_counter.get(t, 0) + 1
                
    # Média de estrelas (quando presente)
    estrelas = [f.get("estrelas") for f in feedbacks if isinstance(f.get("estrelas"), (int, float))]
    media_estrelas = round(sum(estrelas) / len(estrelas), 2) if estrelas else 0.0

    return {
        "total": total,
        "positivos": positivos,
        "neutros": neutros,
        "criticos": criticos,
        "tratados": tratados,
        "pendentes": pendentes,
        "media_estrelas": media_estrelas,
        "tags_contagem": tag_counter,
        "taxa_resolucao": round((tratados / total * 100), 1) if total > 0 else 0.0
    }
