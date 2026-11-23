"""
Módulo de Notificação e Alerta Automático para Gestores
Gerencia o disparo de alertas por e-mail (SMTP) com fallback automático para gravação em log.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
from execution.config import (
    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, 
    SMTP_USE_TLS, MANAGER_EMAIL, ALERTS_LOG_FILE, TMP_DIR
)

def _format_alert_body(feedback: Dict[str, Any]) -> str:
    """Gera o corpo do e-mail/alerta em texto formatado."""
    return f"""====================================================
🚨 ALERTA CRÍTICO DE SATISFAÇÃO - BURGUERSYNC OURINHOS
====================================================
Data/Hora: {feedback.get('data_criacao', datetime.now().isoformat())}
ID do Registro: {feedback.get('id', 'N/A')}

DADOS DO CLIENTE:
- Nome: {feedback.get('nome') or 'Não informado'}
- Contato: {feedback.get('contato') or 'Não informado'}
- Pedido: #{feedback.get('pedido_id') or 'N/A'}
- Nota em Estrelas: {feedback.get('estrelas') or 'Não avaliado'} / 5

AVALIAÇÃO DO CLIENTE:
"{feedback.get('comentario', 'Sem comentário')}"

DIAGNÓSTICO DA IA:
- Sentimento: {feedback.get('sentimento', 'Crítico')}
- Tags: {', '.join(feedback.get('tags', []))}
- Resumo: {feedback.get('resumo', 'N/A')}
- Justificativa: {feedback.get('justificativa', 'N/A')}
- Motor de Análise: {feedback.get('provedor', 'N/A')}

AÇÃO RECOMENDADA:
Entrar em contato imediatamente com o cliente para contenção da crise e reposição/compensação do pedido.
====================================================
"""

def _send_smtp_email(subject: str, body: str) -> bool:
    """Tenta enviar e-mail utilizando as credenciais SMTP configuradas."""
    if not (SMTP_SERVER and SMTP_USER and SMTP_PASSWORD):
        return False
        
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = MANAGER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    server = None
    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            if SMTP_USE_TLS:
                server.starttls()
                
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        return True
    except Exception as e:
        print(f"[AVISO] Falha ao enviar e-mail via SMTP ({e}). Recorrendo ao fallback em log.")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

def _record_alert_fallback(body: str) -> None:
    """Grava o alerta no arquivo temporário .tmp/alerts.log."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DISPARO DE ALERTA GERENCIAL:\n")
        f.write(body)
        f.write("\n")

def notify_manager_if_critical(feedback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifica se o feedback é 'Crítico'. Se for, dispara o alerta por SMTP ou fallback em log.
    Garante que nenhum alerta seja perdido.
    """
    sentimento = feedback.get("sentimento", "")
    if sentimento != "Crítico":
        return {
            "notificado": False,
            "motivo": "Feedback não é crítico",
            "metodo": "nenhum"
        }

    body = _format_alert_body(feedback)
    subject = f"🚨 [CRISE] Feedback Crítico - Pedido #{feedback.get('pedido_id', 'Geral')} ({feedback.get('nome', 'Cliente')})"
    
    # Tentativa de envio real por SMTP
    sucesso_smtp = _send_smtp_email(subject, body)
    
    if sucesso_smtp:
        print(f"[SUCESSO] Alerta crítico enviado via SMTP para {MANAGER_EMAIL}.")
        metodo = "smtp"
    else:
        # Fallback determinístico em arquivo
        _record_alert_fallback(body)
        print(f"[AVISO] Alerta crítico gravado com sucesso no fallback (.tmp/alerts.log).")
        metodo = "fallback_log"

    return {
        "notificado": True,
        "metodo": metodo,
        "destinatario": MANAGER_EMAIL if metodo == "smtp" else str(ALERTS_LOG_FILE),
        "timestamp": datetime.now().isoformat()
    }
