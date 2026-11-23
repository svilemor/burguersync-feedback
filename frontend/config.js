/**
 * Configuração Dinâmica da API BurguerSync Ourinhos
 * Suporta execução local direta ou hospedagem estática via GitHub Pages.
 */
const Config = {
  getApiBaseUrl() {
    // 1. Verificar se há URL personalizada salva no localStorage
    const saved = localStorage.getItem('BURGUERSYNC_API_URL');
    if (saved && saved.trim()) {
      return saved.trim().replace(/\/+$/, '');
    }

    // 2. Se estiver rodando no mesmo host da API FastAPI
    if (window.location.port === '8000') {
      return window.location.origin;
    }

    // 3. Se estiver rodando localmente em outra porta (ex: Live Server)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }

    // 4. Default para GitHub Pages apontando para localhost ou túnel
    return 'http://localhost:8000';
  },

  setApiBaseUrl(url) {
    if (url) {
      localStorage.setItem('BURGUERSYNC_API_URL', url.trim().replace(/\/+$/, ''));
    } else {
      localStorage.removeItem('BURGUERSYNC_API_URL');
    }
  }
};
