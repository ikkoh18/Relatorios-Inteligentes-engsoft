import shutil

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.ai_service import gerar_relatorio
from app.services.export_service import exportar_docx, exportar_markdown, exportar_pdf
from app.services.storage_service import (
    INPUT_DIR,
    ler_fonte_projeto,
    ler_relatorio,
    listar_relatorios,
    salvar_fonte_projeto,
    salvar_relatorio,
)

router = APIRouter(prefix="/reports", tags=["Relatórios"])


class IngestaoPayload(BaseModel):
    projeto_id: str
    conteudo: str
    arquivos: list[str] = []
    template: str = "sprint_review"
    prompt_custom: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "projeto_id": "meu-projeto",
                "conteudo": "Texto extraído dos arquivos selecionados pelo usuário...",
                "arquivos": ["requisitos.md", "ata-sprint.txt"],
                "template": "sprint_review",
                "prompt_custom": "",
            }
        }


class GenerateFromProjectPayload(BaseModel):
    projeto_id: str
    template: str = "sprint_review"
    prompt_custom: str = ""


async def _gerar_a_partir_de_uploads(
    files: list[UploadFile],
    template: str,
    prompt_custom: str,
    projeto_id: str,
    auto_salvar: bool = True,
    registrar_fonte: bool = False,
):
    if not files:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo.")

    conteudo, nomes = "", []
    for f in files:
        try:
            texto = (await f.read()).decode("utf-8", errors="ignore")
            conteudo += f"\n\n--- Arquivo: {f.filename} ---\n{texto}"
            nomes.append(f.filename)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Erro ao ler {f.filename}.")

    if not conteudo.strip():
        raise HTTPException(status_code=400, detail="Arquivos enviados estão vazios.")

    if registrar_fonte:
        salvar_fonte_projeto(
            projeto_id=projeto_id,
            conteudo=conteudo,
            arquivos=nomes,
            origem="modulo2",
        )

    template_final = "custom" if prompt_custom.strip() else template
    relatorio = gerar_relatorio(conteudo, template_final, prompt_custom=prompt_custom)

    metadados = (
        salvar_relatorio(
            conteudo_md=relatorio,
            template=template_final,
            arquivos_origem=nomes,
            projeto_id=projeto_id,
        )
        if auto_salvar
        else None
    )

    return {
        "status": "ok",
        "template": template_final,
        "arquivos": nomes,
        "report": relatorio,
        "salvo_em": metadados["caminho_md"] if metadados else None,
        "id": metadados["id"] if metadados else None,
    }


@router.post("/generate", summary="Gerar relatório via upload de arquivos")
async def generate(
    files: list[UploadFile] = File(...),
    template: str = Form(default="sprint_review"),
    prompt_custom: str = Form(default=""),
    projeto_id: str = Form(default="projeto"),
    auto_salvar: bool = Form(default=True),
):
    return await _gerar_a_partir_de_uploads(
        files=files,
        template=template,
        prompt_custom=prompt_custom,
        projeto_id=projeto_id,
        auto_salvar=auto_salvar,
    )


@router.post("/ingest-files", summary="[Módulo 2] Enviar arquivos selecionados pelo usuário")
async def ingest_files(
    files: list[UploadFile] = File(...),
    template: str = Form(default="sprint_review"),
    prompt_custom: str = Form(default=""),
    projeto_id: str = Form(default="projeto"),
):
    """
    Endpoint para o Módulo 2 encaminhar os arquivos que o usuário selecionou.
    O Módulo 3 lê os arquivos, gera o relatório e salva para os Módulos 4, 5 e 6.
    """
    return await _gerar_a_partir_de_uploads(
        files=files,
        template=template,
        prompt_custom=prompt_custom,
        projeto_id=projeto_id,
        registrar_fonte=True,
    )


@router.post("/ingest", summary="[Módulo 2] Enviar conteúdo extraído via JSON")
async def ingest(payload: IngestaoPayload):
    """
    Endpoint para o Módulo 2 enviar o texto extraído dos arquivos selecionados.
    O relatório é gerado e salvo automaticamente.
    """
    if not payload.conteudo.strip():
        raise HTTPException(status_code=400, detail="Conteúdo vazio.")

    salvar_fonte_projeto(
        projeto_id=payload.projeto_id,
        conteudo=payload.conteudo,
        arquivos=payload.arquivos or ["via_modulo2"],
        origem="modulo2",
    )

    template_final = "custom" if payload.prompt_custom.strip() else payload.template
    relatorio = gerar_relatorio(payload.conteudo, template_final, prompt_custom=payload.prompt_custom)

    metadados = salvar_relatorio(
        conteudo_md=relatorio,
        template=template_final,
        arquivos_origem=payload.arquivos or ["via_modulo2"],
        projeto_id=payload.projeto_id,
    )

    return {
        "status": "ok",
        "id": metadados["id"],
        "salvo_em": metadados["caminho_md"],
        "report": relatorio,
    }


@router.post("/generate-from-project", summary="Gerar relatório com dados já recebidos do Módulo 2")
async def generate_from_project(payload: GenerateFromProjectPayload):
    fonte = ler_fonte_projeto(payload.projeto_id)
    if not fonte or not fonte.get("conteudo", "").strip():
        raise HTTPException(
            status_code=404,
            detail="Ainda não há arquivos do Módulo 2 para este projeto.",
        )

    template_final = "custom" if payload.prompt_custom.strip() else payload.template
    relatorio = gerar_relatorio(fonte["conteudo"], template_final, prompt_custom=payload.prompt_custom)

    metadados = salvar_relatorio(
        conteudo_md=relatorio,
        template=template_final,
        arquivos_origem=fonte.get("arquivos", ["via_modulo2"]),
        projeto_id=payload.projeto_id,
    )

    return {
        "status": "ok",
        "id": metadados["id"],
        "template": template_final,
        "arquivos": fonte.get("arquivos", []),
        "fonte_recebida_em": fonte.get("recebido_em"),
        "salvo_em": metadados["caminho_md"],
        "report": relatorio,
    }


@router.get("/project/{projeto_id}/source", summary="Verificar dados recebidos do Módulo 2")
def get_project_source(projeto_id: str):
    fonte = ler_fonte_projeto(projeto_id)
    if not fonte:
        return {"projeto_id": projeto_id, "recebido": False, "status": "aguardando_modulo2"}
    return {
        "projeto_id": projeto_id,
        "recebido": True,
        "status": "dados_recebidos",
        "arquivos": fonte.get("arquivos", []),
        "origem": fonte.get("origem"),
        "recebido_em": fonte.get("recebido_em"),
    }


@router.post("/receive-file", summary="[Módulo 2] Enviar arquivo para processamento automático")
async def receive_file(
    file: UploadFile = File(...),
    projeto_id: str = Form(default="projeto"),
):
    """
    Compatibilidade com integração por pasta: o Módulo 2 deposita um arquivo
    e o watcher gera o relatório automaticamente em até 10 segundos.
    """
    destino = INPUT_DIR / f"{projeto_id}_{file.filename}"
    with open(destino, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "status": "recebido",
        "arquivo": str(destino),
        "info": "Relatório será gerado automaticamente em até 10 segundos.",
    }


@router.post("/export", summary="Exportar relatório em PDF, DOCX ou Markdown")
async def export(report: str = Form(...), formato: str = Form(default="md")):
    formato = formato.lower()
    if formato == "docx":
        data = exportar_docx(report)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "relatorio.docx"
    elif formato == "pdf":
        data, media, filename = exportar_pdf(report), "application/pdf", "relatorio.pdf"
    else:
        data, media, filename = exportar_markdown(report), "text/markdown", "relatorio.md"

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/list", summary="[Módulos 4/5/6] Listar todos os relatórios gerados")
def list_reports():
    return {"relatorios": listar_relatorios()}


@router.get("/get/{relatorio_id}", summary="[Módulos 4/5/6] Buscar conteúdo de um relatório")
def get_report(relatorio_id: str):
    conteudo = ler_relatorio(relatorio_id)
    if not conteudo:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return {"id": relatorio_id, "conteudo": conteudo}


@router.get("/templates", summary="Listar templates disponíveis")
def listar_templates():
    return {
        "templates": [
            {
                "id": "sprint_review",
                "nome": "Sprint Review",
                "descricao": "Encerramento de sprint com entregas e aprendizados",
            },
            {
                "id": "tecnico",
                "nome": "Técnico",
                "descricao": "Documentação técnica de arquitetura e APIs",
            },
            {
                "id": "executivo",
                "nome": "Executivo",
                "descricao": "Resumo para gestores e clientes sem termos técnicos",
            },
            {
                "id": "custom",
                "nome": "Personalizado",
                "descricao": "Você define as instruções do relatório",
            },
        ]
    }
