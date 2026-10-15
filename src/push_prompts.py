"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()


PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", f"{PROMPT_KEY}.yml")
REQUIRED_VARIABLE = "bug_report"


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate (system + user) a partir dos dados do YAML."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_identifier = f"{username}/{prompt_name}"

    prompt = build_chat_prompt(prompt_data)
    techniques = prompt_data.get("techniques_applied", [])
    tags = list(dict.fromkeys(
        prompt_data.get("tags", [])
        + [prompt_data.get("version", "")]
        + [f"technique:{t}" for t in techniques]
    ))
    tags = [tag for tag in tags if tag]

    description = prompt_data.get("description", "")
    readme = (
        f"# {prompt_name}\n\n"
        f"{description}\n\n"
        f"**Versão:** {prompt_data.get('version', '')}\n\n"
        "## Técnicas aplicadas\n\n"
        + "\n".join(f"- {t}" for t in techniques)
        + "\n"
    )

    print(f"Fazendo push: {prompt_identifier}")
    try:
        client = Client()
        url = client.push_prompt(
            prompt_identifier,
            object=prompt,
            is_public=True,
            description=description,
            readme=readme,
            tags=tags,
            commit_description=prompt_data.get("changelog", f"Versão {prompt_data.get('version', '')}"),
        )
    except Exception as e:
        error_msg = str(e)
        if "Nothing to commit" in error_msg or "409" in error_msg:
            print("   ⚠️  Nenhuma mudança desde o último commit — prompt já está atualizado no Hub")
            return True
        print(f"❌ Erro ao fazer push de '{prompt_identifier}': {e}")
        return False

    print(f"   ✓ Push concluído (público)")
    print(f"   ✓ Tags: {', '.join(tags)}")
    print(f"   ✓ {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    user_prompt = (prompt_data.get("user_prompt") or "").strip()
    if not user_prompt:
        errors.append("user_prompt está vazio")

    try:
        variables = set(build_chat_prompt(prompt_data).input_variables)
    except Exception as e:
        errors.append(f"Template inválido: {e}")
    else:
        if REQUIRED_VARIABLE not in variables:
            errors.append(f"O template precisa usar a variável {{{REQUIRED_VARIABLE}}}")
        extra = variables - {REQUIRED_VARIABLE}
        if extra:
            errors.append(
                f"Variáveis inesperadas no template: {', '.join(sorted(extra))} "
                "(use {{ }} para chaves literais)"
            )

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_FILE)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em prompts/{PROMPT_KEY}.yml")
        return 1

    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print("   ✓ Prompt validado")

    if not push_prompt_to_langsmith(PROMPT_KEY, prompt_data):
        return 1

    print("\n✅ Push concluído com sucesso!")
    print("Próximo passo: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
