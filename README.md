# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do MBA em IA (Full Cycle). O software:

1. Faz **pull** do prompt de baixa qualidade `leonanluppi/bug_to_user_story_v1` do LangSmith Prompt Hub;
2. **Refatora** esse prompt com técnicas de Prompt Engineering (`prompts/bug_to_user_story_v2.yml`);
3. Faz **push** da versão otimizada (pública, com metadados) para `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`;
4. **Avalia** o prompt contra um dataset de 15 bugs com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision), exigindo nota ≥ 0.8 em todas.

O prompt transforma relatos de bugs em User Stories ágeis com critérios de aceitação no formato Given-When-Then.

---

## Técnicas Aplicadas (Fase 2)

O prompt v2 combina quatro técnicas, registradas em `techniques_applied` no YAML e enviadas como tags (`technique:*`) no push.

### 1. Role Prompting

**Por quê:** o v1 dizia apenas "Você é um assistente". Sem persona, o modelo não sabe qual padrão de qualidade seguir: um assistente genérico escreve uma tarefa técnica, enquanto um Product Owner escreve uma User Story centrada no usuário e com critérios testáveis. Como os bugs do dataset vão de UI simples a race conditions, connection pool e OWASP, a persona também precisa de repertório técnico para não errar nem diluir os detalhes.

**Como apliquei:**

```text
Você é um Product Owner Sênior com 10 anos de experiência em times ágeis (Scrum/Kanban)
de produtos digitais: e-commerce, SaaS B2B, mobile e ERP. Você também tem background
técnico em engenharia de software, então entende logs, endpoints, códigos HTTP, queries
SQL e problemas de concorrência e performance.
```

### 2. Few-shot Learning (obrigatória)

**Por quê:** os juízes (`src/metrics.py`) comparam a resposta com uma **referência**. Quanto mais o formato da resposta se aproxima dela, maiores ficam o F1 (recall), a Clarity e a Precision. Explicar o formato só com instruções é ambíguo; mostrar exemplos é muito mais eficaz.

**Como apliquei:** três exemplos de entrada → saída, um para cada nível de complexidade do dataset:

| Exemplo | Nível | Bug | O que ensina |
|---|---|---|---|
| 1 | Simples | Filtro de categoria ignora a seleção | Frase "Como um..., eu quero..., para que..." + 5 critérios Dado/Quando/Então/E |
| 2 | Médio | Upload de avatar falha com HTTP 413 | Usar endpoint e código HTTP nos critérios, seção `Contexto Técnico:` |
| 3 | Complexo | Agendamento da clínica com 3 falhas | Blocos `=== ... ===`, critérios A/B/C por problema, tasks com prefixo `[ÁREA]` |

Os exemplos são **bugs inéditos**, de propósito: copiar casos do dataset de avaliação seria vazamento de dados e inflaria as notas artificialmente.

### 3. Chain of Thought (interno)

**Por quê:** converter um bug em User Story exige inferir coisas que não estão escritas, como quem é a persona afetada, qual é o comportamento correto e qual valor de negócio se perde. Pedir esse raciocínio em etapas reduz personas genéricas ("Como um usuário") e omissões de fatos (que derrubam o recall do F1).

**Como apliquei:** o prompt descreve seis passos (persona → ação → benefício → complexidade → fatos → critérios) e pede que o modelo **não** imprima a análise. Um raciocínio visível na saída seria julgado como texto irrelevante e derrubaria Clarity (concisão) e Precision (foco).

```text
Antes de escrever, analise o relato passo a passo. NÃO escreva esta análise na resposta...
5. Fatos: liste mentalmente cada fato concreto do relato (valores, endpoints, códigos HTTP,
   plataformas, ...). Todos os fatos relevantes devem aparecer na resposta, sem alteração.
```

### 4. Skeleton of Thought

**Por quê:** as referências do dataset têm tamanhos muito diferentes. Um bug simples tem apenas 5 critérios; um complexo tem título, critérios por problema, critérios técnicos, contexto e tasks. Uma estrutura única falharia nos dois sentidos: seções demais nos simples prejudicam Clarity e Precision, e seções de menos nos complexos prejudicam o F1.

**Como apliquei:** o modelo classifica o relato como SIMPLES, MÉDIO ou COMPLEXO e preenche o **esqueleto** correspondente. No nível MÉDIO, as seções extras (`Critérios Adicionais`, `Exemplo de Cálculo`, `Critérios Técnicos`, `Contexto Técnico`/`Contexto de Segurança`) só aparecem quando o relato tem material para elas.

### Demais requisitos do prompt otimizado

- **Regras explícitas:** 10 regras de escrita (primeira linha obrigatória, Given-When-Then, quantidade de critérios por nível, repetir números exatamente, não inventar fatos, sem Markdown/código, português do Brasil).
- **Edge cases:** relato vago (seção `Pontos a Esclarecer:`), vários bugs independentes, pedido de feature em vez de bug, **prompt injection** e código no relato (ex: o `<script>` do caso de XSS é tratado como dado), entrada vazia ou sem relação com software e dados sensíveis.
- **System vs User:** o system prompt traz tudo que é fixo (persona, processo, regras, exemplos). O user prompt traz só a tarefa e o `{bug_report}`, delimitado por `<relato_de_bug>`. No v1 a variável aparecia duplicada no system **e** no user.

---

## Resultados Finais

### Evidências no LangSmith

> ⚠️ **Pendente:** preencher depois de executar `python src/evaluate.py` com as credenciais.

- **Dataset público de avaliação (com os experimentos):** `<link gerado por share_dataset>`
- **Prompt publicado:** `https://smith.langchain.com/hub/<USERNAME_LANGSMITH_HUB>/bug_to_user_story_v2`

Para gerar o link público (rode **uma vez**: compartilhar de novo muda o link):

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; from langsmith import Client; print(Client().share_dataset(dataset_name=os.environ['LANGSMITH_PROJECT'] + '-eval')['url'])"
```

### Notas

| Métrica | v1 (original) | v2 (otimizado) |
|---|---|---|
| Helpfulness | _a preencher_ | _a preencher_ |
| Correctness | _a preencher_ | _a preencher_ |
| F1-Score | _a preencher_ | _a preencher_ |
| Clarity | _a preencher_ | _a preencher_ |
| Precision | _a preencher_ | _a preencher_ |

### Screenshots

Salve as imagens em `docs/screenshots/` e referencie aqui:

- Resultado do `evaluate.py` no terminal com todas as métricas ≥ 0.8
- Experimento no LangSmith (notas por exemplo)
- Tracing detalhado de pelo menos 3 exemplos (um simples, um médio e um complexo)

### Histórico de iterações

| Iteração | Mudança no prompt | Resultado |
|---|---|---|
| 1 | v2 inicial: persona, CoT interno, esqueletos por complexidade, 3 exemplos few-shot, edge cases | _a preencher_ |

### Comparação v1 × v2

| Aspecto | v1 | v2 | Por quê |
|---|---|---|---|
| Persona | "assistente que ajuda" | Product Owner Sênior com background técnico | Define padrão de qualidade e vocabulário |
| Formato de saída | Não especificado | Template "Como um / eu quero / para que" + Given-When-Then | Aproxima a resposta da referência (F1, Clarity) |
| Exemplos | Nenhum | 3 (simples, médio, complexo) | Mostrar o formato é mais eficaz do que descrevê-lo |
| Nível de detalhe | Igual para tudo | Esqueleto por complexidade | Evita excesso em bugs simples e falta em complexos |
| Fidelidade | Sem regra | "Não invente fatos" + "repita os números exatamente" | Reduz alucinação (Precision) e omissão (F1) |
| Raciocínio | Nenhum | CoT em 6 passos, não impresso | Melhora persona/benefício sem poluir a saída |
| Edge cases | Nenhum | 6 casos tratados (incluindo prompt injection) | Robustez em entradas reais |
| System × User | `{bug_report}` duplicado nos dois | System = instruções fixas; User = tarefa + relato delimitado | Separação de responsabilidades e menos ruído |
| Saída | Terminava em "User Story gerada:" (convite a texto livre) | "Responda apenas com a User Story final" | Sem introduções nem comentários |

---

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com) com API key e **handle público** do Hub (veja abaixo)
- API key da [OpenAI](https://platform.openai.com/api-keys) **ou** do [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini)

### 1. Ambiente

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Preencha no `.env`:

| Variável | Descrição |
|---|---|
| `LANGSMITH_API_KEY` | Chave do LangSmith |
| `LANGSMITH_PROJECT` | Nome do projeto; o dataset será `{LANGSMITH_PROJECT}-eval` |
| `USERNAME_LANGSMITH_HUB` | Seu handle público do Hub |
| `LLM_PROVIDER` | `openai` ou `google` |
| `OPENAI_API_KEY` / `GOOGLE_API_KEY` | Chave do provider escolhido |
| `LLM_MODEL` | Modelo que gera as User Stories (precisa aceitar `temperature=0`) |
| `EVAL_MODEL` | Modelo juiz (pode ser o mesmo ou um mais capaz) |

**Handle do Hub:** ele só passa a existir quando você torna um prompt público pela primeira vez. Em LangSmith → Prompts, abra ou crie um prompt, clique nos três pontinhos ao lado de **Playground** → **Make Public** → escolha o handle. O handle é definitivo.

### 3. Fases

```bash
# Fase 1 — pull do prompt original → prompts/bug_to_user_story_v1.yml
python src/pull_prompts.py

# Fase 2 — validar o prompt otimizado (prompts/bug_to_user_story_v2.yml)
pytest tests/test_prompts.py -v

# Fase 3 — push público do v2 para {USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2
python src/push_prompts.py

# Fase 4 — avaliação (cria um experimento no LangSmith e imprime as notas)
python src/evaluate.py
```

Para iterar: edite `prompts/bug_to_user_story_v2.yml` (e atualize `changelog`) → `pytest` → `push_prompts.py` → `evaluate.py`. Cada push vira um novo commit do prompt no Hub, e cada avaliação gera um novo experimento comparável no dashboard.

### O que cada script faz

- **`src/pull_prompts.py`:** `client.pull_prompt("leonanluppi/bug_to_user_story_v1", dangerously_pull_public_prompt=True)`, extrai o texto das mensagens system/human do `ChatPromptTemplate` e salva em YAML.
- **`src/push_prompts.py`:** lê o YAML, valida (campos obrigatórios, sem TODOs, ≥ 2 técnicas, `user_prompt` não vazio e **apenas** a variável `{bug_report}` no template), monta `ChatPromptTemplate` (system + user) e faz `push_prompt(..., is_public=True)` com descrição, readme, tags (incluindo `technique:*`) e descrição do commit.
- **`tests/test_prompts.py`:** os 6 testes exigidos, mais 3 de proteção: `{bug_report}` só no user prompt, nenhuma chave solta no template e o validador do projeto.
- **`src/evaluate.py`, `src/metrics.py`, `src/utils.py`:** fornecidos pelo desafio (não alterados).

### Estrutura

```text
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt original (pull)
│   └── bug_to_user_story_v2.yml   # prompt otimizado
├── datasets/bug_to_user_story.jsonl
├── src/
│   ├── pull_prompts.py
│   ├── push_prompts.py
│   ├── evaluate.py
│   ├── metrics.py
│   └── utils.py
└── tests/test_prompts.py
```
