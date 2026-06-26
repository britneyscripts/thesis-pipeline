import os
import sys
from google.cloud import bigquery
from google.cloud import storage
from dotenv import load_dotenv

# Adding project root to sys.path so we can import packages
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)

OLD_SKU = "motorola-edge-60-5g-512gb-azul-marinho-12gb-ram"
NEW_SKU = "samsung-galaxy-a56-5g-256gb-preto-8gb-ram"

def migrate_bigquery(project_id, dataset_name):
    print("--- 1. BigQuery Migration ---")
    bq_client = bigquery.Client(project=project_id)
    
    # We will update content, crux, and pagespeed tables
    tables = ["content", "crux", "pagespeed"]
    
    for table in tables:
        table_ref = f"{project_id}.{dataset_name}.{table}"
        print(f"Updating table: {table_ref}...")
        
        # Check if table exists first
        try:
            bq_client.get_table(table_ref)
        except Exception:
            print(f"Table {table_ref} not found, skipping.")
            continue
            
        query = f"""
        UPDATE `{table_ref}`
        SET sku = '{NEW_SKU}'
        WHERE sku = '{OLD_SKU}'
        """
        
        try:
            query_job = bq_client.query(query)
            results = query_job.result() # Wait for job to complete
            
            # Get number of affected rows
            num_rows = query_job.num_dml_affected_rows
            print(f"  SUCCESS: Updated {num_rows} rows in {table}.")
        except Exception as e:
            print(f"  ERROR updating {table}: {str(e)}")
            
    # Also update agent_citations if they exist
    citations_table_ref = f"{project_id}.{dataset_name}.agent_citations"
    try:
        bq_client.get_table(citations_table_ref)
        print(f"Checking agent_citations table: {citations_table_ref}...")
        query_cit = f"""
        UPDATE `{citations_table_ref}`
        SET sku = '{NEW_SKU}'
        WHERE sku = '{OLD_SKU}'
        """
        query_job = bq_client.query(query_cit)
        query_job.result()
        print(f"  SUCCESS: Updated {query_job.num_dml_affected_rows} rows in agent_citations.")
    except Exception as e:
        print(f"  Notice (agent_citations): {str(e)}")

def migrate_gcs(project_id, bucket_name):
    print("\n--- 2. Google Cloud Storage Migration ---")
    storage_client = storage.Client(project=project_id)
    
    try:
        bucket = storage_client.bucket(bucket_name)
        print(f"Listing blobs in bucket '{bucket_name}' with prefix '{OLD_SKU}/'...")
        blobs = list(bucket.list_blobs(prefix=f"{OLD_SKU}/"))
        
        if not blobs:
            print("No GCS blobs found to migrate.")
            return
            
        print(f"Found {len(blobs)} blobs. Renaming...")
        copied_count = 0
        deleted_count = 0
        
        for blob in blobs:
            # e.g., motorola-edge-60-5g-.../20260604_1000/content_20260604_1000.json
            new_name = blob.name.replace(OLD_SKU, NEW_SKU, 1)
            print(f"  Copying {blob.name} \n       -> {new_name}")
            
            try:
                # Copy blob to new name
                bucket.copy_blob(blob, bucket, new_name)
                copied_count += 1
                
                # Delete old blob
                blob.delete()
                deleted_count += 1
            except Exception as e:
                print(f"  ERROR migrating blob {blob.name}: {str(e)}")
                
        print(f"GCS migration complete: Copied {copied_count}/{len(blobs)} | Deleted {deleted_count}/{len(blobs)} blobs.")
        
    except Exception as e:
        print(f"GCS Migration failed: {str(e)}")

def migrate_local():
    print("\n--- 3. Local Filesystem Migration ---")
    local_extractions = os.path.join(base_dir, "extractions")
    
    if not os.path.exists(local_extractions):
        print("Local 'extractions' directory not found.")
        return
        
    old_local_dir = os.path.join(local_extractions, OLD_SKU)
    new_local_dir = os.path.join(local_extractions, NEW_SKU)
    
    if os.path.exists(old_local_dir):
        print(f"Found old local directory: {old_local_dir}")
        try:
            os.rename(old_local_dir, new_local_dir)
            print(f"  SUCCESS: Renamed to {new_local_dir}")
        except Exception as e:
            print(f"  ERROR renaming local directory: {str(e)}")
    else:
        print("No old local directory found to rename.")

def main():
    load_dotenv()
    
    # Read environment config
    project_id = os.getenv("GCP_PROJECT_ID") or "thesisusp"
    dataset_name = "thesisusp"
    bucket_name = os.getenv("GCS_BUCKET_NAME") or "ghostprod-extractions"
    
    print("====================================================")
    print("SKU MIGRATION SCRIPT")
    print(f"OLD SKU: {OLD_SKU}")
    print(f"NEW SKU: {NEW_SKU}")
    print(f"GCP Project: {project_id}")
    print(f"BigQuery Dataset: {dataset_name}")
    print(f"GCS Bucket: {bucket_name}")
    print("====================================================")
    
    migrate_bigquery(project_id, dataset_name)
    migrate_gcs(project_id, bucket_name)
    migrate_local()
    
    print("\n=== SKU MIGRATION COMPLETE ===")

if __name__ == "__main__":
    main()
