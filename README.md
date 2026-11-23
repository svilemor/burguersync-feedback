# 🍔 BurguerSync Ourinhos - Avaliador de Feedback Inteligente

Sistema web completo para coleta, análise de sentimento com IA (Google Gemini) e gestão operacional de avaliações de clientes de uma hamburgueria artesanal em Ourinhos/SP.

---

## 🏛️ Arquitetura em 3 Camadas

O projeto adere rigorosamente à arquitetura descrita em `directive/projeto.md`:

1. **Layer 1 (Diretiva):** `directive/projeto.md` definindo as regras de negócio, critérios de classificação (Positivo, Neutro, Crítico) e protocolos de alerta.
2. **Layer 2 (Orquestração):** Coordenação de fluxo entre frontend, IA e persistência com validações e resiliência contínua.
3. **Layer 3 (Execução):** Scripts determinísticos em Python na pasta `execution/`:
   - `execution/storage.py`: Operações atômicas de I/O no banco de dados JSON (`data/feedbacks.json`).
   - `execution/ai_analyzer.py`: Integração com a API do Google Gemini com tentativas exponenciais e fallback determinístico local.
   - `execution/notifier.py`: Disparo automático de alertas para feedbacks críticos via SMTP com fallback em `.tmp/alerts.log`.
   - `execution/api.py`: Backend REST em FastAPI com CORS e documentação interativa OpenAPI/Swagger.
   - `execution/run_server.py`: Inicializador do servidor na porta 8000.

---

## 🚀 Funcionalidades

- **📱 Formulário Público do Cliente:**
  - Identificação completa (Nome, WhatsApp/Contato, Número do Pedido).
  - Classificação visual de 1 a 5 estrelas.
  - Avaliação descritiva em texto aberto.
  - Análise em tempo real pela IA.

- **📊 Dashboard Administrativo do Gerente:**
  - Painel com indicadores chave (Total, Positivos, Neutros, Críticos, Média de Estrelas, Taxa de Resolução).
  - Alerta visual no topo em caso de crises pendentes de atendimento.
  - Nuvem interativa de tags extraídas pela IA (Sabor, Entrega, Atendimento, Embalagem, Preço, etc.).
  - Filtros avançados por sentimento, status (pendente/tratado), tags e busca textual.
  - Checkbox interativo com persistência para marcar atendimentos como tratados.
  - Botão com link direto para acionar o cliente pelo WhatsApp.

- **🚨 Protocolo de Resiliência e Auto-Recuperação (Self-Annealing):**
  - **Suporte ao Gemini:** Configurado para `gemini-3.6-flash` e `gemini-3.8-flash`.
  - **Fallback Determinístico Local:** Caso haja pico de tráfego, erro 503 ou falta de internet/cota, o motor léxico local assume a classificação imediatamente sem perda de requisições.
  - **Resguardo de Alertas Críticos:** Gravação garantida em `.tmp/alerts.log` caso credenciais SMTP não estejam configuradas.

---

## 🛠️ Como Executar Localmente

### 1. Pré-requisitos
- Python 3.12+ instalado.

### 2. Instalação das Dependências
```bash
python -m venv .venv
# No Windows:
.\.venv\Scripts\activate
# No Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuração do Arquivo `.env`
Crie ou edite o arquivo `.env` na raiz do projeto com as chaves:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
GITHUB_PERSONAL_TOKEN=seu_token_github_aqui

# Opcional para envio real de e-mails via SMTP:
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=seu_email@gmail.com
# SMTP_PASSWORD=sua_senha_de_app
# MANAGER_EMAIL=gerente.ourinhos@burguersync.com
```

### 4. Executar o Servidor FastAPI
```bash
python -m execution.run_server
```

Acesse no seu navegador:
- **Formulário do Cliente:** [http://localhost:8000/](http://localhost:8000/)
- **Painel Administrativo:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Documentação da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 Hospedagem no GitHub Pages

O frontend estático está disponível na pasta `docs/` e `frontend/`, pronto para publicação imediata no GitHub Pages da conta **svilemor**:
- **Repositório:** [https://github.com/svilemor/burguersync-feedback](https://github.com/svilemor/burguersync-feedback)
- **Página do Cliente:** [https://svilemor.github.io/burguersync-feedback/docs/index.html](https://svilemor.github.io/burguersync-feedback/docs/index.html)
- **Painel do Gerente:** [https://svilemor.github.io/burguersync-feedback/docs/dashboard.html](https://svilemor.github.io/burguersync-feedback/docs/dashboard.html)
