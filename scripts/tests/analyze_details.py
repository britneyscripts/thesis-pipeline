import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = bigquery.Client()
    project_id = client.project
    dataset_name = "thesisusp"
    table_id = f"{project_id}.{dataset_name}.agent_responses"
    
    # Let's query some skincare results
    query = f"""
    SELECT 
      agent,
      product,
      query_type,
      query,
      response_text
    FROM `{table_id}`
    WHERE error IS NULL AND category = 'skincare'
    ORDER BY product, query_type, agent
    """
    
    df = client.query(query).to_dataframe()
    
    # We will print examples of how gemini-2.5-flash and gemini-2.5-pro answered the same queries
    products = df['product'].unique()
    for prod in products[:3]:
        prod_df = df[df['product'] == prod]
        print("="*100)
        print(f"PRODUCT: {prod.upper()}")
        print("="*100)
        
        q_types = prod_df['query_type'].unique()
        for qt in q_types[:2]:
            qt_df = prod_df[prod_df['query_type'] == qt]
            print(f"\nQuery Type: {qt} | Query: {qt_df['query'].iloc[0]}")
            print("-" * 50)
            
            for idx, row in qt_df.iterrows():
                print(f"[{row['agent']}]:")
                resp = row['response_text'] or ""
                # print first 500 characters
                print(resp[:600] + ("..." if len(resp) > 600 else ""))
                print("." * 30)

if __name__ == "__main__":
    main()
