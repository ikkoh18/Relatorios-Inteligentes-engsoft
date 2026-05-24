import os
import json
from datetime import datetime
from pathlib import Path

BASE_DIR       = Path("app/storage")
INPUT_DIR      = BASE_DIR / "inputs"
OUTPUT_DIR     = BASE_DIR / "outputs"
PROCESSING_DIR = BASE_DIR / "processing"
SOURCE_DIR     = BASE_DIR / "sources"

for d in [INPUT_DIR, OUTPUT_DIR, PROCESSING_DIR, SOURCE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def salvar_relatorio(conteudo_md: str, template: str, arquivos_origem: list, projeto_id: str = None) -> dict:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    projeto_id = projeto_id or "projeto"
    nome_base  = f"{projeto_id}_{template}_{timestamp}"

    caminho_md = OUTPUT_DIR / f"{nome_base}.md"
    caminho_md.write_text(conteudo_md, encoding="utf-8")

    metadados = {
        "id":              nome_base,
        "projeto_id":      projeto_id,
        "template":        template,
        "arquivos_origem": arquivos_origem,
        "gerado_em":       datetime.now().isoformat(),
        "caminho_md":      str(caminho_md),
        "status":          "pronto"
    }
    (OUTPUT_DIR / f"{nome_base}.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadados


def listar_relatorios() -> list:
    relatorios = []
    for arq in sorted(OUTPUT_DIR.glob("*.json"), reverse=True):
        try:
            relatorios.append(json.loads(arq.read_text(encoding="utf-8")))
        except Exception:
            continue
    return relatorios


def salvar_fonte_projeto(projeto_id: str, conteudo: str, arquivos: list[str], origem: str = "modulo2") -> dict:
    projeto_id = projeto_id or "projeto"
    fonte = {
        "projeto_id": projeto_id,
        "conteudo": conteudo,
        "arquivos": arquivos,
        "origem": origem,
        "recebido_em": datetime.now().isoformat(),
    }
    (SOURCE_DIR / f"{projeto_id}.json").write_text(
        json.dumps(fonte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return fonte


def ler_fonte_projeto(projeto_id: str) -> dict | None:
    caminho = SOURCE_DIR / f"{projeto_id}.json"
    if not caminho.exists():
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return None


def ler_relatorio(relatorio_id: str) -> str | None:
    caminho = OUTPUT_DIR / f"{relatorio_id}.md"
    return caminho.read_text(encoding="utf-8") if caminho.exists() else None


def listar_inputs_pendentes() -> list:
    return [
        str(f)
        for f in INPUT_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    ]


def mover_para_processing(caminho: str) -> str:
    origem  = Path(caminho)
    destino = PROCESSING_DIR / origem.name
    if destino.exists():
        destino = PROCESSING_DIR / f"{origem.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{origem.suffix}"
    origem.rename(destino)
    return str(destino)
