import os
import sys
import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

# Allow running from project root or scripts/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_to_bigquery import (
    ensure_table,
    process_agent_citations,
    get_existing_citation_keys,
    AGENT_CITATIONS_SCHEMA
)

def main():
    load_dotenv()
    
    bq_client = bigquery.Client(project="thesisusp")
    dataset_name = "thesisusp"
    dataset_ref = f"thesisusp.{dataset_name}"
    
    responses_table_id = f"{dataset_ref}.agent_responses"
    citations_table_id = f"{dataset_ref}.agent_citations"
    
    print(f"=== Backfilling store citations ===")
    print(f"Querying historical responses from: {responses_table_id}")
    
    # Ensure citations table exists
    ensure_table(bq_client, citations_table_id, AGENT_CITATIONS_SCHEMA)
    print(f"Ensured BigQuery table {citations_table_id} exists.")
    
    # Query all successful responses
    query = f"""
    SELECT 
      run_str,
      agent,
      product,
      query_type,
      response_text,
      timestamp
    FROM `{responses_table_id}`
    WHERE error IS NULL
    """
    
    try:
        results = bq_client.query(query).result()
        # Convert results to a list of dicts
        response_items = []
        for row in results:
            response_items.append({
                "run_str": row.run_str,
                "agent": row.agent,
                "product": row.product,
                "query_type": row.query_type,
                "response_text": row.response_text,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None
            })
        print(f"Found {len(response_items)} historical successful agent responses to parse.")
    except Exception as e:
        print(f"Error querying agent_responses: {e}")
        sys.exit(1)
        
    # Get already loaded citation keys to avoid duplicates
    existing_keys = get_existing_citation_keys(bq_client, citations_table_id)
    print(f"Found {len(existing_keys)} existing citation records in BigQuery.")
    
    # Extract citations
    new_citation_rows, skipped = process_agent_citations(response_items, existing_keys)
    print(f"Extraction complete. New records to insert: {len(new_citation_rows)} | Skipped (duplicates): {skipped}")
    
    # Batch load to BigQuery
    inserted = 0
    if new_citation_rows:
        print(f"Loading {len(new_citation_rows)} rows to {citations_table_id}...")
        # Since insert_rows_json is limited by chunk size, we can chunk if needed,
        # but for a few thousand rows direct insertion is fine.
        errors = bq_client.insert_rows_json(citations_table_id, new_citation_rows)
        if errors:
            print(f"Errors inserting agent_citations: {errors}")
            sys.exit(1)
        else:
            inserted = len(new_citation_rows)
            
    print("\n=== CITATIONS BACKFILL COMPLETED ===")
    print(f"Successfully backfilled: {inserted:4d} records.")
    print("====================================")

if __name__ == "__main__":
    main()
