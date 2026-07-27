# Revisão Crítica — `capitulo_3_metodologia.md`

**Revisão 4 (final) — 27/07/2026** · substitui as revisões anteriores
**Base:** capítulo em 253 linhas (15:53) · `scripts/load_to_bigquery.py` (15:52) · git `e175806`

> **Escopo.** A pipeline roda em produção no GCP (Cloud Function `run-pipeline`, `southamerica-east1`, GCS + BigQuery `thesisusp`). Esta sessão **não acessa GCS nem BigQuery** — nada é afirmado sobre volume, cobertura ou recência do dataset. As verificações abaixo são de **código, evidências versionadas e texto do capítulo**.

---

## 0. Veredito

**A correção do CTS funcionou — está medida e comprovada abaixo (§1).** Era o único bloqueante da revisão anterior, e ele caiu.

Mas a edição da §3.7 **apagou a seção de variáveis independentes**. O capítulo hoje apresenta uma equação com $\beta_1..\beta_4$, termina com um "Onde:" vazio, pula da §3.7.1 para a §3.7.3 e calcula o ARS somando até $k=5$ — **sem definir $X_1$ a $X_5$ em lugar nenhum**. É uma regressão de edição, não de conteúdo: o texto existia na versão anterior e precisa voltar.

| Status | Qtd. |
| :--- | :---: |
| ✅ Resolvido nesta rodada | 3 |
| 🔴 Regressão de edição (bloqueante, ~20 min) | 1 |
| 🟠 Alto | 3 |
| ⬜ Pendente das revisões anteriores | 9 |

---

## 1. ✅ O CTS agora discrimina — verificado empiricamente

A nova implementação (`load_to_bigquery.py`, `process_agent_citations`) faz o que a §3.6.3 promete: janela de ±250 caracteres ao redor de **cada** ocorrência do alias, exigindo **token de produto** *e* **token de compra** dentro da janela.

Rodei a regra nova sobre as respostas reais disponíveis (42 respostas × 22 lojas = 924 pares):

| Tier | Pares | % |
| :--- | ---: | ---: |
| Tier 0 (omissão) | 638 | 69,0% |
| Tier 1 (menção genérica) | 179 | 19,4% |
| Tier 2 (produto + loja em contexto) | 107 | 11,6% |

**Das 286 menções, 63% ficam em Tier 1 e 37% sobem para Tier 2.** Na versão anterior, 100% das respostas disparavam o gatilho e *toda* menção virava Tier 2 — a hierarquia não separava nada. Agora separa.

Efeito colateral positivo para a §3.7: a taxa de eventos ($Y=1$) fica em **11,6% dos pares, ou 107 eventos**. Com 4–5 preditores, isso satisfaz confortavelmente a regra de 10 eventos por variável — o problema de EPV que eu vinha levantando **deixa de ser bloqueante**, e vale dizer isso no capítulo.

*(Ressalva: o cálculo usa as respostas disponíveis localmente, que incluem os SKUs de eletrônicos da fase anterior. A distribuição no dataset atual do BigQuery pode diferir — mas o mecanismo está demonstrado.)*

**Também resolvido nesta rodada:**

- **Tier 4 com casamento de domínio** (`/{alias}`, `.{alias}.`, `={alias}`) em vez de substring solta — elimina os falsos positivos do tipo `naturaesaude.com.br`.
- **Commit e tag** da versão do protocolo (`v2-protocolo-skincare`, commit `6aed4a9`) — resolve a rastreabilidade entre código e dados.

---

## 2. 🔴 Regressão: a §3.7.2 foi apagada

Estado atual do capítulo, linhas 227–234:

```
227  logit(P(Y_it=1)) = β₀ + β₁X₁ᵢₜ + β₂X₂ᵢₜ + β₃X₃ᵢₜ + β₄X₄ᵢₜ
229  Onde:
230  (vazio)
231  ### 3.7.3 Construção do Agent Readiness Score (ARS)
234  ARS = 1/(1+e^-(β̂₀ + Σ_{k=1}^{5} β̂ₖ X_kᵢ)) × 100
```

Quatro consequências:

1. **Nenhuma variável independente está definida no capítulo.** Schema Completeness, Bot Accessibility, TTFB, LCP e o dummy D2C sumiram do texto.
2. **"Onde:" ficou órfão**, sem nada depois.
3. **A numeração pula** de 3.7.1 para 3.7.3.
4. **A equação usa 4 coeficientes; o ARS soma 5.** A decisão sobre $X_5$ (entra ou sai) continua não resolvida — só que agora ela nem aparece.

Some-se a isso que a §3.4 (linha 121) referencia "*o bloqueio $X_2$*" — um símbolo que o capítulo não define mais.

**Ação:** restaurar a §3.7.2 com a lista das variáveis, decidir se $X_5$ entra, e alinhar equação + ARS + diagrama. É o único item bloqueante e leva ~20 minutos.

Recomendação sobre $X_5$: com 107 eventos, **cabe manter as 5 variáveis**. Nesse caso a equação volta a ter $\beta_5 X_{5it}$ e o somatório do ARS fica coerente. Aproveite para padronizar a notação em $X_{kit}$ nos três lugares (equação, lista, ARS).

Também vale, ao restaurar, acrescentar a cada variável a **origem** (tabela/campo do BigQuery) e o **tratamento de nulos** — é o embrião do dicionário de variáveis que falta.

---

## 3. 🟠 Três pontos que continuam abertos na modelagem e na medida

### 3.1 Tier 3 permanece inalcançável
Nenhum ramo atribui `citation_tier = 3` (grep = 0), e a fonte declarada ("Painel Lateral GMC API") não existe como coletor — coerente com a §3.6.2, que já classifica o sidebar como observação qualitativa. Uma escala ordinal com nível estruturalmente vazio é frágil em banca.

**Sugestão:** marcar na própria tabela da §3.6.3 — *"Tier 3 — não instrumentado nesta versão do estudo; observação qualitativa (§3.6.2)"*. Preserva a contribuição conceitual sem prometer dado que não existe.

### 3.2 Tier 4 mede domínio da loja, não a PDP monitorada
O capítulo diz *"a **URL exata da PDP monitorada**"*; o código verifica se o **alias da loja** aparece como segmento de caminho/domínio na URI. Um `grounding_uri` para a home, uma categoria ou um blog post da loja conta como Tier 4. O `urls.json` — que tem a URL monitorada — não é consultado.

Duas saídas, ambas legítimas: comparar contra a URL normalizada de `urls.json`, **ou** reescrever o critério do Tier 4 como *"domínio da loja recuperado no grounding"*, que é o que de fato se mede. O que não pode é a definição dizer uma coisa e o código fazer outra.

### 3.3 §3.6.2 continua prometendo capturas que não existem
Linha 174 e o diagrama (linha 189) afirmam que o deslocamento de canal está *"arquivado em `evidencias/`"*. A pasta segue com 12 arquivos, todos de 19/07: `resultado_teste_meli.png`, 5 `robots_*` e 5 exports de Trends. Busca por `*sidebar*`, `*gemini*`, `*shopping*` no repositório = 0.

Arquivar os prints (com data, prompt e SKU) ou remover a promessa do texto.

---

## 4. ⬜ Pendências acumuladas (correções textuais rápidas)

| # | Item | Linha |
| :-- | :--- | :--- |
| 1 | "Vistas SQL Nativas / BigQuery Views" — contradiz a §3.5, que está correta | 3, 13, 69, 96 |
| 2 | `is_crux_field_data` descrito como implementado (segue não marcado em `linear_backlog.md:72`) | 86 |
| 3 | Playwright como estágio de pipeline — a própria §3.4 já o trata como teste diagnóstico | 13, 63, 95, 247 |
| 4 | §3.8 "Eletrônicos e Skincare" contradiz a §3.2 | 246 |
| 5 | Separador `---` sumiu antes da §3.7 (as demais seções têm) | 218 |
| 6 | Hero cluster: Sallve 35g, Natura 15ml e Neutrogena Hydro Boost 50g violam o critério "estritamente padronizado"; nomes divergem de `urls.json` (ADCOS C15 × C20; Dermage 30g × 30ml) | §3.2 |
| 7 | §3.6.1 descreve 3 níveis; o código tem **6** `query_type`, com `generic` e `level_1_control` sobrepostos | §3.6.1 |
| 8 | `urls.json`: Mercado Livre como `Marketplace` **e** `Especialista`; Droga Raia como `Especialista` **e** `Farma/especialista` — contamina $X_5$ | `urls.json` |
| 9 | `llms.txt` coletado a cada execução, resultado nunca reportado | §3.4 |

**E as seções ausentes** — são o que separa "capítulo correto" de "capítulo completo":

- **Unidade de análise e composição amostral** — $n$, período, frequência, e o que é uma observação. Você já tem o número agora: 10 SKUs × 2–3 lojas = 26 pares loja×SKU, 16 lojas, ~107 eventos por rodada de análise.
- **Dicionário de variáveis** e **hipóteses formais** $H_1..H_5$ com sinal esperado.
- **Limitações** — viés geográfico (`us-central1` nas chamadas Vertex, `extract_agent_responses.py:103` e `:120`, enquanto a Cloud Function está em `southamerica-east1`); fornecedor único (Gemini) e a falha do Claude por saldo; não-reprodutibilidade de LLM mesmo com $T=0$; usar `model_used` e nunca `agent` por causa do fallback; desalinhamento CrUX (28 dias) × PageSpeed × resposta; MNAR de $X_1$ condicional a $X_2$; pseudo-replicação do CrUX; e o `SYSTEM_PROMPT` que pede preços e assim induz parte da alucinação depois reportada.
- **Ética / LGPD / termos de uso** — obrigatória num trabalho sobre `robots.txt` e bloqueio de bots.
- **Validação do modelo** — pseudo-$R^2$, AUC, calibração, VIF (TTFB e LCP são estruturalmente correlacionados).
- **`citation_sentiment`** — calculado e gravado, nunca definido no capítulo.

---

## 5. Checklist final

**Bloqueante:**

- [ ] Restaurar §3.7.2 (variáveis $X_1..X_5$), decidir sobre $X_5$, alinhar equação + ARS + diagrama (§2)

**Alto:**

- [ ] Marcar Tier 3 como não instrumentado (§3.1)
- [ ] Reconciliar a definição do Tier 4 com o que o código mede (§3.2)
- [ ] Arquivar os prints do sidebar ou remover a promessa (§3.3)
- [ ] Recarregar `agent_citations` com a regra nova e reportar a distribuição por tier no Capítulo 4
- [ ] Escrever §Unidade de Análise, §Limitações e §Ética/LGPD

**Rápido (~1 h para os nove):**

- [ ] Itens 1 a 9 da tabela da §4

---

## 6. Onde o capítulo ficou forte

- **O CTS é a contribuição metodológica do trabalho, e agora é uma medida que funciona.** Separar menção genérica de menção com contexto de compra, e ambas de recuperação efetiva no grounding, é mais fino do que a literatura de *answer engines* costuma fazer: Baeza-Yates et al. auditam o **output** do agente; você mede o **input** — a prontidão da PDP. A janela de ±250 caracteres é a operacionalização que sustenta isso, e merece um parágrafo próprio no texto, com a distribuição empírica por tier como evidência de que a escala discrimina.
- **A ressalva de escopo da §3.6.2** (fricção estrutural de visibilidade × tráfego não observável) antecipa a pergunta mais provável da banca sobre o Deslocamento de Canal.
- **A §3.4 é o padrão de rigor do capítulo**: separa bloqueio declarado (`robots.txt`) de bloqueio imposto (WAF), prova o segundo com teste controlado e arquiva a evidência. As demais seções deveriam seguir esse modelo — em particular a §3.6.2.

---

## Anexo — Verificações desta revisão

| Verificação | Fonte |
| :--- | :--- |
| Janela ±250 com produto + compra | `load_to_bigquery.py`, `process_agent_citations` |
| Distribuição por tier (924 pares) | reexecução da regra sobre `extractions/agent-responses/*/*/responses_2*.json` → T0 638 / T1 179 / T2 107 |
| Tier 4 por segmento de domínio | mesmo bloco (`/{alias}`, `.{alias}.`, `={alias}`) |
| Tier 4 não compara com `urls.json` | ausência de referência ao registro de URLs no cálculo |
| Tier 3 nunca atribuído | grep `citation_tier = 3` = 0 |
| §3.7.2 ausente; "Onde:" órfão; 3.7.1 → 3.7.3 | capítulo, linhas 227–234 |
| Equação com 4 β; ARS somando até 5 | capítulo, linhas 227 e 234 |
| $X_2$ citado sem definição | capítulo, linha 121 |
| Sem capturas do sidebar | `evidencias/` (12 arquivos, todos 19/07); `find *sidebar*|*gemini*|*shopping*` = 0 |
| Tag do protocolo | git `6aed4a9` (`v2-protocolo-skincare`), `e175806` (janela + Tier 4 + GEE) |
| Views / `is_crux_field_data` / Playwright / "Eletrônicos" | capítulo, linhas 3, 13, 69, 96 / 86 / 63, 95, 247 / 246 |
| Cobertura e recência dos dados | **não verificável nesta sessão** (sem acesso a GCS/BigQuery) |
