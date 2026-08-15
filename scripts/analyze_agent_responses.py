import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Initialize BigQuery client
    client = bigquery.Client()
    project_id = client.project
    dataset_name = "thesisusp"
    table_id = f"{project_id}.{dataset_name}.agent_responses"
    
    print(f"Querying table: {table_id}")
    
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
    
    print("\n--- Summary per Agent/Model ---")
    df_summary = client.query(query_summary).to_dataframe()
    print(df_summary.to_string(index=False))
    
    # 2. Errors detail
    query_errors = f"""
    SELECT 
      agent,
      model_used,
      error,
      COUNT(*) as occurrences
    FROM `{table_id}`
    WHERE error IS NOT NULL
    GROUP BY agent, model_used, error
    ORDER BY occurrences DESC
    """
    
    print("\n--- Errors Breakdown ---")
    df_errors = client.query(query_errors).to_dataframe()
    if df_errors.empty:
        print("No errors found!")
    else:
        print(df_errors.to_string(index=False))
        
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
    
    print("\n--- Summary by Query Type ---")
    df_by_type = client.query(query_by_type).to_dataframe()
    print(df_by_type.to_string(index=False))
    
    # 4. Latency analysis
    print("\n--- Latency Percentiles (ms) ---")
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
    print(df_perc.to_string(index=False))

    # 5. Retrieve examples of responses to assess qualitative quality
    query_samples = f"""
    SELECT 
      agent,
      query_type,
      product,
      query,
      response_text
    FROM `{table_id}`
    WHERE error IS NULL
    ORDER BY query_type, product, agent
    LIMIT 20
    """
    print("\n--- Sample Responses ---")
    df_samples = client.query(query_samples).to_dataframe()
    for idx, row in df_samples.head(6).iterrows():
        print("="*80)
        print(f"Agent: {row['agent']} | Type: {row['query_type']} | Product: {row['product']}")
        print(f"Query: {row['query']}")
        print("-" * 40)
        # print first 300 chars of the response
        resp = row['response_text'] or ""
        print(resp[:400] + ("..." if len(resp) > 400 else ""))
        print("="*80)

if __name__ == "__main__":
    main()
