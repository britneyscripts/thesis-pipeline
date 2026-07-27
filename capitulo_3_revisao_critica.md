# Revisão Crítica — `capitulo_3_metodologia.md`

**Revisão 3 (final) — 27/07/2026** · substitui as revisões anteriores
**Base:** capítulo em 287 linhas (15:35) + `scripts/` (15:05) + `requirements.txt` (15:05) + `urls.json` (14:05) + `evidencias/` + git (`6a5a2b3`)

> **Escopo desta verificação.** A pipeline roda em produção no GCP (Cloud Function `run-pipeline`, `southamerica-east1`, GCS `ghostprod-extractions` + BigQuery `thesisusp`). Esta sessão **não tem acesso a GCS nem ao BigQuery** — logo, nada é afirmado aqui sobre volume, cobertura ou recência dos dados coletados. Tudo abaixo se refere a **código, configuração, evidências versionadas e ao texto do capítulo**, que são idênticos local e em produção.

---

## 0. Veredito

A rodada resolveu os pontos estruturais mais pesados. O capítulo passou a ter uma variável dependente formalizada (CTS), uma regra de binarização explícita, um modelo GEE com estrutura de correlação declarada, uma tabela `robots.txt` correta e uma pilha de dependências que bate com o texto. Em termos de **desenho**, o Capítulo 3 está defensável.

O que sobrou concentra-se em dois eixos:

1. **Definição × implementação.** Três das cinco regras do CTS não fazem, no código, o que o capítulo diz que fazem. Uma delas — a fronteira Tier 1/Tier 2 — **anula na prática toda a hierarquia** (demonstrado empiricamente na §2). Este é o único achado bloqueante desta revisão.
2. **Consistência interna e seções ausentes.** A §3.7 ganhou GEE mas ficou com a equação e as variáveis desalinhadas; e as seções de unidade de análise, amostra, limitações e ética continuam não existindo.

| Status | Qtd. |
| :--- | :---: |
| ✅ Resolvido nesta rodada | 8 |
| 🔴 Bloqueante (definição ≠ implementação) | 1 |
| 🟠 Alto (inconsistência interna nova ou afirmação sem lastro) | 6 |
| ⬜ Pendente das revisões anteriores | 9 |

---

## 1. ✅ Resolvido nesta rodada

| Item | Verificação |
| :--- | :--- |
| **CTS formalizado e renomeado** | §3.6.3 — a colisão de nomes com o ARS acabou. |
| **Regra de binarização explícita** | §3.6.3 — $Y_{it}=1 \iff \text{CTS}_{it} \ge 50$. Resolve a contradição ordinal × binário. |
| **GEE declarado com estrutura de correlação** | §3.7 — logística binomial via GEE com matriz AR(1) para medidas repetidas em $t$. |
| **`grounding_uris` persistido no BigQuery** | `load_to_bigquery.py:478` (`REPEATED`) e `:604` (mapeamento). |
| **Tiers implementados** | `load_to_bigquery.py:492-493` (schema) e `:641-700` (cálculo). |
| **`requirements.txt` alinhado ao capítulo** | agora inclui `numpy`, `statsmodels`, `playwright`. |
| **§3.4 — contagem e célula do ML corrigidas** | "três fatores" ✓; ML / Google-Extended → "Não (ausente do robots.txt)" ✓. |
| **§3.6.2 rebaixada a observação qualitativa + ressalva de escopo** | O bloco sobre CTR/conversão é uma boa antecipação de pergunta de banca. |

---

## 2. 🔴 BLOQUEANTE — a regra Tier 1 × Tier 2 anula a hierarquia

**O capítulo diz** (§3.6.3, Tier 2): *"O nome do produto **E** a loja de destino específica são citados no texto do chat"*.

**O código faz** (`load_to_bigquery.py:674-681`):

```python
elif text_mentioned:
    if any(kw in text_lower for kw in ["r$", "reais", "preço", "preco", "loja", "site", "comprar"]):
        citation_tier = 2; citation_score = 50
    else:
        citation_tier = 1; citation_score = 25
```

Três defeitos, em ordem de gravidade:

**(a) O teste é da resposta inteira, não da loja.** `text_lower` é o texto completo. Se a resposta contém "R$" *em qualquer lugar*, **toda loja mencionada nela** recebe Tier 2 — inclusive a loja citada de passagem, sem produto e sem contexto de compra.

**(b) O nome do produto nunca é verificado.** O critério do capítulo ("produto E loja") não está implementado em nenhum ponto.

**(c) Na prática, o Tier 1 é código morto.** Rodei o gatilho sobre as respostas reais disponíveis:

```
respostas com texto: 42 | contendo ≥1 keyword de Tier 2: 42 (100%)
```

**100% das respostas** disparam o gatilho — o que é esperado, já que o `SYSTEM_PROMPT` pede explicitamente preços e nomes de loja. Ou seja: toda loja mencionada vira Tier 2 (50 pts), e como a binarização é $Y=1 \iff \text{CTS} \ge 50$, **$Y$ colapsa para "o nome da loja apareceu em algum lugar do texto"** — exatamente a medida ingênua que o sistema de tiers foi criado para substituir.

O CTS existe no papel e no schema, mas não discrimina nada.

**Correção mínima (algumas horas, e destrava o Capítulo 4):** avaliar o contexto **na vizinhança da menção**, não na resposta inteira, e exigir o produto.

```python
# Janela de ±250 caracteres ao redor de CADA ocorrência do alias
for m in re.finditer(rf"\b{re.escape(alias)}\b", text_lower):
    janela = text_lower[max(0, m.start()-250): m.end()+250]
    tem_produto = any(tok in janela for tok in tokens_produto(sku))   # ex.: "vitamina c", "sérum", "30ml"
    tem_compra  = any(kw in janela for kw in ["r$", "comprar", "site oficial", "loja oficial"])
    if tem_produto and tem_compra:
        tier = 2; break
```

E **documentar a janela e a lista de tokens no capítulo** — sem isso, o critério não é replicável. Depois de corrigir, vale reportar a distribuição do CTS por tier: se Tier 1 continuar vazio, o problema é outro; se aparecer, a hierarquia está funcionando.

---

## 3. 🟠 Outros descompassos entre §3.6.3 e o código

### 3.1 Tier 4 não verifica a PDP monitorada
**Capítulo:** *"A **URL exata da PDP monitorada** é indexada e retornada nos metadados"*.
**Código** (`:646-653`): testa `alias in uri` — se o **nome da loja** aparece como substring da URI.

São coisas diferentes. Um `grounding_uri` apontando para a home da Natura, para um blog post ou para uma categoria conta como Tier 4. E o `urls.json` — que contém a URL monitorada — nunca é consultado nessa comparação.

Correção: normalizar e comparar contra a URL de `urls.json` (sem query string, sem barra final). Se quiser manter os dois níveis, vale distinguir *Tier 4 — PDP exata* de *Tier 3.5 — domínio da loja grounded*, que é informação legítima e diferente.

Risco adicional de falso positivo: aliases curtos em *substring* de URI — `raia`, `natura`, `apple`, `vivo`, `botik` casam com domínios de terceiros (`naturaesaude.com.br`, `appleinsider…`).

### 3.2 Tier 3 é inalcançável
Nenhum ramo do código atribui `citation_tier = 3`. A fonte declarada no capítulo ("Painel Lateral GMC API") não existe como coletor — e a §3.6.2 já admite que o sidebar é observação qualitativa.

Uma escala ordinal com um nível estruturalmente vazio é frágil em banca. Duas saídas: (i) marcar o Tier 3 explicitamente como **não instrumentado nesta versão do estudo** na própria tabela, ou (ii) removê-lo e renumerar para 4 níveis. A opção (i) preserva a contribuição conceitual e é honesta.

### 3.3 Assimetria não documentada no casamento de texto
`:656-664`: aliases com ≤4 caracteres usam `\b…\b` (limite de palavra); acima de 4, usam substring simples. Então `amazon` casa dentro de `amazonas`, `sallve` dentro de qualquer composto. É uma regra de medida — precisa estar no capítulo ou ser uniformizada para regex com limite de palavra em todos os casos.

### 3.4 `citation_sentiment` continua sem definição no capítulo
O campo é calculado (`get_citation_sentiment`) e gravado, mas o capítulo nunca diz o que é, como é classificado, nem qual a confiabilidade. Ou entra com critério, ou sai da tabela.

---

## 4. 🟠 §3.7 — inconsistências internas introduzidas pela reescrita

A migração para GEE foi feita na abertura e na equação, mas o resto da seção ficou na versão antiga:

| # | Problema | Onde |
| :-- | :--- | :--- |
| 1 | **A equação tem 4 coeficientes ($\beta_1..\beta_4$), a lista tem 5 variáveis e o ARS soma até $k=5$** | linha 229 vs. 235-239 vs. 268 |
| 2 | **"Onde: $Y_i$… indicadora binária de citação (1 = Loja citada)"** — texto anterior ao CTS; deveria remeter a $\text{CTS}_{it} \ge 50$ e usar $Y_{it}$ | linha 232 |
| 3 | **Notação mista**: $X_{1it}$ na equação, $X_{1i}$ na lista, $X_{ki}$ no ARS | 229 / 235-239 / 268 |
| 4 | **$\varepsilon_{it}$ na equação do logito** — GEE é modelo marginal com função de ligação; não há termo de erro aditivo na escala do logito. Um avaliador quantitativo marca isso. | linha 229 |
| 5 | **A unidade de cluster do GEE não é declarada** — agrupa por loja? loja×SKU? loja×query? É o parâmetro que define os erros-padrão. | §3.7 |
| 6 | **AR(1) não é justificada** — pressupõe medidas repetidas ordenadas e aproximadamente equiespaçadas. Com execuções 3×/dia e janela móvel de 28 dias do CrUX, isso precisa de uma frase de justificativa (ou trocar por `exchangeable`, que é mais conservador). | §3.7 |

Nada aqui é difícil: é uma passada de meia hora na seção para alinhar equação, lista, diagrama e fórmula do ARS — e decidir se $X_5$ entra ou sai (se saiu por parcimônia/EPV, ótimo, mas então some da lista, do diagrama e do somatório).

---

## 5. 🟠 §3.6.2 afirma capturas de tela que não existem

O texto (linha 174) diz que o deslocamento de canal foi *"documentado via inspeção visual exploratória e **capturas de tela arquivadas em `evidencias/`**"*, e o diagrama repete *"(Arquivado em evidencias/)"*.

Conteúdo real de `evidencias/` (12 arquivos): `resultado_teste_meli.png` (o teste do Playwright), 5 arquivos `robots_*`, e 5 exports de Google Trends/keywords. **Nenhuma captura do painel lateral do Gemini.** Busca por `*sidebar*`, `*gemini*`, `*shopping*` no repositório = 0 resultados.

É o tipo de afirmação que a banca checa em 30 segundos, e agora ela está escrita no capítulo. Duas saídas: **arquivar os prints** (com data, prompt usado e SKU) — o caminho certo, porque a observação é valiosa — ou reescrever para "observado durante testes exploratórios de interface", sem prometer arquivo.

---

## 6. ⬜ Pendências das revisões anteriores (não tocadas)

Todas de correção barata, exceto as duas últimas:

| # | Item | Onde |
| :-- | :--- | :--- |
| 1 | **"Vistas SQL Nativas / BigQuery Views"** — contradiz a §3.5, que está correta | linhas 3, 13, 69, 96 |
| 2 | **`is_crux_field_data`** descrito como implementado; segue como item não marcado em `linear_backlog.md:72` | linha 86 |
| 3 | **Playwright** ainda como estágio de pipeline (agora só é teste diagnóstico, conforme a própria §3.4) | linhas 13, 63, 95, 281 |
| 4 | **§3.8 "Eletrônicos e Skincare"** — contradiz a §3.2 | linha 280 |
| 5 | **Hero cluster**: Sallve 35g, Natura 15ml e Neutrogena Hydro Boost 50g (não é sérum de vitamina C) violam o critério "estritamente padronizado"; nomes divergem de `urls.json` (ADCOS C15 × C20; Dermage 30g × 30ml) | §3.2 |
| 6 | **§3.6.1**: capítulo descreve 3 níveis; o código tem **6** `query_type` (`product_exact` 10, `brand` 4, `level_1_control` 2, `level_2_channel` 2, `level_3_attributes` 2, `generic` 2) — com `generic` e `level_1_control` semanticamente sobrepostos | §3.6.1 |
| 7 | **`urls.json`**: Mercado Livre classificado como `Marketplace` e `Especialista`; Droga Raia como `Especialista` e `Farma/especialista` — contamina $X_5$ | `urls.json` |
| 8 | **`llms.txt`**: coletado a cada execução, resultado nunca reportado | §3.4 |
| 9 | **Google Trends em `evidencias/`** não documentado — seria a base empírica da escolha do cluster em §3.2, hoje sustentada por "ABIHPEC / Euromonitor" sem ano nem referência | §3.2 |

**E as seções que continuam ausentes** — estas não são cosméticas:

- **Unidade de análise e composição amostral**: $n$, período, frequência, e o que é uma observação (loja? loja×SKU? loja×SKU×execução? loja×query×modelo?). É a primeira pergunta de uma banca quantitativa, e o capítulo não responde. Ordem de grandeza atual: 10 SKUs × 2–3 lojas = **26 pares loja×SKU**, 16 lojas distintas — com 5 preditores, o problema de eventos por variável precisa ser enfrentado explicitamente (reduzir preditores, penalização de Firth, ou assumir o ARS como índice descritivo).
- **Dicionário de variáveis** (definição operacional + tabela/campo de origem + tratamento de nulos) e **hipóteses formais** $H_1..H_5$ com sinal esperado.
- **Limitações**: viés geográfico (`location="us-central1"`, `extract_agent_responses.py:103` e `:120`, enquanto a Cloud Function roda em `southamerica-east1`); fornecedor único (só Gemini) e a falha do Claude por saldo; não-reprodutibilidade de LLMs mesmo com $T=0$; fallback de modelo mascarando o rótulo (usar `model_used`, nunca `agent`); desalinhamento temporal CrUX (28 dias) × PageSpeed × resposta; missingness MNAR ($X_1$ só observável quando $X_2=1$); pseudo-replicação do CrUX; e o `SYSTEM_PROMPT` em inglês pedindo preços, que induz parte da alucinação depois reportada como achado.
- **Ética / LGPD / termos de uso**: obrigatória num trabalho cujo objeto é `robots.txt` e bloqueio de bots. Declarar se o coletor próprio respeitou as diretivas, sob qual base, com que taxa de requisição e sem dados pessoais.
- **Validação do modelo**: pseudo-$R^2$, AUC, calibração, VIF (TTFB e LCP são estruturalmente correlacionados), holdout.

---

## 7. Checklist de prontidão para a banca

**Bloqueante — fazer antes do Capítulo 4:**

- [ ] Corrigir a regra Tier 1 × Tier 2 para janela de contexto + token de produto (§2)
- [ ] Tier 4 comparar contra a URL de `urls.json`, não contra o nome da loja (§3.1)
- [ ] Recarregar `agent_citations` e conferir a distribuição por tier
- [ ] Alinhar §3.7: equação, lista de variáveis, diagrama e fórmula do ARS (§4)

**Alto — antes de entregar o capítulo:**

- [ ] Arquivar os prints do sidebar ou reescrever a §3.6.2 (§5)
- [ ] Declarar cluster do GEE e justificar AR(1)
- [ ] Marcar o Tier 3 como não instrumentado
- [ ] Escrever §Unidade de Análise + composição amostral
- [ ] Escrever §Limitações e §Ética/LGPD
- [ ] Itens 1 a 4 e 6 a 8 da tabela da §6 (correções textuais, ~1 h no total)

**Recomendado:**

- [ ] Documentar o critério de `citation_sentiment` ou removê-lo
- [ ] Unificar o enum de canais em `urls.json` e declarar a regra de $X_5$
- [ ] Commitar e tagear a versão que gerou os dados analisados, e citá-la no capítulo
- [ ] Incorporar os dados de Google Trends como fonte secundária em §3.2

---

## 8. O que está forte — e vale dizer no texto

- **O CTS é a contribuição metodológica do capítulo.** Separar menção de marca, menção com contexto de compra, oferta transacional e URI efetivamente recuperada é uma operacionalização mais fina do que a literatura de *answer engines* usa: Baeza-Yates et al. auditam o **output** do agente; você mede o **input** (a prontidão da PDP) com granularidade. Isso merece um parágrafo explícito de posicionamento, não ficar implícito numa tabela.
- **A ressalva de escopo da §3.6.2** (visibilidade estrutural × tráfego não observável) antecipa a pergunta mais provável da banca sobre o Deslocamento de Canal. Boa adição.
- **A §3.4 está metodologicamente limpa**: separa bloqueio declarado (`robots.txt`) de bloqueio imposto (WAF) e prova o segundo com um teste controlado e evidência arquivada. É o padrão que as outras seções deveriam seguir.

---

## Anexo — Verificações desta revisão

| Verificação | Fonte |
| :--- | :--- |
| Tiers implementados | `load_to_bigquery.py:641-700`; schema em `:492-493` |
| Gatilho Tier 2 dispara em 100% das respostas | teste sobre `extractions/agent-responses/*/*/responses_2*.json` → 42/42 |
| Tier 2 não checa nome de produto | `load_to_bigquery.py:674-677` |
| Tier 4 casa alias × URI, não a PDP monitorada | `load_to_bigquery.py:646-653` |
| Tier 3 nunca atribuído | grep `citation_tier = 3` = 0 |
| Assimetria ≤4 chars regex / >4 substring | `load_to_bigquery.py:656-664` |
| `grounding_uris` no schema | `load_to_bigquery.py:478`, `:604` |
| `requirements.txt` atualizado | numpy, statsmodels, playwright presentes |
| Sem capturas do sidebar | `ls evidencias/` (12 arquivos); `find` por `*sidebar*`/`*gemini*`/`*shopping*` = 0 |
| §3.7 com 4 β e 5 variáveis | capítulo, linhas 229 / 235-239 / 268 |
| 6 `query_type` no código | `extract_agent_responses.py` |
| Conflitos de canal | `urls.json` — ML {Marketplace, Especialista}; Droga Raia {Especialista, Farma/especialista} |
| Views / `is_crux_field_data` / Playwright / "Eletrônicos" | capítulo, linhas 3, 13, 69, 96 / 86 / 63, 95, 281 / 280 |
| Cobertura e recência dos dados | **não verificável nesta sessão** (sem acesso a GCS/BigQuery) |
