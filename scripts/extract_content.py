import os
import json
import datetime
import glob
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import save_json

def extract_schema(soup):
    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        if script.string:
            try:
                data = json.loads(script.string)
                schemas.append(data)
            except json.JSONDecodeError:
                pass
                
    fields_to_check = ["name", "price", "priceCurrency", "availability", "brand", "description", "aggregateRating", "image", "sku", "gtin", "offers"]
    found_fields = {field: False for field in fields_to_check}
    
    def search_dict(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in found_fields:
                    found_fields[k] = True
                if k == "offers" and isinstance(v, dict):
                    search_dict(v)
                elif isinstance(v, (dict, list)):
                    search_dict(v)
        elif isinstance(d, list):
            for item in d:
                search_dict(item)

    for schema in schemas:
        search_dict(schema)
        
    return {
        "raw_schemas": schemas,
        "fields_presence": found_fields
    }

def extract_basic_content(soup):
    title = soup.title.string if soup.title else None
    
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc:
        meta_desc = soup.find("meta", attrs={"property": "og:description"})
    meta_desc = meta_desc["content"] if meta_desc else None
    
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else None
    
    desc_container = soup.find(id="description") or soup.find(class_=lambda c: c and "description" in c.lower())
    if desc_container:
        words = len(desc_container.get_text(strip=True).split())
    else:
        words = len(soup.body.get_text(strip=True).split()) if soup.body else 0
        
    has_tech_specs_table = False
    tables = soup.find_all("table")
    if tables:
        has_tech_specs_table = True
        
    return {
        "title": title,
        "meta_description": meta_desc,
        "h1": h1_text,
        "description_word_count": words,
        "has_tech_specs_table": has_tech_specs_table
    }

def check_llms_txt(url):
    parsed = urlparse(url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
    try:
        resp = requests.get(llms_url, timeout=10)
        status_code = resp.status_code
        present = status_code == 200
        content = resp.text if present else None
        return {
            "present": present,
            "status_code": status_code,
            "content": content
        }
    except Exception as e:
        return {
            "present": False,
            "error": str(e)
        }

def check_robots_txt(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = requests.get(robots_url, timeout=10)
        return resp.status_code
    except Exception:
        return None


def get_previous_schema_fields(sku_dir, store_name):
    log_files = glob.glob(os.path.join(sku_dir, "*", "content_log_*.json"))
    if not log_files:
        return []
        
    log_files.sort(reverse=True)
    
    try:
        with open(log_files[0], "r") as f:
            prev_log = json.load(f)
            if store_name in prev_log:
                return prev_log[store_name].get("schema_fields_found", [])
    except Exception:
        pass
        
    return []

def main(run_str=None):
    if run_str is None:
        run_str = os.environ.get("RUN_STR") or datetime.datetime.now().strftime("%Y%m%d_%H%M")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    urls_file = os.path.join(base_dir, "urls.json")
    
    if not os.path.exists(urls_file):
        print(f"Error: {urls_file} not found.")
        return
        
    with open(urls_file, "r") as f:
        skus_data = json.load(f)
        
    extractions_dir = os.path.join(base_dir, "extractions")
    
    for sku, urls in skus_data.items():
        print(f"Processing SKU for Content: {sku}")
        
        sku_dir = os.path.join(extractions_dir, sku)
        today_dir = os.path.join(sku_dir, run_str)
        os.makedirs(today_dir, exist_ok=True)
        
        results = []
        logs = {}
        
        for store_info in urls:
            store_name = store_info["store"]
            url = store_info["url"]
            print(f"Extraindo Content para {store_name}...")
            
            res = {
                "store": store_name,
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "errors": []
            }
            
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                page_resp = requests.get(url, headers=headers, timeout=30)
                soup = BeautifulSoup(page_resp.content, "html.parser")
                
                res["schema"] = extract_schema(soup)
                res["basic_content"] = extract_basic_content(soup)
            except Exception as e:
                res["errors"].append(f"Failed to fetch page content: {str(e)}")
                res["schema"] = {"fields_presence": {}}
                
            res["llms_txt"] = check_llms_txt(url)
            import time
            time.sleep(1)  # Rate limiting backoff delay between requests
            results.append(res)
            
            schema_present = [k for k, v in res.get("schema", {}).get("fields_presence", {}).items() if v]
            prev_fields = get_previous_schema_fields(sku_dir, store_name)
            schema_change_detected = False
            for pf in prev_fields:
                if pf not in schema_present:
                    schema_change_detected = True
                    break
            
            logs[store_name] = {
                "status": "success" if not res.get("errors") else "error",
                "errors": res.get("errors", []),
                "schema_fields_found": schema_present,
                "schema_change_detected": schema_change_detected
            }
            
        save_json(results, f"{sku}/{run_str}/content_{run_str}.json")
        save_json(logs, f"{sku}/{run_str}/content_log_{run_str}.json")

if __name__ == "__main__":
    main()
