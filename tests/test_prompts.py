"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.prompts import ChatPromptTemplate
from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


@pytest.fixture(scope="module")
def prompt_data():
    data = load_prompts(PROMPT_FILE)
    assert data and PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    return prompt_data.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip()

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"\bVocê é (um|uma)\b", system_prompt, re.IGNORECASE), \
            "O system prompt deve definir uma persona com 'Você é um/uma ...'"
        assert re.search(r"Product (Owner|Manager)", system_prompt), \
            "A persona deve ser de produto (Product Owner / Product Manager)"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        lowered = system_prompt.lower()
        assert "user story" in lowered
        assert "como um" in lowered and "eu quero" in lowered and "para que" in lowered, \
            "O prompt deve exigir o template 'Como um..., eu quero..., para que...'"
        assert "critérios de aceitação" in lowered
        assert all(step in system_prompt for step in ("Dado que", "Quando", "Então")), \
            "O prompt deve exigir critérios no formato Given-When-Then"

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"^#+\s*Exemplo \d+", system_prompt, re.MULTILINE)
        assert len(examples) >= 2, f"Esperados ao menos 2 exemplos, encontrados {len(examples)}"
        # Cada exemplo precisa ter entrada (Relato) e saída (Resposta)
        assert system_prompt.count("Relato:") >= len(examples)
        assert system_prompt.count("Resposta:") >= len(examples)

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("system_prompt", "user_prompt", "description"):
            text = prompt_data.get(field) or ""
            assert "[TODO]" not in text and "TODO" not in text, f"'{field}' ainda contém TODO"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied")
        assert isinstance(techniques, list)
        assert len([t for t in techniques if str(t).strip()]) >= 2
        assert "Few-shot Learning" in techniques, "Few-shot Learning é obrigatório"

    def test_user_prompt_uses_bug_report_variable(self, prompt_data, system_prompt):
        """O {bug_report} deve ir só no user prompt (na v1 ele estava duplicado no system)."""
        assert "{bug_report}" in prompt_data.get("user_prompt", "")
        assert "{bug_report}" not in system_prompt

    def test_template_has_only_bug_report_variable(self, prompt_data):
        """Chaves soltas no texto viram variáveis no ChatPromptTemplate e quebram o invoke."""
        template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])
        assert set(template.input_variables) == {"bug_report"}

    def test_prompt_structure_is_valid(self, prompt_data):
        """Usa o validador do projeto (campos obrigatórios, TODOs e técnicas)."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
