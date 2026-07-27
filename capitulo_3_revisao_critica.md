# Revisão Crítica — `capitulo_3_metodologia.md`

**Revisão 6 — encerramento · 27/07/2026** · substitui as revisões anteriores
**Base:** capítulo em 341 linhas (17:57) · `scripts/` · `urls.json` (17:50) · git `eb907b1`, tag `v2-protocolo-skincare`

> **Escopo.** Pipeline em produção no GCP; esta sessão não acessa GCS nem BigQuery. Verificações sobre código, evidências versionadas e texto.

---

## 0. Veredito

**O capítulo está pronto.** O dicionário de citações foi corrigido, os conflitos de canal desapareceram, o algoritmo do CTS está documentado passo a passo, e a §3.9 (limitações, ética e replicabilidade) — que era a maior lacuna estrutural — existe.

Sobrou uma ironia útil: **as três últimas afirmações sem lastro no código estão justamente dentro da §3.9**, a seção que uma banca lê com mais atenção porque é onde se declara rigor. Nenhuma delas é difícil — duas são reescrita de frase, uma é `time.sleep()`.

### ✅ Fechado nesta rodada

| Item | Verificação |
| :--- | :--- |
| **Dicionário de citações sincronizado** | **As 16 lojas monitoradas têm alias** — nenhuma marca D2C fica estruturalmente impedida de ser citada. Lojas de eletrônicos removidas. |
| **Universo "só citadas" bem definido** | Restam 5 aliases sem monitoramento (`Drogasil`, `Panvel`, `Pague Menos`, `Drogaria Pacheco`, `Magazine Luiza`) — farmácias que o agente cita mas sem $X$ medido. Correto **desde que** o capítulo declare que elas ficam fora do painel de modelagem e entram só na descritiva. |
| **Conflitos de canal resolvidos** | `urls.json` — nenhuma loja com dois rótulos. Mercado Livre e Droga Raia unificados. |
| **Algoritmo do CTS documentado** | §3.6.3, 5 etapas + fluxograma, com janela de ±250 chars, tokens de produto e de compra explicitados. Um terceiro pode replicar. |
| **§3.8 corrigida** | Playwright agora aparece como "Playwright Diagnóstico" em Inacessibilidade, e a amostra é "Skincare D2C, Varejo Farmacêutico e Marketplaces". |
| **§3.9 criada** | Limitações de escopo, LGPD, *rate limiting*, diretivas de rastreamento e replicabilidade. |
| **Tag publicada** | `v2-protocolo-skincare` existe; repositório público em `github.com/britneyscripts/thesis-pipeline`. |
| **`.env` fora do versionamento** | Listado no `.gitignore` — importante, já que o repositório é público. |

---

## 1. 🔴 Três afirmações da §3.9 que o código não sustenta

### 1.1 "*Rate limiting*" — não existe no código (§3.9.2, item 2)
O texto afirma: *"Os scripts de extração em Python aplicam intervalos de latência (**backoff / sleep**) entre requisições para evitar sobrecarga de servidores"*.

**Verificação:** `grep "sleep|backoff"` em `extract_content.py`, `extract_crux.py`, `extract_pagespeed.py` e `extract_agent_responses.py` → **zero ocorrências**.

Esta é a única afirmação **ética** não sustentada do capítulo, e por isso a mais sensível: uma declaração de conduta responsável que o código não cumpre é pior do que não declarar nada.

**Correção (5 minutos):** adicionar `time.sleep(1)` no laço de requisições de `extract_content.py` e nos consumidores das APIs CrUX/PageSpeed. Aí a frase passa a ser verdadeira — e o custo é irrelevante para 26 pares loja×SKU, 3× ao dia.

### 1.2 O *fallback* CrUX → PageSpeed continua não implementado — agora afirmado em **três** lugares
- §3.3.1, item 4: *"a pipeline aplica a regra de fallback automático"*
- §3.7.2, $X_{3it}$: *"com fallback de laboratório PageSpeed quando o CrUX for nulo"*
- §3.9.1, item 4: *"a pipeline aplica a regra de fallback automático… sinalizadas pela flag binária `is_crux_field_data = 1|0`"*

**Verificação:** `grep is_crux_field_data` em `scripts/` → **zero**. Não há lógica de fallback em `extract_crux.py`. A flag só existe como item **não marcado** em `linear_backlog.md:72`.

É a divergência texto × código mais repetida do capítulo. Duas saídas: implementar (algumas horas — e então a flag precisa entrar como controle no modelo, porque dado de campo e dado de laboratório não são a mesma variável), ou passar as três menções para tempo futuro / "previsto para a fase de tratamento".

### 1.3 "Sementes determinísticas de aleatoriedade" (§3.9.3)
O texto diz: *"As **sementes determinísticas de aleatoriedade** e os hiperparâmetros de decodificação foram fixados em `temperature = 0.0`"*.

Não há `seed` em lugar nenhum do código (`grep seed` = 0), e temperatura não é semente. A API do Vertex AI não expõe semente para esses modelos, então a réplica bit-a-bit não é garantida mesmo com $T=0$.

**Correção honesta e mais forte:** *"A decodificação foi fixada em modo determinístico (`temperature = 0.0`, amostragem gananciosa) com instrução de sistema neutra declarada. A API do Vertex AI não expõe parâmetro de semente (`seed`) para os modelos Gemini 2.5, de modo que réplicas exatas não são garantidas; a variação residual entre execuções é tratada como fonte de variância no desenho longitudinal."*

Isso antecipa a pergunta em vez de dar munição para ela.

---

## 2. 🟢 Um ponto da §3.9.2 que você pode deixar **mais forte** (e verificável)

O item 3 diz apenas *"sem violar firewalls de segurança"*. Você pode afirmar algo muito mais preciso, e checável nos próprios arquivos de `evidencias/`:

- **Amazon Brasil** (`robots_amazon.txt`): sob `User-agent: *` há `Allow: /*/dp/` — as PDPs monitoradas estão **explicitamente liberadas** para rastreadores genéricos. O bloqueio `Disallow: /` atinge apenas os *user-agents* nomeados de IA (`GPTBot`, `ClaudeBot`, `Google-Extended` etc.), que o coletor da pesquisa não usa.
- **Mercado Livre** (`robots_mercadolivre2.txt`): o bloco `User-agent: *` restringe rotas administrativas (`/gz/cart/`, `/gz/merch/`, `/HOME/`) — **não** as rotas de produto.

Ou seja: a coleta **cumpre as diretivas aplicáveis ao seu próprio agente**, e isso é demonstrável linha a linha. Substituir a frase genérica por essa constatação transforma um ponto potencialmente frágil em evidência a favor.

---

## 3. ⬜ Limpezas textuais que sobraram (~40 min)

| # | Item | Linha |
| :-- | :--- | :--- |
| 1 | "Vistas SQL Nativas / BigQuery Views" — contradiz a §3.5, que está correta | 3, 13, 71, 98 |
| 2 | Playwright ainda como estágio de pipeline (a §3.4 e a §3.8 já o tratam como diagnóstico) | 13, 65 |
| 3 | §3.6.2 promete capturas do sidebar em `evidencias/` — a pasta segue com 12 arquivos de 19/07, nenhum do painel lateral | 174, 189 |
| 4 | §3.6.1 descreve 3 níveis; o código tem 6 `query_type`, com `generic` e `level_1_control` sobrepostos | §3.6.1 |
| 5 | Hero cluster: Sallve 35g, Natura 15ml, Neutrogena Hydro Boost 50g violam "estritamente padronizado"; nomes divergem de `urls.json` (ADCOS C15 × C20; Dermage 30g × 30ml) | §3.2 |
| 6 | `llms.txt` coletado a cada execução, resultado nunca reportado | §3.4 |
| 7 | `citation_sentiment` calculado e gravado, nunca definido no capítulo | §3.6.3 |
| 8 | Declarar os **dois universos**: 16 lojas monitoradas (painel) × lojas só citadas (descritiva) | §3.2 ou §3.6.3 |
| 9 | Google Trends em `evidencias/` — base empírica de §3.2, hoje sustentada por "ABIHPEC / Euromonitor" sem ano nem referência | §3.2 |

**Ainda por escrever** (texto novo, não correção): **unidade de análise e composição amostral** — o que é uma observação, $n$ por nível, janela de execuções. Você tem os números: 10 SKUs, 16 lojas, 26 pares loja×SKU, 22 queries × 4 configurações por execução $t$. Some-se a isso a decisão de recorte entre os dois regimes de prompt (persona antiga × instrução neutra), que não são comparáveis.

E, na modelagem: **validação** (pseudo-$R^2$, AUC, calibração, VIF entre TTFB e LCP) e **hipóteses formais** $H_1..H_5$ com sinal esperado.

---

## 4. Fechamento

Este capítulo começou com sete divergências entre o que afirmava e o que o código fazia. Hoje sobram três, todas concentradas na §3.9 e todas de reescrita ou de cinco linhas de código. O núcleo metodológico — variável dependente, protocolo experimental, hiperparâmetros, modelo estatístico e dicionário de citações — está íntegro e auditável.

O que sustenta a defesa:

- **O CTS é a contribuição metodológica do trabalho**, e agora é uma medida que discrimina (Tier 0 69,0% · Tier 1 19,4% · Tier 2 11,6%; das 286 menções, 63% Tier 1 e 37% Tier 2) e que um terceiro consegue replicar a partir da §3.6.3. Baeza-Yates et al. auditam o **output** do agente; você mede o **input** — a prontidão da PDP. Vale um parágrafo explícito de posicionamento.
- **A §3.4 é o padrão de rigor do capítulo**: separa bloqueio declarado (`robots.txt`) de bloqueio imposto (WAF), prova o segundo com teste controlado e arquiva a evidência.
- **A §3.6.4** (instrução neutra + hiperparâmetros justificados) é o nível de detalhe que se pede para aceitar reprodutibilidade em experimento com LLM.
- **A §3.9** fecha o flanco que mais derruba trabalho aplicado em banca: escopo, ética e replicabilidade declarados de forma explícita.

Boa defesa.

---

## Anexo — Verificações desta revisão

| Verificação | Fonte |
| :--- | :--- |
| 16/16 lojas monitoradas com alias | cruzamento `STORE_ALIASES` × `urls.json` |
| 5 aliases sem monitoramento (farmácias + Magalu) | mesmo cruzamento |
| Sem conflitos de tipo de canal | `urls.json` — cada loja com rótulo único |
| Sem `sleep`/`backoff` nos extratores | grep nos 4 scripts de extração = 0 |
| `is_crux_field_data` não implementado | grep em `scripts/` = 0; só `linear_backlog.md:72` (não marcado) |
| Sem `seed` no código | grep `seed` em `scripts/*.py` = 0 |
| Tag e repositório públicos | `git tag` → `v2-protocolo-skincare`; remote `github.com/britneyscripts/thesis-pipeline` |
| `.env` não versionado | `.gitignore`; `git ls-files` não retorna `.env` |
| Amazon libera `/dp/` para UA genérico | `evidencias/robots_amazon.txt`, bloco `User-agent: *` |
| ML bloqueia só rotas administrativas sob `*` | `evidencias/robots_mercadolivre2.txt:63+` |
| Views / Playwright remanescentes | capítulo, linhas 3, 13, 71, 98 / 13, 65 |
| Sem capturas do sidebar | `evidencias/` — 12 arquivos, todos de 19/07 |
| Cobertura e recência dos dados | **não verificável nesta sessão** |
