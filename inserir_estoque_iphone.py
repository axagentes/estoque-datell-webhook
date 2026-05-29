"""
Sincronização de estoque de iPhones e acessórios no Supabase.
Filtra apenas:
  - CELULAR  (tipoProdutoDescricao == "CELULAR")
  - Acessório (snAcessorio == 1)
Aceita o payload aninhado: {"data": {"totalItens": N, "itens": [...]}}
ou diretamente uma lista de itens.

As funções extrair_itens, e_celular_ou_acessorio, mapear e upsert_estoque
são importáveis pelo webhook_estoque.py.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cdexpdefgrbnwgknssxk.supabase.co")
API_KEY      = os.environ.get("API_KEY")

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

HEADERS_UPSERT = {**HEADERS, "Prefer": "resolution=merge-duplicates"}


def extrair_itens(payload) -> list:
    """Aceita lista direta ou estrutura {"data": {"itens": [...]}}."""
    if isinstance(payload, list):
        return payload
    return payload.get("data", {}).get("itens", [])


def e_celular_ou_acessorio(item: dict) -> bool:
    """Retorna True apenas para celulares e acessórios (capas, etc.), excluindo hidrogel."""
    descricao = (item.get("descricao") or "").lower()
    termos_excluidos = ("hidrogel", "traseira", "cartão de memória", "universal", "fosca com protecao", "tela confidencial", "fosca com pelicula", "veicular", "camera armor")
    if any(t in descricao for t in termos_excluidos):
        return False
    if item.get("tipoProdutoDescricao") == "CELULAR":
        return True
    if item.get("snAcessorio") == 1:
        return True
    return False


def mapear(item: dict) -> dict:
    return {
        "id":                 item["id"],
        "descricao":          item.get("descricao"),
        "disponibilidade":    item.get("disponibilidade"),
        "fornecedor_nome":    item.get("fornecedorNome"),
        "data_entrada":       item.get("dataEntrada"),
        "valor_custo":        item.get("valorCusto"),
        "valor_venda":        item.get("valorVenda"),
        "gb_descricao":       item.get("gbDescricao"),
        "aparelho_descricao": item.get("aparelhoDescricao"),
    }


def limpar_tabela() -> None:
    """Remove todos os registros existentes antes da re-sincronização."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/estoque_iphone?id=gte.0",
        headers=HEADERS,
        timeout=30,
    )
    if resp.status_code in (200, 204):
        print("[OK] Tabela limpa.")
    else:
        print(f"[AVISO] Limpeza retornou {resp.status_code}: {resp.text[:200]}")


def upsert_estoque(payload, limpar_antes: bool = True) -> None:
    """
    Filtra e sincroniza estoque. Se limpar_antes=True, apaga tudo antes de inserir
    (garante que a tabela reflita exatamente o payload atual).
    """
    itens = extrair_itens(payload)
    total_recebido = len(itens)

    filtrados = [mapear(i) for i in itens if e_celular_ou_acessorio(i)]
    excluidos = total_recebido - len(filtrados)

    print(f"Itens recebidos : {total_recebido}")
    print(f"Após filtro     : {len(filtrados)}  (excluídos {excluidos} peças/serviços/telas)")

    if not filtrados:
        print("[AVISO] Nenhum item passou no filtro.")
        return

    if limpar_antes:
        limpar_tabela()

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/estoque_iphone",
        headers=HEADERS_UPSERT,
        json=filtrados,
        timeout=60,
    )

    if resp.status_code in (200, 201):
        print(f"[OK] {len(filtrados)} registros sincronizados.")
    else:
        print(f"[ERRO] {resp.status_code}: {resp.text[:400]}")


# ---------------------------------------------------------------------------
# Payload do novo lote (itens recebidos — peças/telas já serão filtradas)
# ---------------------------------------------------------------------------
NOVO_PAYLOAD = {
    "data": {
        "totalItens": 1022,
        "itens": [
            {"id":7917635,"descricao":"7917635 - IPHONE XR - BRANCO - 64GB -  Estado: SEMI-NOVO -  IMEI: 353082100876417 -  IMEI 2: 353082100776047 -  SN: DV6YV204KXK2","disponibilidade":"Disponível para venda","fornecedorNome":"ANDREI RIBEIRO DE PAULA","dataEntrada":"2026-05-27","valorCusto":400,"valorVenda":1000,"gbDescricao":"64GB","aparelhoDescricao":"IPHONE XR","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7917393,"descricao":"7917393 - IPHONE 15 PRO MAX - AZUL TITANIUM - 256GB -  Estado: SEMI-NOVO -  IMEI: 354058240547513 -  IMEI 2: 354058240708289 -  SN: FPGF9WXGYG","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-27","valorCusto":3247,"valorVenda":5000,"gbDescricao":"256GB","aparelhoDescricao":"IPHONE 15 PRO MAX","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7917017,"descricao":"7917017 - IPHONE 16 PRO MAX - PRETO - 256GB -  Estado: SEMI-NOVO -  IMEI: 353393812464040 -  IMEI 2: 353393812380709 -  SN: F04KN9FNMP","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-27","valorCusto":4183,"valorVenda":6299,"gbDescricao":"256GB","aparelhoDescricao":"IPHONE 16 PRO MAX","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7916743,"descricao":"7916743 - IPHONE 16 PRO MAX - PRETO - 256GB -  Estado: SEMI-NOVO -  IMEI: 358536500413696 -  IMEI 2: 358536500437489 -  SN: L9XKW15QH4","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-27","valorCusto":4183.65,"valorVenda":6199,"gbDescricao":"256GB","aparelhoDescricao":"IPHONE 16 PRO MAX","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7916544,"descricao":"7916544 - IPHONE 16 PRO - PRETO - 128GB -  Estado: SEMI-NOVO -  IMEI: 359072841286574 -  IMEI 2: 359072841396357 -  SN: CWR4NG704Y","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-27","valorCusto":3500,"valorVenda":5400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 16 PRO","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7916433,"descricao":"7916433 - IPHONE 16 PRO - PRETO - 128GB -  Estado: SEMI-NOVO -  IMEI: 355983883004804 -  IMEI 2: 355983883075606 -  SN: C2Q9P4N0WH","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-27","valorCusto":3500,"valorVenda":5400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 16 PRO","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895624,"descricao":"7895624 - IPHONE 14 - LILÁS - 128GB -  Estado: SEMI-NOVO -  IMEI: 358832599177247 -  IMEI 2: 358832598986754 -  SN: WCNFYFWLPX","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1498,"valorVenda":2700,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 14","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895593,"descricao":"7895593 - IPHONE 14 - LILÁS - 128GB -  Estado: SEMI-NOVO -  IMEI: 350928999109794 -  IMEI 2: 350928999440991 -  SN: LN7H5020R5","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1498,"valorVenda":2700,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 14","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895590,"descricao":"7895590 - IPHONE 14 - AZUL - 128GB -  Estado: SEMI-NOVO -  IMEI: 351253185580404 -  IMEI 2: 351253183514256 -  SN: DM66M2CMV6","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1498,"valorVenda":2700,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 14","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895584,"descricao":"7895584 - IPHONE 14 - AZUL - 128GB -  Estado: SEMI-NOVO -  IMEI: 356226677296049 -  IMEI 2: 356226677522782 -  SN: K9F3WKCFN2","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1498,"valorVenda":2700,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 14","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895579,"descricao":"7895579 - IPHONE 14 - AZUL - 128GB -  Estado: SEMI-NOVO -  IMEI: 358798480388880 -  IMEI 2: 358798480397568 -  SN: JFMWH2X2FN","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1498,"valorVenda":2700,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 14","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895564,"descricao":"7895564 - IPHONE 13 PRO - PRETO - 128GB -  IMEI: 358750486856139 -  IMEI 2: 358750486568650 -  SN: TL4TVFG9KG","disponibilidade":"Laboratório","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1702,"valorVenda":3000,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13 PRO","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895555,"descricao":"7895555 - IPHONE 13 PRO - BRANCO - 128GB -  Estado: SEMI-NOVO -  IMEI: 352806847638883 -  IMEI 2: 352806847579343 -  SN: HV9LKXW5J6","disponibilidade":"Laboratório","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1702,"valorVenda":3000,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13 PRO","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895528,"descricao":"7895528 - IPHONE 13 - ROSA - 128GB -  Estado: SEMI-NOVO -  IMEI: 356815601967004 -  IMEI 2: 356815601946040 -  SN: DFWL25QY7V","disponibilidade":"Laboratório","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895492,"descricao":"7895492 - IPHONE 13 - ROSA - 128GB -  Estado: SEMI-NOVO -  IMEI: 351138103273366 -  IMEI 2: 351138103446954 -  SN: DKWM2JGTJL","disponibilidade":"Laboratório","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895480,"descricao":"7895480 - IPHONE 13 - ROSA - 128GB -  Estado: SEMI-NOVO -  IMEI: 352678439836021 -  IMEI 2: 352678436463902 -  SN: M2N2F7HRVP","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895467,"descricao":"7895467 - IPHONE 13 - ROSA - 128GB -  Estado: SEMI-NOVO -  IMEI: 353763865078949 -  IMEI 2: 353763865266726 -  SN: H009FDQYWT","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895456,"descricao":"7895456 - IPHONE 13 - PRETO - 128GB -  Estado: SEMI-NOVO -  IMEI: 352678439794246 -  IMEI 2: 352678436987801 -  SN: CQG739CJF9","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895449,"descricao":"7895449 - IPHONE 13 - ROSA - 128GB -  Estado: SEMI-NOVO -  IMEI: 351829685017151 -  IMEI 2: 351829685800143 -  SN: W3F22X63PW","disponibilidade":"Laboratório","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            {"id":7895442,"descricao":"7895442 - IPHONE 13 - AZUL - 128GB -  Estado: SEMI-NOVO -  IMEI: 353257390860335 -  IMEI 2: 353257391811626 -  SN: KX7161X492","disponibilidade":"Disponível para venda","fornecedorNome":"SCAL","dataEntrada":"2026-05-25","valorCusto":1324,"valorVenda":2400,"gbDescricao":"128GB","aparelhoDescricao":"IPHONE 13","tipoProdutoDescricao":"CELULAR","snAcessorio":0,"snPeca":0},
            # --- Acessórios (snAcessorio=1) ---
            {"id":7895191,"descricao":"7895191 - IPHONE 17 PRO MAX","disponibilidade":"Disponível para venda","fornecedorNome":"Almeida Cruz","dataEntrada":"2026-05-25","valorCusto":3.5,"valorVenda":65,"gbDescricao":None,"aparelhoDescricao":"IPHONE 17 PRO MAX","tipoProdutoDescricao":"CAPA","snAcessorio":1,"snPeca":0},
            {"id":7895171,"descricao":"7895171 - IPHONE 17 PRO","disponibilidade":"Disponível para venda","fornecedorNome":"Almeida Cruz","dataEntrada":"2026-05-25","valorCusto":3.5,"valorVenda":65,"gbDescricao":None,"aparelhoDescricao":"IPHONE 17 PRO","tipoProdutoDescricao":"CAPA","snAcessorio":1,"snPeca":0},
            {"id":7895162,"descricao":"7895162 - IPHONE 17","disponibilidade":"Disponível para venda","fornecedorNome":"Almeida Cruz","dataEntrada":"2026-05-25","valorCusto":3.5,"valorVenda":65,"gbDescricao":None,"aparelhoDescricao":"IPHONE 17","tipoProdutoDescricao":"CAPA","snAcessorio":1,"snPeca":0},
            # --- Excluídos automaticamente pelo filtro (snPeca=1 / TELA) ---
            # 7895218 TELA IPHONE 15 PRO MAX  → ignorado
            # 7895187 TELA IPHONE 11          → ignorado
            # 7895177 TELA IPHONE 11 PRO      → ignorado
            # 7895167 TELA IPHONE 12/12 PRO   → ignorado
        ]
    }
}


if __name__ == "__main__":
    upsert_estoque(NOVO_PAYLOAD, limpar_antes=True)
