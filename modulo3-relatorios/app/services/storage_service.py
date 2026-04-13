import os
import json
from datetime import datetime
from pathlib import Path

# Pastas principais
BASE_DIR       = Path("app/storage")
INPUT_DIR      = BASE_DIR / "inputs"    # Módulo 2 deposita arquivos aqui
OUTPUT_DIR     = BASE_DIR / "outputs"   # Relatórios prontos ficam aqui
PROCESSING_DIR = BASE_DIR / "processing" # Arquivos sendo processados

# Garante que as pastas existem
for d in [INPUT_DIR, OUTPUT_DIR, PROCESSING_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def salvar_relatorio(
    conteudo_md: str,
    template: str,
    arquivos_origem: list[str],
    projeto_id: str = None
) -> dict:
    """
    Salva o relatório gerado na pasta outputs.
    Retorna os metadados do arquivo salvo.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    projeto_id = projeto_id or "projeto"
    nome_base  = f"{projeto_id}_{template}_{timestamp}"

    # Salva o Markdown
    caminho_md = OUTPUT_DIR / f"{nome_base}.md"
    caminho_md.write_text(conteudo_md, encoding="utf-8")

    # Salva metadados em JSON (para os módulos 4 e 5 saberem o que chegou)
    metadados = {
        "id":             nome_base,
        "projeto_id":     projeto_id,
        "template":       template,
        "arquivos_origem": arquivos_origem,
        "gerado_em":      datetime.now().isoformat(),
        "caminho_md":     str(caminho_md),
        "status":         "pronto"
    }
    caminho_json = OUTPUT_DIR / f"{nome_base}.json"
    caminho_json.write_text(json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8")

    return metadados


def listar_relatorios() -> list[dict]:
    """Lista todos os relatórios já gerados (lê os JSONs de metadados)."""
    relatorios = []
    for arq in sorted(OUTPUT_DIR.glob("*.json"), reverse=True):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
            relatorios.append(dados)
        except Exception:
            continue
    return relatorios


def ler_relatorio(relatorio_id: str) -> str | None:
    """Lê o conteúdo Markdown de um relatório pelo ID."""
    caminho = OUTPUT_DIR / f"{relatorio_id}.md"
    if caminho.exists():
        return caminho.read_text(encoding="utf-8")
    return None


def listar_inputs_pendentes() -> list[str]:
    """
    Lista arquivos que o Módulo 2 depositou na pasta inputs
    e que ainda não foram processados.
    """
    return [str(f) for f in INPUT_DIR.iterdir() if f.is_file()]


def mover_para_processing(caminho: str) -> str:
    """Move um arquivo de inputs para processing (evita reprocessar)."""
    origem  = Path(caminho)
    destino = PROCESSING_DIR / origem.name
    origem.rename(destino)
    return str(destino)
