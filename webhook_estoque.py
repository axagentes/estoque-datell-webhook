"""
Webhook Flask — Sincronização de Estoque iPhone (Datell → Supabase)

Endpoint principal:
  POST /sync-estoque   recebe o payload do n8n, filtra e sincroniza com Supabase
  GET  /health         monitoramento

Uso local:
  python webhook_estoque.py
  ngrok http 5000     (para expor publicamente ao n8n)
"""

from flask import Flask, request, jsonify
from inserir_estoque_iphone import (
    extrair_itens,
    e_celular_ou_acessorio,
    mapear,
    limpar_tabela,
    SUPABASE_URL,
    API_KEY,
)
import requests as http

app = Flask(__name__)

HEADERS_UPSERT = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/sync-estoque")
def sync_estoque():
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return jsonify({"status": "erro", "mensagem": "Payload JSON inválido"}), 400

    itens = extrair_itens(payload)
    total_recebido = len(itens)

    filtrados = [mapear(i) for i in itens if e_celular_ou_acessorio(i)]
    excluidos = total_recebido - len(filtrados)

    if not filtrados:
        return jsonify({
            "status": "aviso",
            "mensagem": "Nenhum item passou no filtro",
            "recebidos": total_recebido,
        })

    # Full sync: limpa tabela e reinserere apenas itens filtrados
    limpar_tabela()

    resp = http.post(
        f"{SUPABASE_URL}/rest/v1/estoque_iphone",
        headers=HEADERS_UPSERT,
        json=filtrados,
        timeout=60,
    )

    if resp.status_code not in (200, 201):
        return jsonify({
            "status": "erro",
            "mensagem": f"Supabase retornou {resp.status_code}",
            "detalhe": resp.text[:300],
        }), 500

    return jsonify({
        "status": "ok",
        "recebidos": total_recebido,
        "inseridos": len(filtrados),
        "excluidos_filtro": excluidos,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
