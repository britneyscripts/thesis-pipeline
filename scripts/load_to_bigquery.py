import os
import json
import datetime
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud import bigquery

# Category mapping per SKU
SKU_CATEGORIES = {
    "iphone-17-pro": "electronics",
    "samsung-galaxy-s26-512gb-12gb-ram-preto": "electronics",
    "motorola-edge-60-5g-512gb-azul-marinho-12gb-ram": "electronics",
    "natura-serum-intensivo-antioxidante-chronos-15ml-vitamina-c-15": "skincare",
    "la-roche-posay-pure-vitamin-c12-serum-30ml": "skincare",
    "neutrogena-hydro-boost-water-gel-50g": "skincare",
    "boticario-botik-serum-alta-potencia-vitamina-c-10-30ml": "skincare"
}

def ensure_table(bq_client, table_id, schema):
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    return table

def get_existing_keys(bq_client, table_id):
    try:
        query = f"SELECT DISTINCT run_str, sku, store FROM `{table_id}`"
        query_job = bq_client.query(query)
        results = query_job.result()
        return {(row.run_str, row.sku, row.store) for row in results}
    except Exception as e:
        print(f"Notice: Could not read existing keys from {table_id} (might be empty/new): {str(e)}")
        return set()

def process_content_json(data, run_str, sku, category, existing_keys):
    new_rows = []
    skipped_count = 0
    
    for item in data:
        store = item.get("store")
        if not store:
            continue
            
        key = (run_str, sku, store)
        if key in existing_keys:
            skipped_count += 1
            continue
            
        basic = item.get("basic_content", {})
        schema_data = item.get("schema", {})
        fields_presence = schema_data.get("fields_presence", {})
        llms_txt = item.get("llms_txt", {})
        
        schema_fields_count = sum(1 for v in fields_presence.values() if v is True)
        
        title = basic.get("title")
        word_count = basic.get("description_word_count")
        if word_count is not None:
            try:
                word_count = int(word_count)
            except (ValueError, TypeError):
                word_count = 0
        else:
            word_count = 0
            
        is_blocked = False
        if title is None:
            is_blocked = True
        else:
            title_str = str(title)
            if "Just a moment" in title_str or "Não é possível acessar" in title_str or "Mercado Libre" in title_str:
                is_blocked = True
        if word_count < 10:
            is_blocked = True
            
        row = {
            "run_str": run_str,
            "sku": sku,
            "store": store,
            "url": item.get("url"),
            "timestamp": item.get("timestamp"),
            "category": category,
            "title": title,
            "meta_description": basic.get("meta_description"),
            "h1": basic.get("h1"),
            "description_word_count": word_count,
            "has_tech_specs_table": basic.get("has_tech_specs_table"),
            "llms_txt_present": llms_txt.get("present"),
            "llms_txt_status_code": llms_txt.get("status_code"),
            "schema_fields_count": schema_fields_count,
            "schema_name": fields_presence.get("name"),
            "schema_price": fields_presence.get("price"),
            "schema_priceCurrency": fields_presence.get("priceCurrency"),
            "schema_availability": fields_presence.get("availability"),
            "schema_brand": fields_presence.get("brand"),
            "schema_description": fields_presence.get("description"),
            "schema_aggregateRating": fields_presence.get("aggregateRating"),
            "schema_image": fields_presence.get("image"),
            "schema_sku": fields_presence.get("sku"),
            "schema_gtin": fields_presence.get("gtin"),
            "schema_offers": fields_presence.get("offers"),
            "has_errors": bool(item.get("errors")),
            "extraction_blocked": is_blocked,
            "robots_txt_status_code": item.get("robots_txt", {}).get("status_code")
        }
        new_rows.append(row)
        
    return new_rows, skipped_count

def process_crux_json(data, run_str, sku, category, existing_keys):
    new_rows = []
    skipped_count = 0
    
    for item in data:
        store = item.get("store")
        if not store:
            continue
            
        key = (run_str, sku, store)
        if key in existing_keys:
            skipped_count += 1
            continue
            
        crux_data = item.get("crux", {})
        mobile = crux_data.get("mobile", {})
        desktop = crux_data.get("desktop", {})
        
        mobile_metrics = mobile.get("metrics", {})
        desktop_metrics = desktop.get("metrics", {})
        
        mobile_error = mobile.get("error")
        if isinstance(mobile_error, dict):
            mobile_error = json.dumps(mobile_error)
        elif mobile_error is not None:
            mobile_error = str(mobile_error)
            
        desktop_error = desktop.get("error")
        if isinstance(desktop_error, dict):
            desktop_error = json.dumps(desktop_error)
        elif desktop_error is not None:
            desktop_error = str(desktop_error)
            
        row = {
            "run_str": run_str,
            "sku": sku,
            "store": store,
            "url": item.get("url"),
            "timestamp": item.get("timestamp"),
            "category": category,
            "mobile_source": mobile.get("source"),
            "mobile_lcp": mobile_metrics.get("LCP"),
            "mobile_cls": mobile_metrics.get("CLS"),
            "mobile_inp": mobile_metrics.get("INP"),
            "mobile_fcp": mobile_metrics.get("FCP"),
            "mobile_ttfb": mobile_metrics.get("TTFB"),
            "mobile_error": mobile_error,
            "desktop_source": desktop.get("source"),
            "desktop_lcp": desktop_metrics.get("LCP"),
            "desktop_cls": desktop_metrics.get("CLS"),
            "desktop_inp": desktop_metrics.get("INP"),
            "desktop_fcp": desktop_metrics.get("FCP"),
            "desktop_ttfb": desktop_metrics.get("TTFB"),
            "desktop_error": desktop_error
        }
        new_rows.append(row)
        
    return new_rows, skipped_count

def process_pagespeed_json(data, run_str, sku, category, existing_keys):
    new_rows = []
    skipped_count = 0
    
    for item in data:
        store = item.get("store")
        if not store:
            continue
            
        key = (run_str, sku, store)
        if key in existing_keys:
            skipped_count += 1
            continue
            
        ps_data = item.get("pagespeed", {})
        mobile = ps_data.get("mobile", {})
        desktop = ps_data.get("desktop", {})
        
        mobile_metrics = mobile.get("metrics", {})
        
        mobile_error = mobile.get("error")
        if isinstance(mobile_error, dict):
            mobile_error = json.dumps(mobile_error)
        elif mobile_error is not None:
            mobile_error = str(mobile_error)
            
        desktop_error = desktop.get("error")
        if isinstance(desktop_error, dict):
            desktop_error = json.dumps(desktop_error)
        elif desktop_error is not None:
            desktop_error = str(desktop_error)
            
        row = {
            "run_str": run_str,
            "sku": sku,
            "store": store,
            "url": item.get("url"),
            "timestamp": item.get("timestamp"),
            "category": category,
            "mobile_score": mobile.get("score"),
            "mobile_cls": mobile_metrics.get("CLS"),
            "mobile_ttfb": mobile_metrics.get("TTFB"),
            "mobile_fcp": mobile_metrics.get("FCP"),
            "mobile_inp": mobile_metrics.get("INP"),
            "mobile_lcp": mobile_metrics.get("LCP"),
            "mobile_error": mobile_error,
            "desktop_score": desktop.get("score"),
            "desktop_error": desktop_error
        }
        new_rows.append(row)
        
    return new_rows, skipped_count

def main():
    load_dotenv()
    
    # Initialize clients
    storage_client = storage.Client()
    bq_client = bigquery.Client()
    
    bucket_name = os.getenv("GCS_BUCKET_NAME", "ghostprod-extractions")
    project_id = bq_client.project
    dataset_name = "thesisusp"
    
    print(f"Using GCS Bucket: {bucket_name}")
    print(f"Using BigQuery Project: {project_id}")
    
    # 1. Create Dataset if not exists
    dataset_ref = f"{project_id}.{dataset_name}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "southamerica-east1"
    dataset = bq_client.create_dataset(dataset, exists_ok=True)
    print(f"Ensured BigQuery dataset {dataset_ref} exists.")
    
    # Define schemas
    content_schema = [
        bigquery.SchemaField("run_str", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sku", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("store", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("meta_description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("h1", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("description_word_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("has_tech_specs_table", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("llms_txt_present", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("llms_txt_status_code", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("schema_fields_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("schema_name", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_price", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_priceCurrency", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_availability", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_brand", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_description", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_aggregateRating", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_image", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_sku", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_gtin", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("schema_offers", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("has_errors", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("extraction_blocked", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("robots_txt_status_code", "INTEGER", mode="NULLABLE"),
    ]
    
    crux_schema = [
        bigquery.SchemaField("run_str", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sku", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("store", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("mobile_source", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("mobile_lcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_cls", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_inp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_fcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_ttfb", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_error", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("desktop_source", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("desktop_lcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_cls", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_inp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_fcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_ttfb", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_error", "STRING", mode="NULLABLE"),
    ]
    
    pagespeed_schema = [
        bigquery.SchemaField("run_str", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sku", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("store", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("mobile_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_cls", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_ttfb", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_fcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_inp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_lcp", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_error", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("desktop_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("desktop_error", "STRING", mode="NULLABLE"),
    ]
    
    # 2. Ensure tables exist
    content_table_ref = f"{dataset_ref}.content"
    crux_table_ref = f"{dataset_ref}.crux"
    pagespeed_table_ref = f"{dataset_ref}.pagespeed"
    
    ensure_table(bq_client, content_table_ref, content_schema)
    ensure_table(bq_client, crux_table_ref, crux_schema)
    ensure_table(bq_client, pagespeed_table_ref, pagespeed_schema)
    print("Ensured BigQuery tables exist.")
    
    # 3. Fetch existing keys to prevent duplicates
    existing_content = get_existing_keys(bq_client, content_table_ref)
    existing_crux = get_existing_keys(bq_client, crux_table_ref)
    existing_pagespeed = get_existing_keys(bq_client, pagespeed_table_ref)
    
    print(f"Fetched existing keys: Content={len(existing_content)}, CrUX={len(existing_crux)}, PageSpeed={len(existing_pagespeed)}")
    
    # 4. List all blobs in GCS recursively
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    
    content_to_insert = []
    crux_to_insert = []
    pagespeed_to_insert = []
    
    content_skipped = 0
    crux_skipped = 0
    pagespeed_skipped = 0
    
    print("Processing GCS JSON blobs...")
    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue
            
        parts = blob.name.split("/")
        if len(parts) < 3:
            continue
            
        sku = parts[0]
        run_str = parts[1]
        filename = parts[2]
        
        # Determine category
        category = SKU_CATEGORIES.get(sku, "unknown")
        
        # Read file contents
        try:
            raw_text = blob.download_as_text()
            data = json.loads(raw_text)
        except Exception as e:
            print(f"Error reading blob {blob.name}: {str(e)}")
            continue
            
        if not isinstance(data, list):
            continue
            
        if filename.startswith("content_") and not filename.startswith("content_log_"):
            rows, skipped = process_content_json(data, run_str, sku, category, existing_content)
            content_to_insert.extend(rows)
            content_skipped += skipped
        elif filename.startswith("crux_") and not filename.startswith("crux_log_"):
            rows, skipped = process_crux_json(data, run_str, sku, category, existing_crux)
            crux_to_insert.extend(rows)
            crux_skipped += skipped
        elif filename.startswith("pagespeed_") and not filename.startswith("pagespeed_log_"):
            rows, skipped = process_pagespeed_json(data, run_str, sku, category, existing_pagespeed)
            pagespeed_to_insert.extend(rows)
            pagespeed_skipped += skipped
            
    # 5. Insert rows in batch
    content_inserted = 0
    crux_inserted = 0
    pagespeed_inserted = 0
    
    if content_to_insert:
        errors = bq_client.insert_rows_json(content_table_ref, content_to_insert)
        if errors:
            print(f"Errors inserting into content: {errors}")
        else:
            content_inserted = len(content_to_insert)
            
    if crux_to_insert:
        errors = bq_client.insert_rows_json(crux_table_ref, crux_to_insert)
        if errors:
            print(f"Errors inserting into crux: {errors}")
        else:
            crux_inserted = len(crux_to_insert)
            
    if pagespeed_to_insert:
        errors = bq_client.insert_rows_json(pagespeed_table_ref, pagespeed_to_insert)
        if errors:
            print(f"Errors inserting into pagespeed: {errors}")
        else:
            pagespeed_inserted = len(pagespeed_to_insert)
            
    # Output statistics
    print("\n=== PIPELINE LOAD STATISTICS ===")
    print(f"Content:   Inserted = {content_inserted:4d} | Skipped = {content_skipped:4d}")
    print(f"CrUX:      Inserted = {crux_inserted:4d} | Skipped = {crux_skipped:4d}")
    print(f"PageSpeed: Inserted = {pagespeed_inserted:4d} | Skipped = {pagespeed_skipped:4d}")
    print("================================")

if __name__ == "__main__":
    main()
