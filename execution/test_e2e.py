"""
Script de Teste End-to-End Automatizado
Testa todas as camadas do sistema: FastAPI, IA Gemini/Fallback, Armazenamento JSON e Notificações.
"""
from fastapi.testclient import TestClient
from execution.api import app
from execution.config import TMP_DIR, ALERTS_LOG_FILE, DATABASE_FILE
import json

client = TestClient(app)

def run_e2e_tests():
    print("=" * 60)
    print("🧪 INICIANDO TESTES END-TO-END BURGUERSYNC OURINHOS")
    print("=" * 60)

    # 1. Testar Health Check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check falhou: {res_health.text}"
    print("[PASS] 1. Health check da API: OK")

    # 2. Submeter Feedback Positivo
    payload_pos = {
        "nome": "Mariana Souza",
        "contato": "(14) 99777-1122",
        "pedido_id": "OUR-5021",
        "estrelas": 5,
        "comentario": "Melhor hambúrguer de Ourinhos! A maionese temperada e a carne no ponto perfeito, entrega muito antes do previsto."
    }
    res_pos = client.post("/api/feedbacks", json=payload_pos)
    assert res_pos.status_code == 201, f"Falha na criacao de feedback positivo: {res_pos.text}"
    data_pos = res_pos.json()["feedback"]
    assert data_pos["sentimento"] == "Positivo", f"Esperado Positivo, obtido: {data_pos['sentimento']}"
    assert data_pos["alerta_disparado"] is False, "Alerta critico nao deveria disparar para positivo"
    print(f"[PASS] 2. Feedback Positivo processado com sucesso. Tags: {data_pos['tags']}")

    # 3. Submeter Feedback Neutro
    payload_neu = {
        "nome": "Rodrigo Almeida",
        "contato": "(14) 98888-3344",
        "pedido_id": "OUR-5022",
        "estrelas": 3,
        "comentario": "O lanche é gostoso, mas achei que a quantidade de batata frita poderia ser um pouco maior pelo preço cobrado."
    }
    res_neu = client.post("/api/feedbacks", json=payload_neu)
    assert res_neu.status_code == 201, f"Falha na criacao de feedback neutro: {res_neu.text}"
    data_neu = res_neu.json()["feedback"]
    print(f"[PASS] 3. Feedback Neutro processado. Sentimento: {data_neu['sentimento']} | Tags: {data_neu['tags']}")

    # 4. Submeter Feedback Crítico (Crise)
    payload_crit = {
        "nome": "Fernanda Lima",
        "contato": "(14) 99111-5566",
        "pedido_id": "OUR-5023",
        "estrelas": 1,
        "comentario": "Péssima experiência! O pedido atrasou 1 hora e 20 minutos, veio totalmente gelado, refrigerante quente e o lanche errado sem queijo. Exijo meu dinheiro de volta!"
    }
    res_crit = client.post("/api/feedbacks", json=payload_crit)
    assert res_crit.status_code == 201, f"Falha na criacao de feedback critico: {res_crit.text}"
    data_crit = res_crit.json()["feedback"]
    assert data_crit["sentimento"] == "Crítico", f"Esperado Crítico, obtido: {data_crit['sentimento']}"
    assert data_crit["alerta_disparado"] is True, "Alerta critico DEVE disparar para sentimento Crítico"
    crit_id = data_crit["id"]
    print(f"[PASS] 4. Feedback Crítico processado. Alerta disparado com sucesso! Método: {data_crit['alerta_metodo']}")

    # 5. Validar arquivo de alertas gerenciais (.tmp/alerts.log)
    assert ALERTS_LOG_FILE.exists(), "Arquivo .tmp/alerts.log deve existir!"
    with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "Fernanda Lima" in log_content, "Nome da cliente deve constar no alerta"
    assert "OUR-5023" in log_content, "Número do pedido deve constar no alerta"
    assert "ALERTA CRÍTICO DE SATISFAÇÃO" in log_content, "Cabeçalho do alerta deve constar no log"
    print("[PASS] 5. Verificação de integridade do arquivo de alertas gerenciais (.tmp/alerts.log): OK")

    # 6. Testar filtros na API
    # Filtro apenas Positivo
    res_f_pos = client.get("/api/feedbacks?sentimento=Positivo")
    items_pos = res_f_pos.json()
    assert all(i["sentimento"] == "Positivo" for i in items_pos), "Filtro positivo retornou itens incorretos"
    print(f"[PASS] 6. Filtro por sentimento (Positivo): {len(items_pos)} encontrados")

    # Filtro apenas Crítico
    res_f_crit = client.get("/api/feedbacks?sentimento=Crítico")
    items_crit = res_f_crit.json()
    assert all(i["sentimento"] == "Crítico" for i in items_crit), "Filtro crítico retornou itens incorretos"
    print(f"[PASS] 7. Filtro por sentimento (Crítico): {len(items_crit)} encontrados")

    # Busca textual
    res_search = client.get("/api/feedbacks?search=Fernanda")
    items_search = res_search.json()
    assert any(i["nome"] == "Fernanda Lima" for i in items_search), "Busca por 'Fernanda' deve retornar a cliente"
    print(f"[PASS] 8. Busca textual por termo: OK ({len(items_search)} resultado)")

    # 7. Testar Marcação como Tratado (PATCH)
    res_patch = client.patch(f"/api/feedbacks/{crit_id}/status", json={"tratado": True})
    assert res_patch.status_code == 200, f"Falha no PATCH: {res_patch.text}"
    assert res_patch.json()["feedback"]["tratado"] is True, "Status tratado deve ser True"
    print("[PASS] 9. Atualização de status para 'Tratado': OK")

    # 8. Testar Métricas e Estatísticas
    res_stats = client.get("/api/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total"] >= 3, "Total de feedbacks deve ser >= 3"
    assert stats["positivos"] >= 1, "Positivos >= 1"
    assert stats["criticos"] >= 1, "Críticos >= 1"
    assert stats["tratados"] >= 1, "Tratados >= 1"
    assert "tags_contagem" in stats, "Contagem de tags deve existir"
    print(f"[PASS] 10. Estatísticas consolidadas da gerência: {stats}")

    print("=" * 60)
    print("🎉 TODOS OS 10 TESTES END-TO-END PASSARAM COM 100% DE SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_tests()
