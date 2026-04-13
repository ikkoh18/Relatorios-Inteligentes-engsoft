# Módulo 3 — Relatórios Inteligentes

Microsserviço de geração automática de relatórios de projeto usando IA (Claude).

## Funcionalidades (MVP)

- Upload de arquivos do projeto (`.txt`, `.md`, `.py`, `.js`, etc.)
- Geração de relatório via IA com 3 templates: Sprint Review, Técnico, Executivo
- Exportação em PDF, Markdown e DOCX
- Interface web integrada

## Como rodar

### 1. Clone e entre na pasta
```bash
git clone <url-do-repo>
cd modulo3-relatorios
```

### 2. Crie o ambiente virtual e instale as dependências
```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Configure a API key
Crie um arquivo `.env` baseado no `.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-sua-key-aqui
```

### 4. Rode o servidor
```bash
uvicorn app.main:app --reload
```

### 5. Acesse
- Interface web: http://localhost:8000
- Documentação da API: http://localhost:8000/docs

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | /health | Status do serviço |
| GET | /reports/templates | Lista templates disponíveis |
| POST | /reports/generate | Gera relatório a partir de arquivos |
| POST | /reports/export | Exporta relatório em PDF/DOCX/MD |

## Tecnologias

- **FastAPI** — framework da API
- **Anthropic Claude** — IA para geração do relatório
- **python-docx** — exportação DOCX
- **fpdf2** — exportação PDF
- **Uvicorn** — servidor ASGI
