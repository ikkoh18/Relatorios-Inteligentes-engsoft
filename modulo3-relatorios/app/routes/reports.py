from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.services.ai_service import gerar_relatorio
from app.services.export_service import exportar_markdown, exportar_docx, exportar_pdf
from app.services.storage_service import (
    salvar_relatorio,
    listar_relatorios,
    ler_relatorio,
    INPUT_DIR,
)
import shutil

router = APIRouter(prefix="/reports", tags=["Relatórios"])


class IngestaoPayload(BaseModel):
    projeto_id:    str
    conteudo:      str
    template:      str = "sprint_review"
    prompt_custom: str = ""


@router.post("/generate")
async def generate(
    files:         list[UploadFile] = File(...),
    template:      str  = Form(default="sprint_review"),
    prompt_custom: str  = Form(default=""),
    projeto_id:    str  = Form(default="projeto"),
    auto_salvar:   bool = Form(default=True),
):
    """Recebe arquivos, gera relatório com IA e salva automaticamente."""
    if not files:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo.")

    conteudo       = ""
    nomes_arquivos = []
    for f in files:
        try:
            texto = (await f.read()).decode("utf-8", errors="ignore")
            conteudo += f"\n\n--- Arquivo: {f.filename} ---\n{texto}"
            nomes_arquivos.append(f.filename)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Erro ao ler {f.filename}.")

    if not conteudo.strip():
        raise HTTPException(status_code=400, detail="Arquivos enviados estão vazios.")

    template_final = "custom" if prompt_custom.strip() else template
    relatorio = gerar_relatorio(conteudo, template_final, prompt_custom=prompt_custom)

    metadados = None
    if auto_salvar:
        metadados = salvar_relatorio(
            conteudo_md=relatorio,
            template=template_final,
            arquivos_origem=nomes_arquivos,
            projeto_id=projeto_id,
        )

    return {
        "status":   "ok",
        "template": template_final,
        "report":   relatorio,
        "salvo_em": metadados["caminho_md"] if metadados else None,
        "id":       metadados["id"] if metadados else None,
    }


@router.post("/ingest")
async def ingest(payload: IngestaoPayload):
    """Endpoint para o Módulo 2 enviar dados diretamente via JSON."""
    if not payload.conteudo.strip():
        raise HTTPException(status_code=400, detail="Conteúdo vazio.")

    template_final = "custom" if payload.prompt_custom.strip() else payload.template
    relatorio = gerar_relatorio(
        payload.conteudo,
        template_final,
        prompt_custom=payload.prompt_custom
    )

    metadados = salvar_relatorio(
        conteudo_md=relatorio,
        template=template_final,
        arquivos_origem=["via_modulo2"],
        projeto_id=payload.projeto_id,
    )

    return {
        "status":   "ok",
        "id":       metadados["id"],
        "salvo_em": metadados["caminho_md"],
        "report":   relatorio,
    }


@router.post("/export")
async def export(
    report:  str = Form(...),
    formato: str = Form(default="md")
):
    """Exporta relatório para PDF, DOCX ou Markdown."""
    formato = formato.lower()

    if formato == "docx":
        data     = exportar_docx(report)
        media    = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "relatorio.docx"
    elif formato == "pdf":
        data     = exportar_pdf(report)
        media    = "application/pdf"
        filename = "relatorio.pdf"
    else:
        data     = exportar_markdown(report)
        media    = "text/markdown"
        filename = "relatorio.md"

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/list")
def list_reports():
    """Lista todos os relatórios salvos. Módulos 4 e 5 usam este endpoint."""
    return {"relatorios": listar_relatorios()}


@router.get("/get/{relatorio_id}")
def get_report(relatorio_id: str):
    """Retorna o conteúdo de um relatório. Módulos 4 e 5 usam este endpoint."""
    conteudo = ler_relatorio(relatorio_id)
    if not conteudo:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return {"id": relatorio_id, "conteudo": conteudo}


@router.post("/receive-file")
async def receive_file(
    file:       UploadFile = File(...),
    projeto_id: str = Form(default="projeto"),
):
    """O Módulo 2 deposita arquivos aqui. O watcher processa automaticamente."""
    destino = INPUT_DIR / f"{projeto_id}_{file.filename}"
    with open(destino, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "status":  "recebido",
        "arquivo": str(destino),
        "info":    "Relatório será gerado automaticamente em até 10 segundos."
    }


@router.get("/templates")
def listar_templates():
    return {
        "templates": [
            {"id": "sprint_review", "nome": "Sprint Review",
             "descricao": "Encerramento de sprint com entregas e aprendizados"},
            {"id": "tecnico",       "nome": "Técnico",
             "descricao": "Documentação técnica de arquitetura e APIs"},
            {"id": "executivo",     "nome": "Executivo",
             "descricao": "Resumo para gestores e clientes sem termos técnicos"},
            {"id": "custom",        "nome": "Personalizado",
             "descricao": "Você define as instruções do relatório"},
        ]
    }
