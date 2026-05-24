# Módulo 3 — Relatórios Inteligentes

Microsserviço de geração automática de relatórios de projeto usando IA.
Parte da plataforma **DocIA** — Documentação Inteligente de Projetos de Engenharia de Software.

## Responsabilidade do módulo

O Módulo 3 lê os arquivos selecionados pelo usuário no Módulo 2, gera relatórios em Markdown e permite exportação em PDF, Markdown e DOCX.

A interface do Módulo 3 não seleciona arquivos do computador do usuário. Ela trabalha por `projeto_id`, consultando os dados que o Módulo 2 enviou pelos endpoints de integração.

## Funcionalidades

- Leitura dos arquivos recebidos do Módulo 2
- Geração de relatório via IA com 3 templates + prompt personalizado
- Exportação em PDF, Markdown e DOCX
- Recebimento de arquivos ou texto extraído pelo Módulo 2
- Exposição dos relatórios para os Módulos 4, 5 e 6
- Interface web no padrão visual da plataforma

## Como rodar localmente

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Configure `OPENAI_API_KEY` no arquivo `.env`.

Acesse em: http://localhost:8000

## Fluxo local de teste sem o Módulo 2 pronto

Enquanto o Módulo 2 ainda não estiver integrado, simule o envio dos dados por Swagger:

1. Acesse `http://localhost:8000/docs`.
2. Use `POST /reports/ingest` com um `projeto_id`, `conteudo` e lista `arquivos`.
3. Volte para `http://localhost:8000`.
4. Informe o mesmo `projeto_id`, clique em `Verificar Módulo 2` e depois em `Gerar Relatório com IA`.

## Deploy

### Render

O projeto já inclui `render.yaml` e `Procfile`.

No Render:

1. Crie um Web Service apontando para este repositório.
2. Configure a variável `OPENAI_API_KEY`.
3. Use o start command:

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

### Docker

```bash
docker build -t modulo3-relatorios .
docker run -p 8000:8000 --env-file .env modulo3-relatorios
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET  | `/health` | Status do serviço |
| POST | `/reports/ingest-files` | **[Módulo 2]** Envia arquivos selecionados pelo usuário |
| POST | `/reports/ingest` | **[Módulo 2]** Envia conteúdo já extraído via JSON |
| GET  | `/reports/project/{projeto_id}/source` | Consulta se o Módulo 2 já enviou dados do projeto |
| POST | `/reports/generate-from-project` | Gera relatório a partir dos dados recebidos do Módulo 2 |
| GET  | `/reports/list` | **[Módulos 4/5/6]** Lista todos os relatórios gerados |
| GET  | `/reports/get/{id}` | **[Módulos 4/5/6]** Retorna conteúdo de um relatório |
| POST | `/reports/export` | Exporta relatório em PDF, DOCX ou Markdown |
| GET  | `/reports/templates` | Lista templates disponíveis |
| GET  | `/docs` | Documentação interativa Swagger UI |

## Integração com outros módulos

Veja [INTEGRATION.md](INTEGRATION.md) para exemplos dos contratos usados pelo Módulo 2 e pelos Módulos 4, 5 e 6.
