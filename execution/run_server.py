"""
Script de Inicialização do Servidor Uvicorn
Inicia a API FastAPI e o servidor de arquivos estáticos na porta 8000.
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Tratamento para evitar problemas de codificação no console Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"[INFO] Iniciando BurguerSync Ourinhos API Server em http://localhost:{port}")
    print(f"[INFO] Documentação Swagger disponível em: http://localhost:{port}/docs")
    
    uvicorn.run("execution.api:app", host=host, port=port, reload=False)
