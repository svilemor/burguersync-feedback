"""
Módulo de Configuração do Sistema Avaliador de Feedback
Gerencia variáveis de ambiente, caminhos de diretórios e fallbacks.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis do .env
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# Diretórios operacionais
TMP_DIR = BASE_DIR / ".tmp"
DATA_DIR = BASE_DIR / "data"
DATABASE_FILE = DATA_DIR / "feedbacks.json"
ALERTS_LOG_FILE = TMP_DIR / "alerts.log"

# Garantir existência dos diretórios necessários
TMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Chaves e Serviços
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GITHUB_PERSONAL_TOKEN = os.getenv("GITHUB_PERSONAL_TOKEN", "").strip()

# Configurações SMTP para Alertas
SMTP_SERVER = os.getenv("SMTP_SERVER", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else 587
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "gerente.ourinhos@burguersync.com").strip()

# Modelos Gemini suportados em ordem de preferência
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]
