# Linha do Tempo de Avaliação de Dados — Abordagem CRISP-DM Detalhada

Este documento expande o cronograma de avaliação de dados da sua tese utilizando a metodologia **CRISP-DM** (*Cross-Industry Standard Process for Data Mining*). Cada fase foi desmembrada em sub-tarefas específicas para evitar a subestimativa de tempo e garantir o rigor científico exigido pela USP.

---

## 1. Resumo da Coleta (O que já está no Google Cloud)
* **Período de coleta**: 04/06/2026 a 23/06/2026 (60 execuções completas)
* **Escopo**: 7 SKUs monitorados em 15 lojas e-commerce diferentes.
* **Volume total**:
  - `content`: 1.568 registros (dados estruturados, títulos, descrições)
  - `crux`: 1.568 registros (métricas de usuários reais Chrome UX)
  - `pagespeed`: 1.568 registros (pontuações de laboratório e auditoria)
  - `agent_responses`: 84 registros (respostas das IAs para as 21 consultas de compras)

---

## 2. Cronograma Geral Ampliado (Datas Exatas)

O cronograma foi estendido de 4 para **8 semanas** (aproximadamente 2 meses) para garantir tempo suficiente para tratamento de nulos, testes de hipóteses estatísticos robustos e avaliação de alucinações nas LLMs.

### 📅 Cronograma Geral
```mermaid
gantt
    title Cronograma de Avaliação Detalhado (CRISP-DM)
    dateFormat  YYYY-MM-DD
    section CRISP-DM
    Fase 1: Entendimento do Negócio      :done, f1, 2026-06-04, 2026-06-23
    Fase 2: Entendimento dos Dados      :active, f2, 2026-06-24, 8d
    Fase 3: Preparação dos Dados         :f3, 2026-07-02, 10d
    Fase 4: Modelagem Estatística        :f4, 2026-07-12, 14d
    Fase 5: Avaliação dos Resultados     :f5, 2026-07-26, 13d
    Fase 6: Implantação e Redação Final  :f6, 2026-08-08, 15d
```

---

## 3. Detalhamento das Fases em Sub-tarefas

### 🎯 Fase 1: Business Understanding (Entendimento do Negócio)
* **Status**: **Concluído**
* **Período**: 04/06/2026 a 23/06/2026
* **Sub-tarefas**:
  - [x] Definição das perguntas centrais de pesquisa (Ex: Lojas de marca D2C performam melhor que marketplaces gerais?).
  - [x] Mapeamento dos SKUs (eletrônicos vs. skincare) e mapeamento dos canais concorrentes de venda.
  - [x] Formulação preliminar de hipóteses estatísticas sobre WPO (Web Performance Optimization) móvel vs desktop.

### 📊 Fase 2: Data Understanding (Entendimento dos Dados)
* **Período**: **24/06/2026 a 01/07/2026** (8 dias)
* **Sub-tarefas**:
  - [ ] **Amostragem**: Executar consultas piloto no BigQuery para inspecionar amostras reais de dados das quatro tabelas.
  - [ ] **Estatística Descritiva Inicial**: Gerar as contagens totais e médias básicas (médias de LCP, médias de pontuações de PageSpeed, contagem de respostas por agente).
  - [ ] **Mapeamento de Dados Faltantes (Nulos)**: Quantificar a taxa de nulos em cada métrica no CrUX e PageSpeed.
  - [ ] **Análise de Frequência e Tendência**: Verificar o padrão diário dos dados para garantir que a coleta incremental capturou variações relevantes.

### 🧹 Fase 3: Data Preparation (Preparação e Limpeza dos Dados)
* **Período**: **02/07/2026 a 11/07/2026** (10 dias)
* **Sub-tarefas**:
  - [ ] **Tratamento de Bloqueios de Bots**: Identificar e rotular registros poluídos por bloqueios de segurança (como CAPTCHAs, "Just a moment..." ou erros HTTP 403 detectados em e-commerces como Vivo e Boticário).
  - [ ] **Imputação de Nulos**: Definir a melhor técnica para lidar com registros faltantes no CrUX (por exemplo, substituir pela média da loja, utilizar interpolação temporal ou excluir o registro da comparação pareada).
  - [ ] **Recodificação e Enriquecimento (Feature Engineering)**:
    - Agrupar as lojas por seu modelo de negócio (Ex: *D2C Marca* como Apple/Natura, *Marketplace* como Amazon/Mercado Livre, *Varejo* como Casas Bahia).
    - Converter e normalizar tempos (ex: milissegundos para segundos).
  - [ ] **Consolidação (Data Merging)**: Realizar o `JOIN` das tabelas `content`, `crux` e `pagespeed` no par chave `(run_str, sku, store)` para criar a base consolidada de modelagem.

### 📐 Fase 4: Modeling (Modelagem / Análise Estatística)
* **Período**: **12/07/2026 a 25/07/2026** (14 dias)
* **Sub-tarefas**:
  - [ ] **Testes de Normalidade**: Aplicar testes como Shapiro-Wilk ou Kolmogorov-Smirnov nas variáveis de WPO para escolher entre testes paramétricos ou não-paramétricos.
  - [ ] **Análise de Variância Móvel vs Desktop**:
    - Executar o Teste T Pareado (ou Wilcoxon) para verificar a hipótese de WPO inferior em ambiente Mobile.
  - [ ] **Análise Multivariada por Canal/Loja**:
    - Aplicar ANOVA (ou Kruskal-Wallis) seguido de testes post-hoc (como Tukey HSD) para apontar quais canais têm as diferenças de carregamento mais significativas.
  - [ ] **Análise de Correlação e Regressão**:
    - Medir a correlação (Pearson/Spearman) entre PageSpeed Score e as Core Web Vitals do CrUX (FCP, LCP, INP, CLS).
    - Ajustar modelos de regressão linear para medir o poder preditivo das pontuações do PageSpeed sobre a experiência real do usuário.

### 🧪 Fase 5: Evaluation (Avaliação dos Resultados e LLMs)
* **Período**: **26/07/2026 a 07/08/2026** (13 dias)
* **Sub-tarefas**:
  - [ ] **Avaliação Quantitativa dos Agentes**:
    - Analisar o tamanho de respostas (Word Count) e tempo de latência de geração por modelo (Gemini 2.5 Flash vs Claude Haiku).
    - Mapear a taxa de erros e uso de fallback de modelos na API.
  - [ ] **Avaliação Qualitativa de Factualidade (Alucinação)**:
    - Realizar análise comparativa cruzando as lojas/preços recomendados nas respostas de IA com os dados reais de e-commerce extraídos na mesma data (tabela `content`).
    - Classificar alucinações (Ex: Recomendação de preço fora da realidade, indicação de loja que não vende o SKU, etc.).
  - [ ] **Validação com Objetivos de Negócio**: Conferir se as descobertas estatísticas e qualitativas respondem com robustez às metas iniciais da tese.

### 📝 Fase 6: Deployment (Implantação e Redação Final)
* **Período**: **08/08/2026 a 22/08/2026** (15 dias)
* **Sub-tarefas**:
  - [ ] **Exportação de Visualizações**: Salvar gráficos finais (violino, dispersão com retas de regressão e matrizes de correlação) em alta definição.
  - [ ] **Geração de Tabelas Estatísticas**: Exportar tabelas formatadas em Markdown/LaTeX com médias, p-valores e intervalos de confiança.
  - [ ] **Escrita da Seção de Resultados**: Redigir o texto descritivo e as discussões teóricas do capítulo de resultados da tese.
  - [ ] **Organização do Repositório**: Documentar o código no `README.md` final e arquivar os notebooks de análise de forma organizada.
