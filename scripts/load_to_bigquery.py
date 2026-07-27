import os
import json
import datetime
import re
from dotenv import load_dotenv
from google.cloud import storage
from google.cloud import bigquery

# Category mapping per SKU
SKU_CATEGORIES = {
    "iphone-17-pro": "electronics",
    "samsung-galaxy-s26-512gb-12gb-ram-preto": "electronics",
    "samsung-galaxy-a56-5g-256gb-preto-8gb-ram": "electronics",
    "natura-serum-intensivo-antioxidante-chronos-15ml-vitamina-c-15": "skincare",
    "la-roche-posay-pure-vitamin-c12-serum-30ml": "skincare",
    "neutrogena-hydro-boost-water-gel-50g": "skincare",
    "boticario-botik-serum-alta-potencia-vitamina-c-10-30ml": "skincare",
    "sallve-antioxidante-hidratante-35g": "skincare",
    "creamy-skincare-vitamina-c-serum-30g": "skincare",
    "principia-serum-vitamina-c-10-vc-10-30ml": "skincare",
    "beyoung-booster-antiaging-serum-30ml": "skincare",
    "adcos-derma-complex-vitamina-c-20-30ml": "skincare",
    "dermage-improve-c-20-serum-antioxidante-30ml": "skincare"
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

def load_all():
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
    if bucket:
        try:
            blobs = bucket.list_blobs()
            for blob in blobs:
                if not blob.name.endswith(".json"):
                    continue
                parts = blob.name.split("/")
                if len(parts) < 3:
                    continue
                sku = parts[0]
                run_str = parts[1]
                filename = parts[2]
                category = SKU_CATEGORIES.get(sku, "unknown")
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
        except Exception as e:
            print(f"Notice: GCS blob listing skipped or unavailable: {str(e)}")

    # 4b. Also scan local extractions directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    extractions_dir = os.path.join(base_dir, "extractions")
    
    if os.path.exists(extractions_dir):
        print(f"Processing local extractions from {extractions_dir}...")
        for root, dirs, files in os.walk(extractions_dir):
            for file in files:
                if not file.endswith(".json"):
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), extractions_dir)
                parts = rel_path.split(os.sep)
                if len(parts) < 3:
                    continue
                sku = parts[0]
                run_str = parts[1]
                filename = parts[2]
                category = SKU_CATEGORIES.get(sku, "unknown")
                
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"Error reading local file {rel_path}: {str(e)}")
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

# ---------------------------------------------------------------------------
# Agent responses loader
# ---------------------------------------------------------------------------

AGENT_RESPONSES_SCHEMA = [
    bigquery.SchemaField("run_str", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("agent", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("model_used", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("fallback_used", "BOOLEAN", mode="REQUIRED"),
    bigquery.SchemaField("query_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("product", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("query", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("response_text", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("grounding_uris", "STRING", mode="REPEATED"),
    bigquery.SchemaField("response_length", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("latency_ms", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("error", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
]

AGENT_CITATIONS_SCHEMA = [
    bigquery.SchemaField("run_str", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("sku", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("store_cited", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("agent", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("query_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("cited", "BOOLEAN", mode="REQUIRED"),
    bigquery.SchemaField("citation_tier", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("citation_score", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("citation_sentiment", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
]

STORE_ALIASES = {
    "Apple Brasil": ["apple", "apple brasil", "loja da apple"],
    "Vivo": ["vivo"],
    "Fastshop": ["fast shop", "fastshop"],
    "Americanas": ["americanas", "lojas americanas"],
    "Kabum": ["kabum", "kabum!"],
    "Amazon Brasil": ["amazon", "amazon.com.br", "amazon brasil"],
    "Samsung": ["samsung", "loja da samsung"],
    "Magazine Luiza": ["magazine luiza", "magalu", "magazineluiza"],
    "Mercado Livre": ["mercado livre", "mercadolivre", "mercado libre"],
    "Natura Brasil": ["natura", "natura brasil"],
    "La Roche-Posay Brasil": ["la roche", "roche posay", "la roche-posay", "la roche posay"],
    "Droga Raia": ["droga raia", "raia"],
    "Drogasil": ["drogasil"],
    "Pague Menos": ["pague menos"],
    "Cosmetis": ["cosmetis"],
    "Neutrogena": ["neutrogena"],
    "Boticário": ["boticário", "o boticário", "botik"],
    "Panvel": ["panvel"],
    "Beleza na Web": ["beleza na web"],
    "Época Cosméticos": ["época cosméticos", "epoca cosmeticos"],
    "Drogaria São Paulo": ["drogaria são paulo", "drogaria sao paulo"],
    "Drogaria Pacheco": ["pacheco", "drogaria pacheco"]
}

def get_existing_agent_keys(bq_client, table_id):
    """Return a set of (run_str, agent, product, query_type) tuples already in BigQuery."""
    try:
        query = f"SELECT DISTINCT run_str, agent, product, query_type FROM `{table_id}`"
        results = bq_client.query(query).result()
        return {(row.run_str, row.agent, row.product, row.query_type) for row in results}
    except Exception as e:
        print(f"Notice: Could not read existing keys from {table_id} (might be empty/new): {str(e)}")
        return set()

def get_existing_citation_keys(bq_client, table_id):
    """Return a set of (run_str, agent, sku, store_cited) tuples already in BigQuery."""
    try:
        query = f"SELECT DISTINCT run_str, agent, sku, store_cited FROM `{table_id}`"
        results = bq_client.query(query).result()
        return {(row.run_str, row.agent, row.sku, row.store_cited) for row in results}
    except Exception as e:
        print(f"Notice: Could not read existing citation keys from {table_id} (might be empty/new): {str(e)}")
        return set()

def get_citation_sentiment(text_lower, alias_list):
    """Detect sentiment for a matched store in a window of 120 chars before/after."""
    idx = -1
    matched_alias = None
    for alias in alias_list:
        i = text_lower.find(alias)
        if i != -1:
            idx = i
            matched_alias = alias
            break
            
    if idx == -1:
        return "neutral"
        
    start = max(0, idx - 120)
    end = min(len(text_lower), idx + len(matched_alias) + 120)
    window = text_lower[start:end]
    
    negatives = [
        "evite", "evitar", "cuidado", "falsific", "pirata", "não recomendo", 
        "perigo", "não oficial", "terceirizados", "terceiros", "atenção", 
        "alerta", "golpe", "fraude", "confiável?", "desconfie"
    ]
    
    positives = [
        "recomendo", "melhor", "seguro", "oficial", "confiável", "excelente", 
        "ótimo", "garantia", "original"
    ]
    
    for neg in negatives:
        if neg in window:
            return "negative"
            
    for pos in positives:
        if pos in window:
            return "positive"
            
    return "neutral"

def process_agent_responses(data, existing_keys):
    """Filter out already-loaded rows and return new rows ready for BigQuery insertion."""
    new_rows = []
    skipped_count = 0

    for item in data:
        key = (item.get("run_str"), item.get("agent"), item.get("product"), item.get("query_type"))
        if key in existing_keys:
            skipped_count += 1
            continue

        # Coerce types to match BigQuery schema
        row = {
            "run_str": item.get("run_str"),
            "agent": item.get("agent"),
            "model_used": item.get("model_used"),
            "fallback_used": bool(item.get("fallback_used", False)),
            "query_type": item.get("query_type"),
            "product": item.get("product"),
            "category": item.get("category"),
            "query": item.get("query"),
            "response_text": item.get("response_text"),
            "grounding_uris": item.get("grounding_uris") or [],
            "response_length": int(item.get("response_length") or 0),
            "latency_ms": int(item.get("latency_ms") or 0),
            "error": item.get("error"),
            "timestamp": item.get("timestamp"),
        }
        new_rows.append(row)

    return new_rows, skipped_count

def process_agent_citations(results, existing_keys):
    """Extract store citations from agent response text & grounding metadata using 5-Tier Scoring System."""
    new_rows = []
    skipped_count = 0
    now_iso = datetime.datetime.now().isoformat()
    
    for item in results:
        run_str = item.get("run_str")
        agent = item.get("agent")
        sku = item.get("product") or item.get("sku")
        query_type = item.get("query_type")
        response_text = item.get("response_text") or ""
        grounding_uris = item.get("grounding_uris") or []
        timestamp = item.get("timestamp") or now_iso
        
        if not run_str or not agent or not sku:
            continue
            
        text_lower = response_text.lower()
        uris_lower = [u.lower() for u in grounding_uris]
        
        for store, aliases in STORE_ALIASES.items():
            key = (run_str, agent, sku, store)
            if key in existing_keys:
                skipped_count += 1
                continue
                
            # Compute 5-Tier Citation Hierarchy
            citation_tier = 0
            citation_score = 0
            cited = False
            
            # Check Tier 4: Exact Grounded URI in grounding_chunks
            has_grounded_uri = False
            for uri in uris_lower:
                for alias in aliases:
                    if len(alias) > 3 and alias in uri:
                        has_grounded_uri = True
                        break
                if has_grounded_uri:
                    break

            # Search for alias match in conversational text
            text_mentioned = False
            for alias in aliases:
                if len(alias) <= 4:
                    if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                        text_mentioned = True
                        break
                else:
                    if alias in text_lower:
                        text_mentioned = True
                        break
            
            # Assign Tiers & Scores
            if has_grounded_uri:
                citation_tier = 4
                citation_score = 100
                cited = True
            elif text_mentioned:
                # Check for product/store price context (Tier 2 vs Tier 1)
                if any(kw in text_lower for kw in ["r$", "reais", "preço", "preco", "loja", "site", "comprar"]):
                    citation_tier = 2
                    citation_score = 50
                else:
                    citation_tier = 1
                    citation_score = 25
                cited = True
            else:
                citation_tier = 0
                citation_score = 0
                cited = False
            
            sentiment = None
            if cited:
                sentiment = get_citation_sentiment(text_lower, aliases)
                
            row = {
                "run_str": run_str,
                "sku": sku,
                "store_cited": store,
                "agent": agent,
                "query_type": query_type,
                "cited": cited,
                "citation_tier": citation_tier,
                "citation_score": citation_score,
                "citation_sentiment": sentiment,
                "timestamp": timestamp
            }
            new_rows.append(row)
            
    return new_rows, skipped_count

def load_agent_responses(results):
    """
    Load a list of agent-response dicts (produced by extract_agent_responses.py)
    into BigQuery table thesisusp.agent_responses and citations into thesisusp.agent_citations.
    """
    load_dotenv()

    bq_client = bigquery.Client()
    project_id = bq_client.project
    dataset_name = "thesisusp"
    dataset_ref = f"{project_id}.{dataset_name}"

    # Ensure dataset exists
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "southamerica-east1"
    bq_client.create_dataset(dataset, exists_ok=True)

    # 1. Load Responses
    table_id = f"{dataset_ref}.agent_responses"
    ensure_table(bq_client, table_id, AGENT_RESPONSES_SCHEMA)
    print(f"Ensured BigQuery table {table_id} exists.")

    existing_keys = get_existing_agent_keys(bq_client, table_id)
    print(f"Fetched {len(existing_keys)} existing agent-response keys from BigQuery.")

    new_rows, skipped = process_agent_responses(results, existing_keys)

    inserted = 0
    if new_rows:
        errors = bq_client.insert_rows_json(table_id, new_rows)
        if errors:
            print(f"Errors inserting agent_responses into BigQuery: {errors}")
        else:
            inserted = len(new_rows)

    print("\n=== AGENT RESPONSES LOAD STATISTICS ===")
    print(f"Inserted: {inserted:4d} | Skipped (duplicates): {skipped:4d}")
    print("========================================")

    # 2. Load Citations
    citations_table_id = f"{dataset_ref}.agent_citations"
    ensure_table(bq_client, citations_table_id, AGENT_CITATIONS_SCHEMA)
    print(f"Ensured BigQuery table {citations_table_id} exists.")

    existing_citation_keys = get_existing_citation_keys(bq_client, citations_table_id)
    print(f"Fetched {len(existing_citation_keys)} existing agent-citation keys from BigQuery.")

    new_citation_rows, cit_skipped = process_agent_citations(results, existing_citation_keys)

    cit_inserted = 0
    if new_citation_rows:
        errors = bq_client.insert_rows_json(citations_table_id, new_citation_rows)
        if errors:
            print(f"Errors inserting agent_citations into BigQuery: {errors}")
        else:
            cit_inserted = len(new_citation_rows)

    print("\n=== AGENT CITATIONS LOAD STATISTICS ===")
    print(f"Inserted: {cit_inserted:4d} | Skipped (duplicates): {cit_skipped:4d}")
    print("========================================")


if __name__ == "__main__":
    load_all()
