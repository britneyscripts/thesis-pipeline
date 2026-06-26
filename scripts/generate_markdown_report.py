import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

def df_to_markdown(df):
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(map(str, headers)) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        # Replace newlines in cell values to avoid breaking markdown tables
        row_str = [str(val).replace('\n', ' ') for val in row.values]
        lines.append("| " + " | ".join(row_str) + " |")
    return "\n".join(lines)

def clean_error_msg(err):
    if not err:
        return ""
    err_str = str(err)
    if "aiplatform.endpoints.predict" in err_str:
        return "403 PERMISSION_DENIED: aiplatform.endpoints.predict denied on resource (Vertex AI)"
    elif "Your credit balance is too low" in err_str:
        return "400 Anthropic: Credit balance too low to access Anthropic API"
    elif "was not found or your project does not have access to it" in err_str:
        return "404 Vertex AI: Publisher model not found or project has no access"
    elif "is not found for API version v1beta" in err_str:
        return "404 Gemini: Model not found or not supported in v1beta"
    else:
        return err_str[:120] + "..." if len(err_str) > 120 else err_str

def main():
    load_dotenv()
    
    # Initialize BigQuery client
    client = bigquery.Client(project="thesisusp")
    dataset_name = "thesisusp"
    table_id = f"thesisusp.{dataset_name}.agent_responses"
    citations_table_id = f"thesisusp.{dataset_name}.agent_citations"
    
    print(f"Running report generation from table: {table_id}")
    
    # 1. General counts and fallbacks
    query_summary = f"""
    SELECT 
      agent,
      model_used,
      fallback_used,
      COUNT(*) as total_runs,
      COUNTIF(error IS NOT NULL) as error_count,
      COUNTIF(error IS NULL) as success_count,
      ROUND(AVG(latency_ms), 2) as avg_latency_ms,
      ROUND(AVG(response_length), 2) as avg_response_length_chars
    FROM `{table_id}`
    GROUP BY agent, model_used, fallback_used
    ORDER BY total_runs DESC
    """
    df_summary = client.query(query_summary).to_dataframe()
    
    # 2. Errors detail (fetch all errors, clean them up and group them in Python)
    query_errors = f"""
    SELECT 
      agent,
      model_used,
      error
    FROM `{table_id}`
    WHERE error IS NOT NULL
    """
    df_errors_raw = client.query(query_errors).to_dataframe()
    
    if not df_errors_raw.empty:
        df_errors_raw['clean_error'] = df_errors_raw['error'].apply(clean_error_msg)
        df_errors = df_errors_raw.groupby(['agent', 'model_used', 'clean_error']).size().reset_index(name='occurrences')
        df_errors = df_errors.sort_values(by='occurrences', ascending=False)
    else:
        df_errors = pd.DataFrame(columns=['agent', 'model_used', 'clean_error', 'occurrences'])
        
    # 3. Performance by Query Type
    query_by_type = f"""
    SELECT 
      agent,
      query_type,
      COUNT(*) as total_runs,
      ROUND(AVG(latency_ms), 2) as avg_latency_ms,
      ROUND(AVG(response_length), 2) as avg_response_length
    FROM `{table_id}`
    WHERE error IS NULL
    GROUP BY agent, query_type
    ORDER BY query_type, agent
    """
    df_by_type = client.query(query_by_type).to_dataframe()
    
    # 4. Latency analysis
    query_percentiles = f"""
    SELECT
      agent,
      COUNT(*) as count,
      MIN(latency_ms) as min_lat,
      APPROX_QUANTILES(latency_ms, 100)[OFFSET(50)] as median_lat,
      APPROX_QUANTILES(latency_ms, 100)[OFFSET(90)] as p90_lat,
      MAX(latency_ms) as max_lat
    FROM `{table_id}`
    WHERE error IS NULL
    GROUP BY agent
    """
    df_perc = client.query(query_percentiles).to_dataframe()

    # 5. Citations by Store
    query_citations_by_store = f"""
    SELECT 
      store_cited,
      COUNTIF(cited = TRUE) as total_cited,
      COUNTIF(cited = TRUE AND citation_sentiment = 'positive') as positive_citations,
      COUNTIF(cited = TRUE AND citation_sentiment = 'neutral') as neutral_citations,
      COUNTIF(cited = TRUE AND citation_sentiment = 'negative') as negative_citations
    FROM `{citations_table_id}`
    GROUP BY store_cited
    ORDER BY total_cited DESC
    """
    df_cit_store = client.query(query_citations_by_store).to_dataframe()

    # 6. Citations by Agent
    query_citations_by_agent = f"""
    SELECT 
      agent,
      COUNT(*) as total_checks,
      COUNTIF(cited = TRUE) as total_cited,
      ROUND(COUNTIF(cited = TRUE) / COUNT(*), 4) * 100 as citation_rate_pct
    FROM `{citations_table_id}`
    GROUP BY agent
    ORDER BY citation_rate_pct DESC
    """
    df_cit_agent = client.query(query_citations_by_agent).to_dataframe()

    # 7. Sample responses for iPhone 17 Pro and Boticario Botik (some examples)
    query_samples = f"""
    SELECT 
      agent,
      query_type,
      product,
      query,
      response_text
    FROM `{table_id}`
    WHERE error IS NULL AND product IN ('iphone-17-pro', 'boticario-botik')
    ORDER BY product, query_type, agent
    LIMIT 10
    """
    df_samples = client.query(query_samples).to_dataframe()

    # Build Markdown report
    md = []
    md.append("# Resultados da Extração de Agentes (`extract_agent_responses`) - Acumulado até Hoje\n")
    md.append("Este relatório apresenta um resumo estatístico e qualitativo das execuções dos agentes de recomendação de compras baseados em LLMs, extraídos da tabela `thesisusp.agent_responses` no BigQuery.\n")
    
    md.append("## 1. Visão Geral de Execuções e Modelos\n")
    md.append("Resumo quantitativo de execuções por agente, modelo real utilizado, uso de fallback e latência média:\n")
    md.append(df_to_markdown(df_summary) + "\n")
    
    md.append("## 2. Detalhamento de Erros e Falhas\n")
    if df_errors.empty:
        md.append("Não foram encontrados registros de erros nas execuções.\n")
    else:
        md.append("Ocorrências de falhas agrupadas por agente, modelo e mensagem de erro simplificada:\n")
        md.append(df_to_markdown(df_errors) + "\n")
        
    md.append("## 3. Desempenho por Tipo de Consulta\n")
    md.append("Estatísticas de latência e tamanho de resposta divididas pelo tipo de consulta (`brand`, `generic`, `product_exact`):\n")
    md.append(df_to_markdown(df_by_type) + "\n")
    
    md.append("## 4. Percentis de Latência (ms)\n")
    md.append("Distribuição detalhada de latência apenas para chamadas com sucesso:\n")
    md.append(df_to_markdown(df_perc) + "\n")

    md.append("## 5. Análise de Citações por Loja / Canal de E-commerce\n")
    md.append("Total de vezes em que cada loja foi citada e a distribuição de sentimento da citação (positivo, neutro, negativo):\n")
    md.append(df_to_markdown(df_cit_store) + "\n")

    md.append("## 6. Taxa de Citação Geral por Agente\n")
    md.append("Porcentagem de citações bem-sucedidas em relação ao total de oportunidades de citação por agente:\n")
    md.append(df_to_markdown(df_cit_agent) + "\n")
    
    md.append("## 7. Exemplos de Respostas dos Agentes\n")
    md.append("Abaixo estão algumas amostras das respostas retornadas pelos modelos:\n")
    
    for idx, row in df_samples.iterrows():
        md.append(f"### Agente: `{row['agent']}` | Produto: `{row['product']}` ({row['query_type']})\n")
        md.append(f"**Pergunta:** *{row['query']}*\n")
        resp = row['response_text'] or ""
        # Format the response in a blockquote
        resp_indented = "\n".join([f"> {line}" for line in resp.split("\n")])
        md.append(resp_indented + "\n")
        md.append("\n---\n")

    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "agent_results_summary_accumulated.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    print(f"Report successfully generated at: {report_path}")

if __name__ == "__main__":
    main()
