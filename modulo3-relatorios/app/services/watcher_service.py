"""
Monitora a pasta app/storage/inputs.
Quando o Módulo 2 depositar arquivos lá, gera o relatório automaticamente
e salva em app/storage/outputs — sem nenhuma interação humana.
"""
import asyncio
import logging
from pathlib import Path
from app.services.ai_service import gerar_relatorio
from app.services.storage_service import (
    listar_inputs_pendentes,
    mover_para_processing,
    salvar_relatorio,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watcher")

INTERVALO_SEGUNDOS = 10   # verifica a pasta a cada 10 segundos
TEMPLATE_AUTOMATICO = "sprint_review"  # template padrão para processamento automático


async def processar_arquivo(caminho: str):
    """Processa um único arquivo: lê, gera relatório, salva."""
    try:
        p = Path(caminho)
        logger.info(f"[watcher] Processando: {p.name}")

        # Move para processing (evita reprocessar se demorar)
        caminho_proc = mover_para_processing(caminho)

        # Lê o conteúdo
        conteudo = Path(caminho_proc).read_text(encoding="utf-8", errors="ignore")
        if not conteudo.strip():
            logger.warning(f"[watcher] Arquivo vazio, ignorando: {p.name}")
            return

        # Gera o relatório com IA
        logger.info(f"[watcher] Gerando relatório para: {p.name}")
        relatorio = gerar_relatorio(conteudo, TEMPLATE_AUTOMATICO)

        # Salva na pasta outputs
        projeto_id = p.stem  # usa o nome do arquivo como ID do projeto
        metadados  = salvar_relatorio(
            conteudo_md=relatorio,
            template=TEMPLATE_AUTOMATICO,
            arquivos_origem=[p.name],
            projeto_id=projeto_id
        )

        logger.info(f"[watcher] Relatório salvo: {metadados['id']}")

    except Exception as e:
        logger.error(f"[watcher] Erro ao processar {caminho}: {e}")


async def monitorar_pasta():
    """Loop infinito que verifica a pasta inputs periodicamente."""
    logger.info(f"[watcher] Monitorando pasta inputs a cada {INTERVALO_SEGUNDOS}s...")
    while True:
        pendentes = listar_inputs_pendentes()
        if pendentes:
            logger.info(f"[watcher] {len(pendentes)} arquivo(s) encontrado(s).")
            for caminho in pendentes:
                await processar_arquivo(caminho)
        await asyncio.sleep(INTERVALO_SEGUNDOS)
