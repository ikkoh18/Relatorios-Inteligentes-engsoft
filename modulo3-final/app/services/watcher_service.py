import asyncio
import logging
from pathlib import Path
from app.services.ai_service import gerar_relatorio
from app.services.storage_service import listar_inputs_pendentes, mover_para_processing, salvar_relatorio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watcher")

INTERVALO_SEGUNDOS = 10
TEMPLATE_AUTOMATICO = "sprint_review"


async def processar_arquivo(caminho: str):
    try:
        p = Path(caminho)
        logger.info(f"[watcher] Processando: {p.name}")
        caminho_proc = mover_para_processing(caminho)
        conteudo = Path(caminho_proc).read_text(encoding="utf-8", errors="ignore")
        if not conteudo.strip():
            return
        relatorio  = gerar_relatorio(conteudo, TEMPLATE_AUTOMATICO)
        metadados  = salvar_relatorio(
            conteudo_md=relatorio,
            template=TEMPLATE_AUTOMATICO,
            arquivos_origem=[p.name],
            projeto_id=p.stem
        )
        logger.info(f"[watcher] Salvo: {metadados['id']}")
    except Exception as e:
        logger.error(f"[watcher] Erro: {e}")


async def monitorar_pasta():
    logger.info(f"[watcher] Monitorando inputs a cada {INTERVALO_SEGUNDOS}s...")
    while True:
        pendentes = listar_inputs_pendentes()
        for caminho in pendentes:
            await processar_arquivo(caminho)
        await asyncio.sleep(INTERVALO_SEGUNDOS)
