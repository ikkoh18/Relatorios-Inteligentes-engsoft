import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes import reports
from app.services.watcher_service import monitorar_pasta


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o watcher em background quando o servidor sobe
    task = asyncio.create_task(monitorar_pasta())
    yield
    # Cancela o watcher quando o servidor desliga
    task.cancel()


app = FastAPI(
    title="Módulo 3 — Relatórios Inteligentes",
    description="Microsserviço de geração automática de relatórios com IA.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(reports.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "module": 3, "version": "1.0.0"}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")
