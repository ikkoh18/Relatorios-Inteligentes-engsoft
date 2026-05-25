import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()


def carregar_template(nome: str) -> str:
    caminho = f"app/templates/{nome}.txt"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Gere um relatório estruturado e completo do projeto fornecido."


def _client_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _linhas_relevantes(conteudo: str, limite: int = 8) -> list[str]:
    linhas = []
    for linha in conteudo.splitlines():
        texto = linha.strip(" -\t")
        if not texto or texto.startswith("--- Arquivo:"):
            continue
        if texto not in linhas:
            linhas.append(texto)
        if len(linhas) >= limite:
            break
    return linhas


def _gerar_relatorio_contingencia(conteudo: str, template_nome: str, prompt_custom: str = "") -> str:
    linhas = _linhas_relevantes(conteudo)
    resumo = " ".join(linhas)[:1200] or "Conteudo do projeto recebido sem texto legivel."
    instrucoes = prompt_custom.strip() or carregar_template(template_nome)

    pontos = "\n".join(f"- {linha}" for linha in linhas[:6]) or "- Sem pontos textuais detectados."

    return f"""# Relatorio Inteligente do Projeto

> Modo de contingencia: o provedor de IA nao concluiu a chamada no momento, entao o Modulo 3 estruturou o conteudo recebido para manter a integracao funcionando.

## Objetivo do Relatorio

{instrucoes.strip()}

## Visao Geral

{resumo}

## Principais Pontos Identificados

{pontos}

## Encaminhamentos Recomendados

- Validar se os arquivos enviados pelo Modulo 2 representam o escopo correto do projeto.
- Complementar requisitos, decisoes tecnicas e registros de reuniao quando faltarem detalhes.
- Usar este relatorio como base para os Modulos 4, 5 e 6 consumirem o conteudo em Markdown.

## Observacao Operacional

Quando a quota do provedor de IA estiver disponivel novamente, este mesmo endpoint volta a gerar o texto com o modelo configurado.
"""


def gerar_relatorio(conteudo: str, template_nome: str, prompt_custom: str = "") -> str:
    instrucoes = prompt_custom.strip() if prompt_custom.strip() else carregar_template(template_nome)

    prompt = f"""Você é um redator técnico especializado em documentação de projetos de software.

Instruções:
{instrucoes}

Conteúdo fornecido:
{conteudo}

Gere o relatório completo seguindo as instruções acima.
Formate em Markdown com títulos, subtítulos e listas onde apropriado.
Seja objetivo e profissional."""

    client = _client_openai()
    if not client:
        return _gerar_relatorio_contingencia(conteudo, template_nome, prompt_custom)

    try:
        resposta = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return resposta.choices[0].message.content
    except OpenAIError:
        return _gerar_relatorio_contingencia(conteudo, template_nome, prompt_custom)
