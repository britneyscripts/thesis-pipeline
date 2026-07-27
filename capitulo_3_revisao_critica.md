# Revisão Crítica — `capitulo_3_metodologia.md`

**Revisão 2 — 27/07/2026** (substitui a revisão de 27/07 manhã)
**Escopo:** re-verificação do capítulo após a rodada de ajustes, confrontado com o estado atual de `scripts/`, `urls.json`, `evidencias/`, `requirements.txt`, `notebooks/eda.ipynb`, `cloudbuild.yaml`, `main.py` e histórico do git.

> ### ⚠️ Limite desta revisão — leia antes
> A pipeline roda **em produção no GCP** (Cloud Function `run-pipeline`, região `southamerica-east1`, gravando em `gs://ghostprod-extractions` e em BigQuery `thesisusp`). Confirmado em `cloudbuild.yaml` e em `config.py:29-54`, onde `save_json` escolhe entre disco local e GCS conforme a variável `GOOGLE_CLOUD_PROJECT`.
>
> Desta sessão **não há acesso ao GCS nem ao BigQuery**. Portanto:
> - a pasta local `extractions/` é apenas um **espelho parcial** das execuções feitas em modo local — **não é o dataset**;
> - **nenhuma afirmação sobre volume, cobertura ou recência dos dados coletados pode ser feita por esta revisão**;
> - tudo que está marcado abaixo como verificado refere-se a **código, configuração e documentos versionados**, que são a mesma coisa localmente e em produção.
>
> Onde a verificação depende do estado da nuvem, o item está marcado **🔎 VERIFICAR NO BQ** com a consulta exata a rodar.

---

## 0. Resumo da rodada

A rodada de ajustes resolveu os pontos de **código** (que eram os mais graves) e três dos quatro erros factuais. O capítulo melhorou muito: a §3.6.3 (Sistema de Pontuação Hierárquica) é uma contribuição metodológica real e bem construída, e a reclassificação do Playwright como teste diagnóstico (§3.4, item 3) é mais honesta e, ao mesmo tempo, um argumento mais forte do que o anterior.

Restam três categorias de problema:

1. **Uma questão de versionamento entre código e dados** — não de execução. O código corrigido está no *working tree* e não commitado; é preciso garantir que a versão em produção é a corrigida e saber a partir de qual execução $t$ os dados passaram a refletir o novo desenho (§2).
2. **Correções parciais:** o Playwright saiu de §3.4 mas continua no diagrama de §3.3, na tabela de §3.3.2 e em §3.8; o escopo virou skincare no `urls.json` mas §3.8 ainda diz "Eletrônicos e Skincare".
3. **Itens não tocados:** §3.7 inteira, contradição das *BigQuery Views*, `is_crux_field_data`, critérios do *hero cluster*, e as seções ausentes (unidade de análise, $n$, limitações, ética, hipóteses).

| Status | Qtd. |
| :--- | :---: |
| ✅ Resolvido | 9 |
| 🟠 Resolvido parcialmente (gerou inconsistência nova) | 5 |
| 🔴 Novo problema introduzido pela edição | 6 |
| ⬜ Não endereçado | 12 |
| 🔎 Depende de verificação no BigQuery | 4 |

---

## 1. ✅ O que foi resolvido

| # | Item | Verificação |
| :-- | :--- | :--- |
| 1 | **`temperature=0.0` agora existe** | `extract_agent_responses.py:109-110` e `:130-131` — `GenerateContentConfig(temperature=0.0)` nas duas funções. A afirmação de §3.3.2 passou a ser verdadeira. |
| 2 | **`grounding_metadata` é capturado** | `:141-152` — extrai `grounding_chunks[].web.uri` para `grounding_uris`, com try/except. Esse era o item nº 1 da lista anterior. |
| 3 | **Escopo do `urls.json` limpo** | 10 SKUs, 100% skincare. Eletrônicos removidos. |
| 4 | **Categoria uniforme no código** | 22 queries, todas `category: "skincare"`. |
| 5 | **Tabela `robots.txt` corrigida** | Amazon agora marcada como bloqueando `Google-Extended` ✓ (bate com `robots_amazon.txt:83-84`); ML como `Disallow: /` ✓; Magalu como "sem restrição explícita" ✓; linha da Vivo (sem evidência) removida ✓. |
| 6 | **"Caso Cosmetis" removido** | A contradição com `zero-clic.md` deixou de existir. |
| 7 | **Playwright reposicionado** | §3.4 item 3 agora o descreve como *teste diagnóstico controlado*, com o argumento correto e mais forte: o bloqueio é política de WAF, não limitação da ferramenta. E há evidência (`evidencias/resultado_teste_meli.png`). |
| 8 | **dbt removido do repositório** | `thesis_dbt/` deletado — elimina a terceira arquitetura concorrente. |
| 9 | **§3.6.3 — operacionalização do $Y$** | Sistema de 5 tiers, com critério e fonte de dados por tier. Resolve conceitualmente o gap mais sério da versão anterior. |

---

## 2. 🔴 Versionamento: qual código está em produção e a partir de quando

*(Esta seção substitui a alegação de "dados não recoletados" da primeira versão desta revisão, que estava errada — foi inferida do espelho local, não do dataset em nuvem.)*

O problema real não é execução, é **rastreabilidade de versão**. O capítulo descreve um desenho experimental (temperatura zero, 4 configurações, 10 SKUs skincare, captura de `grounding_uris`); os dados no BigQuery foram gerados por *alguma* versão do código ao longo do tempo. Para o Capítulo 4 e para a banca, é preciso saber **exatamente qual execução $t$ marca a virada**.

### 2.1 O que está verificado no código versionado

| Fato | Fonte |
| :--- | :--- |
| Pipeline em produção = Cloud Function `run-pipeline`, gen2, `southamerica-east1`, `--source=.` | `cloudbuild.yaml` |
| Orquestrador GCP roda **4 estágios**: content, CrUX, PageSpeed, **agent responses** → depois carrega no BQ | `main.py:20-45` |
| Orquestrador local roda **3 estágios** — **sem agentes** | `scripts/run_pipeline.py:32-34` |
| Destino do JSON alterna local ↔ GCS pela env `GOOGLE_CLOUD_PROJECT` | `scripts/config.py:29-54` |
| As correções (T=0, `grounding_uris`, 10 SKUs, 22 queries) estão **não commitadas** no *working tree* | `git status` → ` M scripts/extract_agent_responses.py`; `git diff HEAD` = 250 inserções em 3 arquivos |

### 2.2 O ponto de atenção

`--source=.` faz upload do **diretório de trabalho** no momento do deploy. Então há dois cenários, e eles têm consequências diferentes:

- **Se o deploy foi manual** (`gcloud functions deploy` rodado da pasta): o código corrigido **está** em produção, mas **não existe commit que o identifique**. Não há como citar no capítulo "os dados a partir de $t$ foram gerados pela versão X" — e não há como reproduzir.
- **Se o deploy é por trigger de Cloud Build no push**: as correções **não chegaram** em produção, porque não foram commitadas.

Em ambos os casos a ação é a mesma e é barata: **commitar e tagear agora** (ex.: `v2-protocolo-skincare`), redeployar, e registrar no capítulo a data/hora da primeira execução com o protocolo novo.

### 2.3 🔎 Verificar no BigQuery (5 minutos, responde tudo)

```sql
-- 1) A partir de quando as 4 configurações estão rodando, e com qual modelo de fato
SELECT run_str, agent, model_used, fallback_used, COUNT(*) AS n
FROM `thesisusp.agent_responses`
GROUP BY 1,2,3,4
ORDER BY run_str DESC;

-- 2) Escopo por execução: quando os eletrônicos saíram da base
SELECT run_str, category, COUNT(DISTINCT product) AS produtos, COUNT(*) AS n
FROM `thesisusp.agent_responses`
GROUP BY 1,2 ORDER BY run_str DESC;

-- 3) Taxonomia de prompts por execução (3 tipos antigos vs. 6 novos)
SELECT run_str, query_type, COUNT(*) AS n
FROM `thesisusp.agent_responses`
GROUP BY 1,2 ORDER BY run_str DESC;

-- 4) O campo grounding_uris chegou a existir na tabela?
SELECT column_name, data_type
FROM `thesisusp.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'agent_responses';
```

A consulta (4) é a mais importante — ver §4.4: **`grounding_uris` não é gravado no BigQuery**, e esse é um defeito de código, independente de onde a pipeline roda.

### 2.4 Divergência entre os dois orquestradores (achado novo)

`main.py` (GCP) executa o estágio de agentes; `scripts/run_pipeline.py` (local) **não**. São dois protocolos de coleta diferentes convivendo no mesmo repositório, e o capítulo descreve apenas um.

Consequência prática: execuções locais produzem `content` + `crux` + `pagespeed` **sem** a resposta do agente correspondente. Se o painel casar $X$ e $Y$ pela chave `(run_str, sku, store)`, as execuções locais entram com $Y$ ausente — e "ausente" não é o mesmo que "não citada" (Tier 0). Se isso não for tratado, vira falso zero na variável dependente.

**Ação:** documentar em §3.3 que existem dois modos de execução, com estágios distintos; e, no tratamento do painel, **descartar explicitamente as execuções sem estágio de agente** em vez de deixá-las virarem Tier 0.

### 2.5 O que continua valendo independentemente da nuvem

- **`grounding_uris` capturado mas não persistido** (§4.4) — defeito de código, some no `load_to_bigquery`.
- **Sistema de 5 tiers não implementado** (§4.5) — nenhum script calcula tier ou score.
- **Sem esses dois, o Tier 4 é inatingível** por construção, mesmo com as configurações *grounded* rodando em produção há semanas.

---

## 3. 🔴 Problemas novos introduzidos pela edição

### 3.1 $Y_{\text{score}}$ (ordinal, 0–100) vs. $Y_i$ binário — §3.6.3 contradiz §3.7
A §3.6.3 define uma variável dependente **ordinal de 5 níveis** (0/25/50/75/100). A §3.7 permaneceu **intacta** e continua especificando $Y_i$ como "indicadora binária de citação" em uma **Regressão Logística Binomial**.

São modelos incompatíveis. É preciso escolher e escrever:
- **(a) Logística ordinal** (*proportional odds*) sobre os 5 tiers — usa toda a informação, mas exige testar a hipótese de chances proporcionais e o $n$ atual não ajuda;
- **(b) Logística binomial** com **regra de binarização declarada** (ex.: $Y=1$ se Tier ≥ 2), mantendo o $Y_{\text{score}}$ como análise descritiva do Deslocamento de Canal;
- **(c) Dois modelos irmãos**, um para $Y_1$ (chat) e outro para $Y_2$ (sidebar), que é o que a §3.6.2 promete.

**Recomendação:** (b). É a mais defensável com o $n$ disponível e preserva o valor narrativo do sistema de tiers.

### 3.2 Colisão de nomes: dois scores 0–100
$Y_{\text{score}}$ (§3.6.3) e ARS (§3.7.3) são ambos escalas 0–100, e um é a variável dependente enquanto o outro é a predição do modelo. Na leitura corrida — e na banca — isso se confunde de imediato. Renomear um dos dois (ex.: **Citation Tier Score (CTS)** para o dependente, reservando ARS para a predição).

### 3.3 Tabela §3.4 — "Mercado Livre / Bloqueio Google-Extended: **Sim (Via WAF)**"
A coluna é sobre **diretivas de `robots.txt`**. `Google-Extended` **não aparece** em `robots_mercadolivre2.txt` (grep = 0). WAF e `robots.txt` são mecanismos distintos: um é bloqueio de rede, o outro é declaração de política. Misturá-los na mesma célula enfraquece uma tabela que, no resto, agora está correta.

**Correção sugerida:** `Não (ausente do robots.txt)` na coluna Google-Extended, e registrar o bloqueio de rede na coluna de Inacessibilidade HTTP, que já existe.

### 3.4 §3.4 anuncia "quatro fatores" e lista três
A frase de abertura ("A análise de inacessibilidade revelou **quatro** fatores determinantes") ficou da versão anterior, mas os itens 3 e 4 foram fundidos em um só. Hoje há 3 itens. Erro de contagem visível.

### 3.5 Duas seções numeradas **3.6.4**
"Modelos Avaliados e Infraestrutura Vertex AI" e "Efeito da Memória Paramétrica vs. Google Search Grounding" têm o mesmo número. A segunda deve ser 3.6.5.

### 3.6 §3.6.2 agora faz uma afirmação empírica sem instrumento de coleta
O texto passou a descrever um achado específico e forte: o sidebar "**desloca a conversão**, omitindo a loja oficial D2C e exibindo botões de compra direcionados a marketplaces e farmácias concorrentes (ex.: Amazon, Beleza na Web, Farmácia Preço Popular, Droga Raia)".

Não existe no repositório nenhum coletor do Gemini Shopping / Merchant Center, e `evidencias/` não contém captura de tela do painel lateral. Como está, é uma afirmação de resultado sem fonte declarada — exatamente o tipo de frase que a banca pede para sustentar.

**Ação:** ou declarar explicitamente como **observação qualitativa exploratória**, com $n$, datas e prints arquivados em `evidencias/`, ou construir o instrumento. A segunda opção é cara; a primeira é honesta e suficiente, desde que o texto não a apresente como resultado sistemático.

---

## 4. 🟠 Correções parciais — inconsistências que sobraram

### 4.1 Playwright: corrigido em §3.4, ainda presente em três outros lugares
- §3.3, diagrama: `C[Stage 2: Playwright Headless Browser]` alimentando o armazenamento de extrações;
- §3.3.2, tabela de bibliotecas: `playwright` como "Simulação Headless de SPAs" na pilha da pipeline;
- §3.8, linha 2: "Requests, BeautifulSoup, **Playwright**, APIs CrUX e PageSpeed" como ferramenta de extração;
- §3.1, fase 3: "pipelines de extração (HTML estático **e headless browser com Playwright**)".

E `playwright` continua **fora do `requirements.txt`**. Como agora é um teste diagnóstico, o correto é: sair do diagrama e de §3.8, virar uma linha na §3.3.2 rotulada como *ferramenta de validação diagnóstica* (não de produção), e entrar em `requirements.txt` (ou num `requirements-dev.txt`) para que o teste seja reproduzível.

### 4.2 Escopo skincare: `urls.json` limpo, capítulo ainda inconsistente
- §3.8, linha 1, continua dizendo "Amostra de SKUs e lojas (**Eletrônicos** e Skincare D2C/Marketplace)";
- §3.2 abre justificando a exclusão dos eletrônicos, mas as execuções anteriores à limpeza do `urls.json` os contêm — 🔎 **VERIFICAR NO BQ** com a consulta (2) da §2.3 para saber a partir de qual `run_str` a base é 100% skincare.

Duas saídas coerentes: (i) usar apenas as execuções pós-corte e declarar os eletrônicos como **fase-piloto descartada** (uma frase em Limitações resolve, e o achado do *knowledge cutoff* do iPhone 17 Pro pode ser citado como evidência exploratória do piloto); ou (ii) manter os eletrônicos como grupo de contraste declarado. O que não funciona é o estado atual, em que o texto nega o que a base contém e não há corte temporal declarado.

**Em qualquer dos casos, o capítulo precisa dizer explicitamente qual janela de execuções compõe a amostra analisada** — é isso que resolve a inconsistência, não a limpeza do `urls.json` sozinha.

### 4.3 Taxonomia de prompts: §3.6.1 descreve 3 níveis, o código agora tem 6 tipos
O código passou a ter `product_exact` (10), `brand` (4), `level_1_control` (2), `level_2_channel` (2), `level_3_attributes` (2), `generic` (2). A §3.6.1 continua descrevendo apenas os três "Níveis".

Além disso, `generic` e `level_1_control` são semanticamente sobrepostos (ambos são consulta de categoria sem marca), o que vai gerar ambiguidade na hora de agrupar para análise.

**Ação:** ou consolidar o código em 3 tipos, ou documentar os 6 no capítulo com a definição de cada um e um apêndice com as 22 queries. E resolver a sobreposição `generic` × `level_1_control`.

### 4.4 `grounding_uris` é capturado mas não é persistido no BigQuery
`extract_agent_responses.py` grava `grounding_uris` no JSON local (`:200`, `:214`), mas o schema de `agent_responses` em `load_to_bigquery.py` **não tem esse campo** (grep `grounding` no arquivo = 0 ocorrências). Os campos são: `run_str, agent, model_used, fallback_used, query_type, product, category, query, response_text, response_length, latency_ms, error, timestamp`.

Ou seja: o dado mais valioso do novo desenho para o painel — o Tier 4 — **para no disco local e não chega ao warehouse**. Adicionar `SchemaField("grounding_uris", "STRING", mode="REPEATED")` e o mapeamento correspondente em `process_agent_responses`.

### 4.5 Sistema de 5 tiers: especificado no capítulo, não implementado
Não há lógica de tier/pontuação em nenhum script (`grep -i tier` em `scripts/` = 0). A citação continua sendo **casamento de string** por `STORE_ALIASES` (`load_to_bigquery.py:495`, loop em `:629`), gerando o campo booleano `cited` + `citation_sentiment`.

O schema de `agent_citations` também é binário: `run_str, sku, store_cited, agent, query_type, cited, citation_sentiment`. Para suportar §3.6.3 é preciso `citation_tier INTEGER` e `citation_score INTEGER`.

Além disso, o capítulo diz que Tier 1 e Tier 2 vêm de "Regex em `response_text`" — mas o código usa `in` sobre string em minúsculas, não regex, e **não distingue** "marca sozinha" de "produto + loja". A regra que separa Tier 1 de Tier 2 precisa ser escrita e implementada; hoje ela não existe.

---

## 5. ⬜ Itens da revisão anterior ainda não endereçados

### 5.1 Contradição das *BigQuery Views* — intocada
Continua em quatro pontos: parágrafo de abertura (linha 3, "tratamento via **Vistas SQL Nativas (BigQuery Views)**"), §3.1 fase 3 ("transformação de dados com Vistas SQL no BigQuery"), diagrama de §3.3 (`I[BigQuery SQL Views]`) e §3.3.2 ("execução de DDL/DML de Vistas SQL Nativas"). A §3.5 continua afirmando o contrário — e é ela que está correta. Correção puramente textual, 5 minutos.

### 5.2 `is_crux_field_data` — ainda descrito como implementado
Continua em §3.3.1 item 4 no presente do indicativo ("a pipeline aplica a regra de *fallback* automático"). Continua existindo apenas como item **não marcado** em `linear_backlog.md:72`. Não há lógica de fallback em `extract_crux.py` nem em `extract_pagespeed.py`.

### 5.3 Critérios do *Hero Product Cluster* — violações mantidas
§3.2 declara "estritamente padronizada: 30ml/30g, concentração 10–20%", e a própria lista contém:

| Item | Violação |
| :--- | :--- |
| Sallve — Antioxidante Hidratante **35g** | volume |
| Natura Chronos — **15ml** | volume |
| Neutrogena — **Hydro Boost Water Gel 50g** | não é sérum de vitamina C; volume |

Persiste também a divergência de nomenclatura: capítulo diz "ADCOS Vitamina C **15** Oil Control", `urls.json` e `extractions/` dizem `adcos-derma-complex-vitamina-c-**20**-30ml`; "Dermage Improve C 20 Biotic **30g**" vs. `dermage-improve-c-20-serum-antioxidante-**30ml**"; "Beyoung Sérum Vita C 18" vs. `beyoung-booster-antiaging-serum-30ml`.

Sugestão pragmática: trocar "estritamente padronizada" por "predominantemente padronizada (30ml/30g; exceções documentadas na Tabela X)" e justificar a Neutrogena como **controle negativo de categoria** — o que é defensável e até elegante, porque testa se o agente distingue ativo funcional.

### 5.4 §3.7 inteira — não sofreu nenhuma alteração
Continuam pendentes:
- **unidade de análise indefinida** ($X_{it}$ em §3.5 vs. $X_{ki}$ em §3.7; loja? loja×SKU? loja×SKU×execução? loja×query×modelo?);
- **nenhum $n$, período ou frequência de coleta** no capítulo (os dados existem em `docs/evaluation_timeline.md` e `zero-clic.md`);
- **EPV**: o `urls.json` atual tem 10 SKUs × 2–3 lojas = **26 pares loja×SKU**, com 16 lojas distintas, para 5 preditores. O problema de eventos por variável **piorou** com o corte dos eletrônicos e precisa ser enfrentado (reduzir preditores, penalização de Firth, ou reposicionar o ARS como índice descritivo);
- **pseudo-replicação do CrUX** (janela móvel de 28 dias × coleta 3×/dia);
- **multicolinearidade** TTFB × LCP e ausência de VIF/diagnósticos;
- **nenhuma métrica de validação** (pseudo-$R^2$, AUC, calibração, Hosmer-Lemeshow, holdout);
- **GEE aparece só na tabela de §3.8**, sem estrutura de correlação, cluster ou erros-padrão robustos declarados em §3.7;
- **missingness MNAR**: $X_1$ (Schema) só é observável quando $X_2 = 1$ (loja acessível);
- **ARS = $\hat{p} \times 100$**: falta admitir a tautologia e justificar o valor gerencial via decomposição da contribuição marginal de cada $X_k$.

### 5.5 Seções ausentes — nenhuma foi criada
Continuam faltando: **unidade de análise e composição amostral**, **dicionário de variáveis** (definição operacional + tabela/campo de origem + tratamento de nulos), **hipóteses formais $H_1..H_5$ com sinal esperado**, **limitações**, **ética/LGPD/termos de uso**, **estratégia de replicabilidade**.

O bloco de Limitações precisa conter, no mínimo: viés geográfico (`location="us-central1"`, `extract_agent_responses.py:103` e `:120`); fornecedor único (só Gemini) e a falha do Claude por saldo de créditos; não-reprodutibilidade de LLMs (versões mudam sem aviso; `seed` não é exposto pela API mesmo com $T=0$); fallback de modelo mascarando o rótulo (147 execuções de `gemini-2.5-pro` rotuladas assim mas executadas em `gemini-2.5-flash` — usar `model_used`, nunca `agent`); desalinhamento temporal CrUX × PageSpeed × resposta; e o **prompt de sistema em inglês pedindo resposta em português com a instrução "*be specific about prices if known*"**, que incentiva o modelo a preencher lacunas — ou seja, o desenho experimental induz parte da alucinação de preço que depois é reportada como achado.

### 5.6 Dicionário de canais — conflitos ainda presentes em `urls.json`
Mesmo após a limpeza, dois casos continuam com classificação contraditória para a **mesma loja**:

| Loja | Rótulos atribuídos | Ocorrências |
| :--- | :--- | :---: |
| **Mercado Livre** | `Marketplace` **e** `Especialista` | 4 |
| **Droga Raia** | `Especialista` **e** `Farma/especialista` | 3 |

Como $X_5$ (dummy D2C) é derivado desse campo, a variável continua contaminada. Os cinco rótulos atuais (`D2C marca`, `D2C DNVB`, `Marketplace`, `Especialista`, `Farma/especialista`) precisam virar um enum fechado e documentado, com a regra explícita de colapso para binário.

### 5.7 `llms.txt` — resultado ainda não reportado
`check_llms_txt` existe (`extract_content.py:74`) e roda a cada execução. O capítulo menciona a verificação em §3.3.1 e §3.8, mas nunca reporta o resultado. Se a resposta é "0 de 16 lojas publicam `llms.txt`", isso é um achado publicável e cabe numa linha da §3.4.

### 5.8 `requirements.txt` desatualizado em relação ao capítulo
§3.3.2 e §3.8 citam `numpy`, `statsmodels` e `playwright`. O arquivo contém apenas: `requests`, `beautifulsoup4`, `python-dotenv`, `google-cloud-secret-manager`, `google-cloud-storage`, `google-cloud-bigquery`, `pandas`, `db-dtypes`, `matplotlib`, `seaborn`, `anthropic`, `google-genai`. Para um trabalho que promete replicabilidade, o `requirements.txt` **é** o anexo metodológico.

---

## 6. Achado novo desta revisão: fonte de dados não documentada

`evidencias/` contém dados de **Google Trends e de pesquisa de palavras-chave** que não aparecem em lugar nenhum do Capítulo 3:

- `time_series_BR_20250719-1827_20260719-1827.csv` — série semanal de interesse de busca (jul/2025–jul/2026) para "protetor solar", "vitamina c", "skincare", "ácido hialurônico", "sérum facial", "sérum vitamina c";
- `todas_as_categorias-*.csv` + PNGs — volumes de busca e CPC por palavra-chave (`la roche posay vitamina c`, `smartphone`, `celular samsung`).

Isso é potencialmente valioso: é a evidência que justifica a **seleção do cluster de produtos** em §3.2 (hoje sustentada só por citação genérica a "ABIHPEC / Euromonitor", sem ano nem referência completa) e daria base empírica ao critério de escolha dos SKUs.

**Ação:** ou incorporar como fonte de dados secundária declarada em §3.2 — com data de extração, ferramenta e recorte geográfico — ou remover da pasta de evidências. Dados não documentados na pasta de evidências levantam a pergunta "o que mais foi usado e não foi contado?".

*(Nota: o arquivo `todas_as_categorias-celular_samsung-*.csv` é de eletrônicos — mais um resíduo do escopo antigo.)*

---

## 7. Plano de ação atualizado

**Bloco A — antes de escrever qualquer linha nova (destrava tudo o mais):**

| # | Ação | Esforço |
| :-- | :--- | :---: |
| A1 | Adicionar `grounding_uris` ao schema de `agent_responses` em `load_to_bigquery.py` | 15 min |
| A2 | Implementar `citation_tier` / `citation_score` (regra Tier 1 × Tier 2 escrita e codificada) | 2–3 h |
| A3 | **Commitar + tagear** o código corrigido e redeployar, garantindo que produção = versão citada no capítulo | 15 min |
| A4 | Rodar as 4 consultas da §2.3 e fixar a **janela de execuções** que compõe a amostra | 30 min |
| A5 | Tratar execuções locais (sem estágio de agente) para que não virem falso Tier 0 no painel | 1 h |

**Bloco B — correções textuais baratas (1 hora no total):**

| # | Ação |
| :-- | :--- |
| B1 | Remover "Vistas SQL / BigQuery Views" das linhas 3, 13, 69 e 96 |
| B2 | `is_crux_field_data` → tempo futuro, ou implementar |
| B3 | Playwright fora do diagrama §3.3, de §3.1 e de §3.8; manter só como validação diagnóstica |
| B4 | §3.4: "quatro fatores" → "três fatores" |
| B5 | Renumerar a segunda §3.6.4 → §3.6.5 |
| B6 | §3.4 tabela: ML / Google-Extended → "Não (ausente do robots.txt)" |
| B7 | §3.8 linha 1: remover "Eletrônicos" |
| B8 | Renomear $Y_{\text{score}}$ → CTS para não colidir com ARS |
| B9 | Atualizar `requirements.txt` (numpy, statsmodels, playwright) |
| B10 | Reportar o resultado do `llms.txt` em §3.4 |

**Bloco C — reescrita metodológica (o trabalho de fato):**

| # | Ação |
| :-- | :--- |
| C1 | Reconciliar §3.6.3 (ordinal) com §3.7 (binário) — recomendo binarizar em Tier ≥ 2 e declarar |
| C2 | Escrever §Unidade de Análise + tabela de composição amostral ($n$, período, frequência) |
| C3 | Escrever §Dicionário de Variáveis e §Hipóteses ($H_1..H_5$ com sinal esperado) |
| C4 | Escrever §Limitações e §Ética/LGPD/Termos de Uso |
| C5 | Unificar o enum de canais em `urls.json` (resolver ML e Droga Raia) e declarar a regra de $X_5$ |
| C6 | Reespecificar §3.7: GEE/cluster, EPV, VIF, AUC, calibração, tratamento do MNAR de $X_1$ |
| C7 | Declarar o escopo real do dataset (eletrônicos como piloto descartado ou contraste) |
| C8 | Documentar ou remover as fontes Google Trends de `evidencias/` |
| C9 | Rotular §3.6.2 (sidebar) como observação qualitativa, com prints arquivados |

---

## 8. Onde o capítulo está mais forte agora

- **§3.6.3 é a melhor seção do capítulo.** Um sistema de pontuação hierárquica que separa menção de marca, menção de loja, oferta transacional e URI efetivamente recuperada é uma operacionalização mais fina do que a literatura de *answer engines* costuma usar (Baeza-Yates et al. auditam o *output*; você mede o *input* e agora com granularidade). Vale defender como contribuição metodológica explícita — e vale dizer isso no texto, não deixar implícito.
- **A tese do Deslocamento de Canal (§3.6.2) é o achado mais original do trabalho.** "A loja oficial ganha a menção e perde a venda" é uma frase que a banca vai lembrar. Precisa só de evidência arquivada.
- **A §3.4 reescrita é mais rigorosa que a anterior**: separar "bloqueio declarado (robots.txt)" de "bloqueio imposto (WAF)" e provar o segundo com Playwright é um raciocínio metodológico limpo — corrigindo apenas a célula do Google-Extended.

---

## Anexo — Verificações desta revisão

| Verificação | Fonte |
| :--- | :--- |
| `temperature=0.0` implementado | `scripts/extract_agent_responses.py:109-110`, `:130-131` |
| `grounding_uris` capturado | `scripts/extract_agent_responses.py:141-152`, `:200`, `:214` |
| `grounding_uris` **não** persistido no BQ | grep `grounding` em `scripts/load_to_bigquery.py` = 0 |
| Tiers não implementados | grep `tier` em `scripts/` = 0; schema `agent_citations` = `cited BOOLEAN` |
| Citação ainda por string match | `load_to_bigquery.py:495` (`STORE_ALIASES`), `:627-637` (`text_lower`, `in`) |
| Pipeline roda no GCP (Cloud Function) | `cloudbuild.yaml`; `scripts/config.py:29-54` (`save_json` local ↔ GCS) |
| Dois orquestradores com estágios distintos | `main.py:20-45` (4 estágios, com agentes) vs. `scripts/run_pipeline.py:32-34` (3 estágios) |
| Correções ainda não commitadas | `git status` → ` M scripts/extract_agent_responses.py`; `git diff HEAD` = 250 inserções |
| Cobertura/recência dos dados | **não verificável nesta sessão** — sem acesso a GCS/BigQuery (ver §2.3) |
| `urls.json` = 10 SKUs skincare | leitura do arquivo; 16 lojas distintas; 26 pares loja×SKU |
| Conflitos de tipo de canal | ML → {`Marketplace`,`Especialista`}; Droga Raia → {`Especialista`,`Farma/especialista`} |
| 6 `query_type` no código | `extract_agent_responses.py` → `product_exact` 10, `brand` 4, `level_1_control` 2, `level_2_channel` 2, `level_3_attributes` 2, `generic` 2 |
| ML sem `Google-Extended` | grep em `evidencias/robots_mercadolivre2.txt` = 0 |
| Amazon bloqueia `Google-Extended` | `evidencias/robots_amazon.txt:83-84` |
| `is_crux_field_data` ainda ausente | grep no repo → só `linear_backlog.md:72` (não marcado) e o capítulo |
| Playwright fora do `requirements.txt` | `requirements.txt` (12 pacotes, sem playwright/numpy/statsmodels) |
| dbt removido | `git status` → `D thesis_dbt/*` |
| Google Trends não documentado | `evidencias/time_series_BR_*.csv`, `todas_as_categorias-*.csv` |
| Notebook EDA sem modelagem | `notebooks/eda.ipynb` → 3 seções (Content, CrUX, PageSpeed); sem `statsmodels`/`logit`/`ARS` |
