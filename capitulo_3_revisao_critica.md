# Revisão Crítica — `capitulo_3_metodologia.md`

**Revisão 5 — encerramento · 27/07/2026** · substitui as revisões anteriores
**Base:** capítulo em 293 linhas (16:45) · `scripts/` · git `e2344c0`

> **Escopo.** Pipeline em produção no GCP; esta sessão não acessa GCS nem BigQuery. Verificações sobre código, evidências versionadas e texto.

---

## 0. Veredito: o capítulo está pronto no que importa

O desenho metodológico está **fechado e defensável**. Não há mais nenhuma divergência entre o que o capítulo afirma e o que o código faz nos pontos centrais — variável dependente, protocolo experimental, hiperparâmetros e modelo estatístico.

Resta **uma questão de comparabilidade de dados** (§2, importante e fácil de tratar em uma frase) e uma lista de **limpezas textuais** (§3). Nenhuma delas é de desenho.

**O que fechou nesta rodada:**

| Item | Verificação |
| :--- | :--- |
| **§3.7 restaurada e coerente** | Equação com $\beta_1..\beta_5$, lista das 5 variáveis em notação $X_{kit}$, diagrama e fórmula do ARS — os quatro alinhados (linhas 237, 241-246, 248-269, 274). |
| **`system_instruction` neutra** | `extract_agent_responses.py:99-102`, aplicada em `call_gemini` (`:117`) e `call_gemini_grounded` (`:139`). |
| **Prompt não contamina mais a resposta** | `contents=query` — o system prompt antigo ("*be specific about prices*") saiu do corpo da mensagem. |
| **Tier 3 marcado como não instrumentado** | §3.6.3, tabela — resolve o nível ordinal vazio sem perder a contribuição conceitual. |
| **Prompts dos Níveis 2 e 3 sem indução de marca** | Reescritos no capítulo **e** no código (`level_2_channel`, `level_3_attributes`) — a alegação de *Unbiased Prompt Engineering* agora se sustenta. |
| **CTS discrimina (medido na revisão anterior)** | 924 pares: Tier 0 = 69,0%, Tier 1 = 19,4%, Tier 2 = 11,6%. Das 286 menções, 63% Tier 1 e 37% Tier 2. **107 eventos** — folga confortável na regra de 10 eventos por variável, com 5 preditores. |

---

## 1. 🟠 Duas asserções do capítulo que o código ainda não sustenta

### 1.1 `evidencias/` continua sem as capturas do sidebar
§3.6.2 (linha 174) e o diagrama (linha 189) dizem que o Deslocamento de Canal está *"arquivado em `evidencias/`"*. A pasta tem 12 arquivos, todos de 19/07: `resultado_teste_meli.png`, 5 `robots_*` e 5 exports de Trends. Busca por `*sidebar*` / `*gemini*` / `*shopping*` no repositório = 0.

É o único ponto do capítulo que promete evidência inexistente. Arquivar os prints (data, prompt, SKU) ou trocar por "observado em testes exploratórios de interface".

### 1.2 O *fallback* CrUX → PageSpeed agora é afirmado em dois lugares
A definição de $X_{3it}$ (linha 244) passou a incluir *"com fallback de laboratório PageSpeed quando o CrUX for nulo"*, o que reforça a §3.3.1 (linha 86). Mas a regra continua **não implementada**: `is_crux_field_data` só existe como item não marcado em `linear_backlog.md:72`, e não há lógica de fallback em `extract_crux.py` nem em `extract_pagespeed.py`.

Implementar (algumas horas) ou mudar para tempo futuro nos dois pontos. Se implementar, a flag precisa entrar como controle no modelo — dado de campo e dado de laboratório não são a mesma variável.

*(Nota menor: a definição de $X_{2it}$ na linha 243 menciona só bloqueio WAF, enquanto a §3.4 trata WAF **e** `robots.txt`. Uniformizar.)*

---

## 2. 🟠 Ponto novo — quebra de regime de prompt no meio do painel

A troca do `SYSTEM_PROMPT` ("*You are a helpful shopping assistant… be specific about store names, prices…*") pela `SYSTEM_INSTRUCTION` neutra é metodologicamente **correta** — elimina o viés de persona que eu havia apontado como limitação. Mas ela cria uma descontinuidade:

- **Regime A** (execuções antigas): persona de assistente de compras, instrução em inglês, prompt concatenado ao corpo da mensagem, temperatura *default*.
- **Regime B** (execuções novas): instrução neutra em português, `system_instruction` própria, `temperature = 0.0`.

Respostas dos dois regimes **não são comparáveis** — o Regime A induzia explicitamente citação de loja e preço, que é justamente o que o CTS mede. Empilhar tudo no mesmo painel longitudinal contaminaria os coeficientes.

**Ação (uma frase no capítulo + um filtro na consulta):** declarar a data/`run_str` de corte e usar **apenas as execuções do Regime B** no painel de modelagem. As execuções do Regime A viram fase-piloto — e continuam citáveis como evidência exploratória (o caso do *knowledge cutoff* do iPhone 17 Pro, por exemplo).

Isso também resolve, de uma vez, a questão dos SKUs de eletrônicos: eles ficam do lado do piloto.

*Nota de código:* o `SYSTEM_PROMPT` antigo continua no arquivo, hoje usado só por `call_claude` (caminho morto — a API não tem saldo). Dois prompts de sistema no mesmo script confundem quem for replicar. Vale remover ou comentar.

---

## 3. ⬜ Limpezas textuais pendentes (~1 hora, todas)

| # | Item | Linha |
| :-- | :--- | :--- |
| 1 | "Vistas SQL Nativas / BigQuery Views" — contradiz a §3.5, que está correta | 3, 13, 69, 96 |
| 2 | Playwright como estágio de pipeline — a §3.4 já o trata como teste diagnóstico | 13, 63, 95, 287 |
| 3 | §3.8 "Eletrônicos e Skincare" contradiz a §3.2 (resolve junto com o §2 acima) | 286 |
| 4 | Hero cluster: Sallve 35g, Natura 15ml, Neutrogena Hydro Boost 50g violam "estritamente padronizado"; nomes divergem de `urls.json` (ADCOS C15 × C20; Dermage 30g × 30ml) | §3.2 |
| 5 | §3.6.1 descreve 3 níveis; o código tem 6 `query_type` (`product_exact` 10, `brand` 4, `level_1_control` 2, `level_2_channel` 2, `level_3_attributes` 2, `generic` 2), com `generic` e `level_1_control` sobrepostos | §3.6.1 |
| 6 | `urls.json`: Mercado Livre como `Marketplace` **e** `Especialista`; Droga Raia como `Especialista` **e** `Farma/especialista` — contamina $X_5$ | `urls.json` |
| 7 | `llms.txt` coletado a cada execução, resultado nunca reportado | §3.4 |
| 8 | `citation_sentiment` calculado e gravado, nunca definido no capítulo | §3.6.3 |
| 9 | Google Trends em `evidencias/` — seria a base empírica de §3.2, hoje sustentada por "ABIHPEC / Euromonitor" sem ano nem referência | §3.2 |

---

## 4. As seções que faltam (o trabalho que sobra)

Não são correções — são texto novo, e é o que separa um capítulo correto de um capítulo completo:

1. **Unidade de análise e composição amostral.** Você já tem os números: 10 SKUs × 2–3 lojas = 26 pares loja×SKU, 16 lojas distintas, 22 queries × 4 configurações por execução $t$, ~107 eventos. Falta dizer **o que é uma observação** e qual a janela de execuções (ver §2).
2. **Dicionário de variáveis** — origem (tabela/campo no BigQuery) e tratamento de nulos por variável. A §3.7.2 restaurada já é 70% disso.
3. **Hipóteses formais** $H_1..H_5$ com sinal esperado de cada $\beta_k$.
4. **Limitações** — viés geográfico (`us-central1` nas chamadas Vertex, enquanto a Cloud Function roda em `southamerica-east1`); fornecedor único (Gemini) e a falha do Claude por saldo; não-reprodutibilidade de LLM mesmo com $T=0$; usar `model_used` e nunca `agent` (fallback mascara o rótulo); desalinhamento CrUX 28 dias × PageSpeed × resposta; MNAR de $X_1$ condicional a $X_2$; quebra de regime de prompt (§2).
5. **Ética / LGPD / termos de uso** — indispensável num trabalho sobre `robots.txt` e bloqueio de bots: se o coletor próprio respeitou as diretivas, sob qual base, com que taxa de requisição, sem dados pessoais.
6. **Validação do modelo** — pseudo-$R^2$, AUC, calibração, VIF (TTFB e LCP são estruturalmente correlacionados).

---

## 5. Fechamento

Do ponto de vista de **coerência interna e de correspondência entre texto e implementação**, o Capítulo 3 está resolvido. O que sobra é: uma decisão de recorte amostral (§2), nove limpezas de texto (§3) e seis seções a escrever (§4) — nada disso depende de rediscutir metodologia.

E vale registrar o que ficou bom, porque é o que sustenta a defesa:

- **O CTS é a contribuição metodológica do trabalho.** Separar menção genérica de menção com contexto de compra, e ambas de recuperação efetiva no grounding, é mais fino do que a literatura de *answer engines* costuma fazer — Baeza-Yates et al. auditam o **output** do agente; você mede o **input**, a prontidão da PDP. A janela de ±250 caracteres é a operacionalização que sustenta isso, e a distribuição empírica por tier prova que a escala discrimina. Isso merece um parágrafo explícito de posicionamento no capítulo.
- **A §3.4 é o padrão de rigor**: separa bloqueio declarado (`robots.txt`) de bloqueio imposto (WAF), prova o segundo com teste controlado e arquiva a evidência.
- **A §3.6.4 nova** (instrução neutra + hiperparâmetros justificados) é exatamente o nível de detalhe que uma banca pede para aceitar reprodutibilidade em experimento com LLM.

---

## Anexo — Verificações desta revisão

| Verificação | Fonte |
| :--- | :--- |
| §3.7 coerente (5 β, 5 variáveis, diagrama, ARS) | capítulo, linhas 237 / 241-246 / 248-269 / 274 |
| `SYSTEM_INSTRUCTION` neutra aplicada | `extract_agent_responses.py:99-102`, `:117`, `:139` |
| `contents=query` (sem prompt concatenado) | `extract_agent_responses.py:120`, `:143` |
| `temperature=0.0` nas duas funções | `extract_agent_responses.py:116`, `:138` |
| `SYSTEM_PROMPT` antigo ainda no arquivo (só `call_claude`) | `extract_agent_responses.py:76-79`, `:93` |
| Prompts Níveis 2 e 3 presentes no código | busca por "site da marca" e "textura leve" = encontrados |
| 6 `query_type` no código | `extract_agent_responses.py` |
| Tier 3 marcado como não instrumentado | capítulo, §3.6.3 |
| Distribuição do CTS (924 pares) | reexecução da regra sobre `extractions/agent-responses/*/*/responses_2*.json` |
| Sem capturas do sidebar | `evidencias/` (12 arquivos, todos 19/07); `find` = 0 |
| `is_crux_field_data` não implementado | grep no repo → só `linear_backlog.md:72` (não marcado) e o capítulo |
| Conflitos de canal | `urls.json` — ML {Marketplace, Especialista}; Droga Raia {Especialista, Farma/especialista} |
| Cobertura e recência dos dados | **não verificável nesta sessão** |
