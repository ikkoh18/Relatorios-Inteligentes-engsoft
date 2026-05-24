# Integração do Módulo 3

O Módulo 3 lê os arquivos selecionados pelo usuário no Módulo 2, gera relatórios com IA e deixa os resultados disponíveis para os Módulos 4, 5 e 6.

## Módulo 2 -> Módulo 3

### Enviar arquivos selecionados pelo usuário

Use este endpoint quando o Módulo 2 tiver os arquivos originais selecionados pelo usuário.

```http
POST /reports/ingest-files
Content-Type: multipart/form-data
```

Campos:

- `files`: um ou mais arquivos selecionados pelo usuário.
- `projeto_id`: identificador do projeto.
- `template`: `sprint_review`, `tecnico`, `executivo` ou `custom`.
- `prompt_custom`: obrigatório apenas quando `template` for `custom`.

### Enviar conteúdo já extraído

Use este endpoint se o Módulo 2 já extraiu e concatenou o texto dos arquivos.

```http
POST /reports/ingest
Content-Type: application/json
```

```json
{
  "projeto_id": "meu-projeto",
  "conteudo": "texto extraído dos arquivos selecionados pelo usuário",
  "arquivos": ["requisitos.md", "ata-sprint.txt"],
  "template": "sprint_review",
  "prompt_custom": ""
}
```

## Interface do Módulo 3

A interface não seleciona arquivos locais. Ela usa o `projeto_id` para consultar os dados enviados pelo Módulo 2.

```http
GET /reports/project/{projeto_id}/source
```

```http
POST /reports/generate-from-project
Content-Type: application/json
```

```json
{
  "projeto_id": "meu-projeto",
  "template": "sprint_review",
  "prompt_custom": ""
}
```

## Módulos 4, 5 e 6 -> Módulo 3

### Listar relatórios

```http
GET /reports/list
```

### Buscar relatório por ID

```http
GET /reports/get/{id}
```

Retorna:

```json
{
  "id": "meu-projeto_sprint_review_20260524_160000",
  "conteudo": "# Relatório em Markdown..."
}
```

## Health check

```http
GET /health
```
