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

#### `[EDA-01]` Basic Descriptive Statistics & Distribution Analysis
* **Type**: Task | **Priority**: High  
* **Description**: Run Python scripts on BigQuery `thesisusp` to compute central tendency and dispersion metrics across execution runs $t$.
* **Subtasks**:
  - [ ] Compute **Mean, Median, Standard Deviation, IQR (Q3-Q1), Min, Max, and Skewness** for `TTFB`, `LCP`, `CLS`, `PageSpeed Score`, and `Schema Completeness`.
  - [ ] Generate boxplots comparing Shopify DNVBs vs. General Retail Channels.
  - [ ] Calculate Zero-Citation Inflation rate (% of runs with 0 citations).
* **Deliverable**: `extractions/eda_descriptive_stats.csv` & boxplot figures.

#### `[EDA-02]` Data Imputation & Fallback Hierarchy (CrUX Field vs. PageSpeed Lab)
* **Type**: Task | **Priority**: High  
* **Description**: Implement data imputation hierarchy using PageSpeed Insights lab metrics as a fallback when CrUX field data is missing due to low traffic.
* **Subtasks**:
  - [ ] Map CrUX data coverage (% of pages with valid p75 field data).
  - [ ] Implement Fallback Imputation Rule: Use PageSpeed Lab TTFB/LCP when CrUX field data is NULL, adding binary flag `is_crux_field_data = 1|0`.
* **Deliverable**: Data Imputation Summary Table & Fallback Coverage Report.

#### `[EDA-03]` Security Walls & Bot Accessibility Matrix
* **Type**: Task | **Priority**: Medium  
* **Description**: Map WAF blocking patterns and `robots.txt` AI crawler disallow directives.
* **Subtasks**:
  - [ ] Aggregate HTTP status response rates (200 OK, 403 Forbidden, 429 Rate Limited) across store extractions.
  - [ ] Parse `robots.txt` for AI crawler disallow rules (`GPTBot`, `Google-Extended`, `ClaudeBot`, `CCBot`).
* **Deliverable**: Security & Bot Accessibility Contingency Table.

#### `[EDA-04]` Schema.org JSON-LD Completeness Index
* **Type**: Task | **Priority**: High  
* **Description**: Measure data completeness of structured markup across all 10 target D2C/Retail SKUs.
* **Subtasks**:
  - [ ] Calculate % presence of 11 mandatory e-commerce JSON-LD fields (`name`, `price`, `priceCurrency`, `availability`, `brand`, `gtin`, etc.).
  - [ ] Rank stores by Schema Completeness Index.
* **Deliverable**: Schema Completeness Ranking Table.

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

#### `[PY-01]` Python Data Processing & 5-Tier Citation Scoring (pandas)
* **Type**: Task | **Priority**: High  
* **Description**: Process raw BigQuery tables using `pandas` and `google-cloud-bigquery` Python client to compute store performance metrics, parse Schema completeness, and map LLM citations into the **5-Tier Hierarchical Citation Score ($Y_{\text{score}}$: 0–100 pts)**.
* **Subtasks**:
  - [ ] Execute Python data wrangling script to compute $Y_{\text{score}}$ (Tier 4: 100pts PDP URI, Tier 3: 75pts Sidebar Offer, Tier 2: 50pts Product+Store Chat Mention, Tier 1: 25pts Brand Mention, Tier 0: 0pts Omission).
  - [ ] Merge technical predictor metrics ($X_{it}$) and outcome scores ($Y_{it}$) into a consolidated longitudinal panel `pandas.DataFrame`.
* **Deliverable**: Consolidated panel DataFrame with $Y_{\text{score}}$ ready for GEE modeling.

#### `[MODEL-01]` Fit Multivariate Panel GEE Logistic Regression & Compute ARS Score
* **Type**: Task | **Priority**: High  
* **Description**: Model citation probability using Generalized Estimating Equations (GEE) to handle longitudinal panel correlation across runs $t$.
* **Subtasks**:
  - [ ] Fit GEE Logistic Regression with AR(1) working correlation structure in Python (`statsmodels`).
  - [ ] Extract estimated coefficients ($\beta$), standard errors, Odds Ratios ($\exp(\beta)$), and $p$-values.
  - [ ] Compute the **Agent Readiness Score (ARS: 0–100)** for all 10 target stores:
    $$\text{ARS}_i = \frac{1}{1 + e^{-\hat{z}_i}} \times 100$$
* **Deliverable**: Econometric GEE model output table & ARS store benchmark ranking.

---

### 📌 EPIC 5: Theoretical Discovery & Dissertation Writing (`DOC`)

#### `[THEORY-01]` Document Empirical Finding: Disaggregated Agentic Funnel
* **Type**: Task | **Priority**: High  
* **Description**: Formally detail the theoretical discovery of how Generative AI interface architecture splits the shopping funnel into two distinct response surfaces: **Conversational Chat Discovery** (Open-Web RAG) vs. **Shopping Sidebar Transaction** (GMC API).
* **Subtasks**:
  - [x] Document Chat Window vs. Sidebar Disaggregation in Section 3.6.2 of `capitulo_3_metodologia.md`.
  - [ ] Connect empirical findings to Accornero's (2026) Shopper Schism framework in Chapter 4 / Results.
* **Deliverable**: Theoretical Model Section in Dissertation.

#### `[DOC-01]` Finalize Chapter 3 Methodology Manuscript
* **Type**: Task | **Priority**: High  
* **Description**: Consolidate all architectural diagrams, prompt taxonomies, GEE model specifications, and EDA results into `capitulo_3_metodologia.md`.
* **Subtasks**:
  - [x] Incorporate Skincare D2C single-cluster rationale (Section 3.2).
  - [x] Incorporate Disaggregated Agentic Funnel diagram (Section 3.6.2).
  - [ ] Insert EDA summary tables and GEE regression results.
* **Deliverable**: Complete Chapter 3 manuscript formatted for ABNT / USP ICMC standards.
