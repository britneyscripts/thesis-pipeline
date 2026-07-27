# 📋 Linear Project Backlog: MBA Thesis — Agentic E-Commerce & ARS Pipeline

> **Repository**: `thesisUSP/thesis-pipeline`  
> **Domain**: Skincare D2C vs. Retail in Brazil (Hero Product Cluster: Vitamin C / Antioxidant Serums 30ml/30g)  
> **Methodology Framework**: CRISP-DM + GEE Multivariate Panel Logistic Regression  

---

## 🏗️ System & Pipeline Architecture Overview

```mermaid
flowchart TD
    subgraph 1. Data Ingestion & Extraction Layer (Python)
        A[urls.json / SKU Registry] --> B[Stage 1: Content & Schema.org Parser]
        A --> C[Stage 2: Playwright Headless Browser for SPAs]
        A --> D[Stage 3: Google PageSpeed Insights API]
        A --> E[Stage 4: Chrome UX Report - CrUX API]
    end

    subgraph 2. GCP Cloud & Data Warehousing (GCP)
        B & C & D & E --> F[Google Cloud Storage - GCS]
        F --> G[Google BigQuery - thesisusp Raw Tables]
        G --> H[Python Data Processing & pandas DataFrames]
    end

    subgraph 3. Experimental LLM Evaluation & Grounding
        I[extract_agent_responses.py] --> J[Vertex AI SDK: Gemini 2.5 Flash & Pro]
        J --> K1["Chat Discovery Surface (Y1): Open-Web RAG"]
        J --> K2["Shopping Sidebar Surface (Y2): Merchant Center API"]
    end

    subgraph 4. Econometric & Statistical Modeling (Python)
        H & K1 & K2 --> L[GEE Multivariate Panel Logistic Regression]
        L --> M[Agent Readiness Score - ARS Index 0-100]
```

---

## 🎯 Epics and Task Breakdown

---

### 📌 EPIC 1: Technical System Architecture (`ARCH`)

#### `[ARCH-01]` Document End-to-End Data Pipeline Infrastructure & Tech Stack
* **Type**: Task | **Priority**: High  
* **Description**: Document the technical data engineering architecture: 4-stage Python extraction pipeline, Python package selections with technical rationales, GCP infrastructure, and BigQuery dataset storage.
* **Subtasks**:
  - [x] Document 4-stage Python extraction pipeline (Content, Playwright SPA, PageSpeed, CrUX).
  - [x] Document Python package stack choices & technical rationales (`requests`, `beautifulsoup4`, `playwright`, `google-cloud-bigquery`, `pandas`, `statsmodels`, `scikit-learn`).
  - [x] Document BigQuery (`thesisusp`) raw storage and Python-first DataFrame processing architecture.
* **Deliverable**: Section 3.3 and 3.5 in `capitulo_3_metodologia.md`.

---

### 📌 EPIC 2: Exploratory Data Analysis (`EDA`) — Panel Data Focus

#### `[EDA-01]` Central Tendency & Dispersion Analysis Across Execution Runs $t$
* **Type**: Task | **Priority**: High  
* **Description**: Compute comprehensive statistical metrics across execution runs $t$ on BigQuery dataset `thesisusp` to establish baseline distributions for technical predictors and outcome metrics.
* **Subtasks**:
  - [ ] Extract panel dataset linking `content_extractions`, `pagespeed_extractions`, `crux_extractions`, and `agent_responses`.
  - [ ] Compute summary metrics (**Mean, Median, Standard Deviation, Interquartile Range Q3-Q1, Min, Max, and Skewness**) for `mobile_ttfb`, `mobile_lcp`, `mobile_cls`, `mobile_score`, `schema_completeness`, and `citation_score`.
  - [ ] Calculate the **Zero-Citation Inflation Rate** (% of runs $t$ resulting in Tier 0 zero citations).
  - [ ] Generate comparative boxplot visualizations comparing Shopify DNVBs vs. General Retail Channels.
* **Deliverable**: `extractions/eda_descriptive_stats.csv` & `extractions/eda_channel_comparison_boxplots.png`.

#### `[EDA-02]` Data Imputation & Fallback Hierarchy (CrUX Field vs. PageSpeed Lab)
* **Type**: Task | **Priority**: High  
* **Description**: Establish data quality metrics and document the lab baseline fallback hierarchy when CrUX field data is missing due to low traffic volume.
* **Subtasks**:
  - [ ] Calculate CrUX field data coverage rate (% of target store PDPs with valid $p75$ field metrics).
  - [ ] Evaluate correlation ($r$) between CrUX field TTFB/LCP and PageSpeed synthetic lab metrics across high-traffic retail stores.
  - [ ] Document PageSpeed lab metrics as the controlled synthetic baseline for lower-traffic D2C PDPs.
* **Deliverable**: `extractions/eda_crux_coverage_report.csv` & Data Quality Imputation Matrix.

#### `[EDA-03]` Security Walls & Bot Accessibility Matrix (WAF & Crawler Policies)
* **Type**: Task | **Priority**: Medium  
* **Description**: Map edge security blocking patterns (Cloudflare / Akamai 403 Forbidden) and AI crawler `robots.txt` disallow policies across all 16 monitored e-commerce stores.
* **Subtasks**:
  - [ ] Aggregate HTTP response code distributions (200 OK, 403 Forbidden, 429 Rate Limited, 503 Service Unavailable) across extraction runs.
  - [ ] Parse `robots.txt` disallow rules for major AI crawler User-Agents (`Google-Extended`, `GPTBot`, `ClaudeBot`, `CCBot`).
  - [ ] Construct the binary predictor $X_{2it}$ ($1 =$ Unblocked / 200 OK; $0 =$ WAF 403 Forbidden).
* **Deliverable**: Security & Bot Accessibility Contingency Matrix in Chapter 4.

#### `[EDA-04]` Schema.org JSON-LD Structured Data Completeness Index ($X_{1it}$)
* **Type**: Task | **Priority**: High  
* **Description**: Perform deep structural audit of JSON-LD microdata across all target PDPs to compute the Schema Completeness Score ($X_{1it}$).
* **Subtasks**:
  - [ ] Parse `@context` and `@type` declarations (`Product`, `Offer`, `Brand`, `AggregateRating`) from raw HTML `<script type="application/ld+json">` tags.
  - [ ] Evaluate presence of 11 mandatory e-commerce JSON-LD properties: `name`, `image`, `description`, `sku`, `gtin` / `gtin13`, `brand`, `offers`, `price`, `priceCurrency`, `availability`, and `seller`.
  - [ ] Calculate continuous score $X_{1it} = \frac{\text{Count(Fields Present)}}{11} \in [0.0, 1.0]$.
  - [ ] Rank all 16 monitored store PDPs by Schema Completeness Index ($X_1$) and cross-tabulate against D2C vs. Retail channel type ($X_5$).
  - [ ] Export structured data completeness breakdown table for Chapter 4 results.
* **Deliverable**: `extractions/eda_schema_completeness_ranking.csv` & Schema Quality Distribution Chart.

---

### 📌 EPIC 3: Prompt Engineering & LLM Experiments (`LLM`)

#### `[LLM-01]` Refine Prompt Registry to Lean Skincare Suite
* **Type**: Task | **Priority**: High  
* **Description**: Purge legacy electronics queries and install the 6 authentic, price-and-channel-focused Brazilian Skincare prompts in `extract_agent_responses.py`.
* **Subtasks**:
  - [x] Delete `electronics` category queries from `QUERIES` list in Python script.
  - [x] Add 6 non-induced Brazilian Skincare prompts across Level 1 (Problem-Centric), Level 2 (Channel Comparison), and Level 3 (Attributes).
  - [x] Validate Python dictionary structure and execution compatibility.
* **Deliverable**: Updated `extract_agent_responses.py` (6 lean queries protecting GCP billing).

#### `[LLM-02]` Document Level 1 Prompt as Baseline Control Group
* **Type**: Task | **Priority**: Medium  
* **Description**: Formally designate Level 1 (Zero-Knowledge, Zero-Brand) as the experimental control group, eliminating the need for artificial counterpoint queries.
* **Subtasks**:
  - [x] Document Level 1 as the Un-primed Control in `capitulo_3_metodologia.md`.
  - [x] Establish the citation delta between Level 1 and Level 3 as the measure of LLM retrieval sensitivity.
* **Deliverable**: Experimental Design subsection in Chapter 3.

#### `[LLM-03]` Execute Vertex AI Gemini Experiments
* **Type**: Task | **Priority**: High  
* **Description**: Trigger automated agent experiment calls via Vertex AI SDK for 4 standardized Gemini configurations: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-grounded`, and `gemini-2.5-pro-grounded`.
* **Subtasks**:
  - [ ] Run `python3 scripts/extract_agent_responses.py`.
  - [ ] Verify response ingestion into BigQuery tables `thesisusp.agent_responses` and `thesisusp.agent_citations`.
* **Deliverable**: LLM experimental dataset loaded into BigQuery.

---

### 📌 EPIC 4: Python Data Wrangling & Econometric Modeling (`MODEL`)

#### `[PY-01]` Python Data Processing & 5-Tier Citation Scoring (CTS Algorithm)
* **Type**: Task | **Priority**: High  
* **Description**: Process raw BigQuery tables using `pandas` and `google-cloud-bigquery` Python client to compute store performance metrics, parse Schema completeness, and map LLM citations into the **Citation Tier Score (CTS: 0–100 pts)** via `STORE_ALIASES` dictionary lookup and $\pm 250$ character windowed context parsing.
* **Subtasks**:
  - [x] Update `load_to_bigquery.py` schema to include `grounding_uris` (`REPEATED STRING`), `citation_tier` (`INTEGER`), and `citation_score` (`INTEGER`).
  - [x] Implement 5-Tier CTS calculation logic with $\pm 250$ char context window and domain-level URI matching.
  - [x] Index 100% of Skincare D2C brand aliases (`Sallve`, `Creamy Skincare`, `Principia`, `Beyoung`, `ADCOS`, `Dermage`, `O Boticário`, `Natura`, `La Roche-Posay`, `Neutrogena`) in `STORE_ALIASES`.
  - [x] Document 5-step citation parsing algorithm and dictionary mapping protocol in Section 3.6.3 of `capitulo_3_metodologia.md`.
* **Deliverable**: Automated CTS calculation module in `scripts/load_to_bigquery.py` & Chapter 3 documentation.

#### `[MODEL-01]` Fit Multivariate Panel GEE Logistic Regression & Compute ARS Score
* **Type**: Task | **Priority**: High  
* **Description**: Model citation probability using Generalized Estimating Equations (GEE) with AR(1) working correlation structure in `statsmodels` to handle longitudinal panel correlation across runs $t$.
* **Subtasks**:
  - [ ] Apply Binarization Rule: $Y_{it} = 1 \iff \text{CTS}_{it} \ge 50$ (Tier 2, 3, or 4); $Y_{it} = 0 \iff \text{CTS}_{it} < 50$ (Tier 0 or 1).
  - [ ] Fit GEE Logistic Regression with AR(1) working correlation structure grouped by store $i$ in Python (`statsmodels`).
  - [ ] Extract estimated coefficients ($\beta$), standard errors, Odds Ratios ($\exp(\beta)$), and $p$-values for the 5 predictors ($X_{1it} \dots X_{5it}$).
  - [ ] Compute the **Agent Readiness Score (ARS: 0–100)** for all 10 target stores:
    $$\text{ARS}_{it} = \frac{1}{1 + e^{-(\hat{\beta}_0 + \sum_{k=1}^5 \hat{\beta}_k X_{kit})}} \times 100$$
* **Deliverable**: Econometric GEE model output table & ARS store benchmark ranking in Chapter 4.

---

### 📌 EPIC 5: Theoretical Discovery & Dissertation Writing (`DOC`)

#### `[THEORY-01]` Document Empirical Finding: Disaggregated Agentic Funnel
* **Type**: Task | **Priority**: High  
* **Description**: Formally detail the theoretical discovery of how Generative AI interface architecture splits the shopping funnel into two distinct response surfaces: **Conversational Chat Discovery** (Open-Web RAG) vs. **Shopping Sidebar Transaction** (GMC API).
* **Subtasks**:
  - [x] Document Chat Window vs. Sidebar Disaggregation in Section 3.6.2 of `capitulo_3_metodologia.md`.
  - [x] Add Methodological Scope Caveat on Structural Visibility Friction vs. Unobserved Click Traffic in Section 3.6.2.
  - [ ] Connect empirical findings to Accornero's (2026) Shopper Schism framework in Chapter 4 / Results.
* **Deliverable**: Theoretical Model Section in Dissertation.

#### `[DOC-01]` Finalize Chapter 3 Methodology Manuscript
* **Type**: Task | **Priority**: High  
* **Description**: Consolidate all architectural diagrams, prompt taxonomies, GEE model specifications, limitations, and ethical guidelines into `capitulo_3_metodologia.md`.
* **Subtasks**:
  - [x] Incorporate Skincare D2C single-cluster rationale and Sample Delimitation Note (Section 3.2).
  - [x] Incorporate Disaggregated Agentic Funnel diagram and CTS 5-Tier Hierarchy (Section 3.6.2 & 3.6.3).
  - [x] Document 5-step citation parsing algorithm and dictionary mapping protocol (`STORE_ALIASES`) (Section 3.6.3).
  - [x] Document neutral `system_instruction` and Vertex AI hyperparameters (Section 3.6.4).
  - [x] Document 5-variable GEE model specification and ARS formula (Section 3.7).
  - [x] Document Methodological Limitations, LGPD Ethical Safeguards, and Replicability Guidelines (Section 3.9).
  - [x] Tag and push git release **`v2-protocolo-skincare`** to GitHub.
* **Deliverable**: Complete Chapter 3 manuscript formatted for ABNT / USP ICMC standards. (COMPLETED 100%)
