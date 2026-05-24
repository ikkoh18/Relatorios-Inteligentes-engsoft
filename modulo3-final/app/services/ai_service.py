import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def carregar_template(nome: str) -> str:
    caminho = f"app/templates/{nome}.txt"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Gere um relatório estruturado e completo do projeto fornecido."


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

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return resposta.choices[0].message.content
