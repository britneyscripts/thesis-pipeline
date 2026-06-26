# Relatório de Análise dos Resultados: Modelos de IA (Gemini vs. Claude)

Este documento apresenta a análise dos primeiros resultados obtidos na execução dos agentes comparativos no BigQuery (`thesisusp.agent_responses`). O objetivo desta análise é subsidiar a **Fase 5 (Evaluation/Avaliação)** da metodologia CRISP-DM adotada na dissertação de MBA.

---

## 1. Resumo Executivo (Executiva de Resultados)

Foram analisadas as execuções dos modelos configurados no pipeline. A análise revela dados quantitativos sobre a viabilidade operacional (latência, taxas de erro e falhas de fallback) e aspectos qualitativos fundamentais sobre o comportamento dos modelos gerativos em cenários de recomendação de compras.

*   **Pivô para Google Cloud (Vertex AI) validado**: Enquanto a API da Anthropic (Claude) falhou por completo por falta de créditos, os modelos Gemini 2.5 via Vertex AI executaram com 100% de sucesso.
*   **Problema de Latência Crítico no Pro**: O modelo `gemini-2.5-pro` demonstrou uma latência mediana de **29,9 segundos**, o que inviabiliza sua aplicação em chat em tempo real (UX). O `gemini-2.5-flash` obteve latência de **16,2 segundos** (quase metade do tempo).
*   **Deriva Temporal / Alinhamento Temporal**: Todos os modelos demonstraram uma "âncora temporal" desatualizada (corte em meados de 2024), afirmando que o iPhone 17 Pro não existe e que o iPhone 16 é o próximo lançamento de 2024. Isso evidencia a necessidade técnica de **Google Search Grounding** para aplicações comerciais em 2026.
*   **Erro de Configuração no Gemini 1.5**: O modelo `gemini-1.5-flash` falhou 100% das vezes com erro de Vertex AI 404 (model ID inválido ou não disponível no projeto).

---

## 2. Análise Quantitativa

A tabela abaixo sumariza as métricas extraídas diretamente do banco de dados `thesisusp.agent_responses`:

| Agente / Modelo | Modelo Executado | Fallback Utilizado | Execuções | Sucessos | Falhas | Latência Média (ms) | Tam. Médio Resp. (chars) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **claude** | `claude-haiku-4-5-20251001` | Sim | 42 | 0 | 42 | - | 0 |
| **gemini-1.5-flash** | `gemini-1.5-flash-lite` | Sim | 21 | 0 | 21 | - | 0 |
| **gemini** (antigo) | `gemini-1.5-flash` | Sim | 21 | 0 | 21 | - | 0 |
| **gemini** | `gemini-2.5-flash` | Não | 21 | 21 | 0 | 17.906 | 3.833 |
| **gemini-2.5-flash** | `gemini-2.5-flash` | Não | 21 | 21 | 0 | 17.743 | 3.643 |
| **gemini-2.5-pro** | `gemini-2.5-pro` | Não | 21 | 21 | 0 | 29.538 | 3.846 |

### 2.1 Análise de Latência (Apenas Sucessos)
A latência é um gargalo central em aplicações interativas de comércio eletrônico.

*   **Gemini 2.5 Flash**:
    *   Mínimo: **12,6s**
    *   Mediano: **16,2s**
    *   Máximo: **25,8s**
*   **Gemini 2.5 Pro**:
    *   Mínimo: **21,2s**
    *   Mediano: **29,9s**
    *   Máximo: **38,3s**

> [!WARNING]
> A latência média do Gemini 2.5 Pro aproxima-se de **30 segundos**. Em termos de UX (Experiência do Usuário), tempos de espera superiores a 5 segundos causam abandono massivo. Para o pipeline assíncrono de recomendação, o Pro é excelente pela profundidade, mas para um agente interativo (Chatbot), o **Flash** é a escolha ideal, embora ainda precise de otimizações de streaming.

### 2.2 Detalhamento de Erros

1.  **Anthropic (Claude)**: 100% de erro 400.
    *   *Mensagem*: `"Your credit balance is too low to access the Anthropic API."`
    *   *Diagnóstico*: Confirma a restrição orçamentária e a assertividade da decisão de pivotar para os modelos do Google.
2.  **Gemini 1.5 Flash (Vertex AI)**: 100% de erro 404.
    *   *Mensagem*: `"Publisher model projects/thesisusp/locations/us-central1/publishers/google/models/gemini-1.5-flash-lite was not found..."`
    *   *Diagnóstico*: O modelo `gemini-1.5-flash-lite` (fallback do 1.5) ou o `gemini-1.5-flash` não estão disponíveis no endpoint regional especificado ou a string de chamada do Vertex AI está incorreta no SDK da Vertex.

---

## 3. Análise Qualitativa e Comportamento dos Modelos

### 3.1 Limitação de Memória Paramétrica: Ausência de Grounding em Tempo Real
Ao realizar a consulta do produto **iPhone 17 Pro** (definido no prompt como consulta de marca e exata), os modelos responderam o seguinte:

*   **Gemini 2.5 Pro**:
    > *"o Apple iPhone 17 Pro ainda não foi anunciado ou lançado pela Apple. [...] Atualmente, o modelo mais recente é o iPhone 15. O próximo lançamento esperado é o iPhone 16 (provavelmente em setembro de 2024)."*
*   **Gemini 2.5 Flash**:
    > *"Até o momento, o iPhone 17 Pro não foi lançado pela Apple. [...] Os modelos mais recentes disponíveis são da linha iPhone 15. O iPhone 16 é esperado em setembro de 2024."*

**Implicações de Negócio e de Pesquisa (Tese)**:
Estamos em **junho de 2026**. Os modelos responderam que o iPhone 15 é o mais novo e que o iPhone 16 sairá em setembro de 2024. Isso ilustra de forma prática o fenômeno de **Knowledge Cutoff** e a dependência exclusiva da **Memória Paramétrica** (Mallen et al., 2023), em oposição ao uso de **Retrieval-Augmented Generation (RAG)** ou ferramentas de **Search Grounding** em tempo real.
*   **Limitação da Memória Paramétrica**: Os pesos internos do modelo retêm apenas as informações consolidadas até o seu momento de corte de treinamento. Sem grounding externo, o modelo reconstrói uma resposta baseada unicamente nessa memória estática.
*   **Ausência de Grounding**: Para aplicações comerciais dinâmicas em e-commerce, a ausência de um mecanismo de recuperação em tempo real (como o Google Search Grounding) resulta em alucinações temporais severas e invalida a recomendação de produtos recentemente lançados.

### 3.2 Estrutura e Qualidade das Respostas (Skincare)
Para consultas reais de produtos de skincare (**La Roche-Posay Vitamina C12**, **Natura Chronos**), ambos os modelos performaram muito bem estruturalmente:

*   **Estrutura de Tópicos**: Apresentam as informações com formatação Markdown impecável, listando lojas físicas e e-commerces conhecidos no Brasil (Droga Raia, Drogasil, Pague Menos, Beleza na Web).
*   **Tom de Assistente**: Adotam uma linguagem polida, amigável e focada na ajuda ao consumidor, exatamente conforme instruído no `SYSTEM_PROMPT`.
*   **Profundidade**: O **Gemini 2.5 Pro** oferece uma divisão mais refinada de sugestões dermatológicas por faixa de preço (Ex: Separando marcas de luxo como Skinceuticals de marcas nacionais de bom custo-benefício como O Boticário), enquanto o **Flash** tende a ser mais direto nas listas de farmácias.

---

## 4. Recomendações e Próximos Passos na Tese

Com base nesses primeiros resultados, as seguintes ações e conclusões devem ser integradas à tese:

1.  **Escolha do Modelo Base**:
    *   **Recomendação**: Usar o `gemini-2.5-flash` como modelo principal devido à sua eficiência de latência (~16s contra ~30s) e menor custo.
    *   **Fallback**: Configurar o `gemini-2.5-flash` para cair para um modelo local ou manter o Vertex AI ajustado, descartando a tentativa de fallback para Claude.
2.  **Habilitar Grounding (Pesquisa Integrada)**:
    *   Para mitigar o problema do iPhone 17 Pro (deriva temporal de 2026), deve-se implementar o `Google Search tool` nativo do SDK do Gemini. Isso trará preços reais e dados de estoque atualizados.
3.  **Correção do Gemini 1.5**:
    *   Verificar o nome exato dos modelos do Vertex AI em `scripts/extract_agent_responses.py` para corrigir o erro 404 (provavelmente mapeando para `gemini-1.5-flash-002` ou similar).
