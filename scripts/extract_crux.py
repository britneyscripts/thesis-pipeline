import os
import json
import datetime
import requests
import time
from urllib.parse import urlparse
from config import get_api_key, save_json

CRUX_API_KEY = get_api_key('CRUX_API_KEY')

def get_crux_data(url, api_key):
    if not api_key:
        return {"error": "CRUX_API_KEY not found"}
    
    endpoint = f"https://chromeuxreport.googleapis.com/v1/records:queryRecord?key={api_key}"
    
    def query_crux(url, form_factor, use_origin=False):
        payload = {
            "formFactor": form_factor,
            "metrics": ["largest_contentful_paint", "cumulative_layout_shift", "interaction_to_next_paint", "first_contentful_paint", "experimental_time_to_first_byte"]
        }
        if use_origin:
            parsed = urlparse(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            payload["origin"] = origin
        else:
            payload["url"] = url
            
        try:
            resp = requests.post(endpoint, json=payload, timeout=15)
            if resp.status_code == 200:
                return resp.json(), "origin" if use_origin else "url"
            elif resp.status_code == 404 and not use_origin:
                return query_crux(url, form_factor, use_origin=True)
            else:
                return {"error": f"API returned {resp.status_code}", "message": resp.text}, None
        except Exception as e:
            return {"error": str(e)}, None

    mobile_data, mobile_source = query_crux(url, "PHONE")
    desktop_data, desktop_source = query_crux(url, "DESKTOP")

    def extract_metrics(data):
        metrics = {}
        if data and "record" in data and "metrics" in data["record"]:
            raw_metrics = data["record"]["metrics"]
            metric_map = {
                "largest_contentful_paint": "LCP",
                "cumulative_layout_shift": "CLS",
                "interaction_to_next_paint": "INP",
                "first_contentful_paint": "FCP",
                "experimental_time_to_first_byte": "TTFB"
            }
            for raw_k, new_k in metric_map.items():
                if raw_k in raw_metrics and "percentiles" in raw_metrics[raw_k]:
                    metrics[new_k] = raw_metrics[raw_k]["percentiles"].get("p75")
        return metrics

    return {
        "mobile": {
            "source": mobile_source,
            "metrics": extract_metrics(mobile_data),
            "error": mobile_data.get("error") if mobile_data and "error" in mobile_data else None
        },
        "desktop": {
            "source": desktop_source,
            "metrics": extract_metrics(desktop_data),
            "error": desktop_data.get("error") if desktop_data and "error" in desktop_data else None
        }
    }

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
        print(f"Processing SKU for CrUX: {sku}")
        
        sku_dir = os.path.join(extractions_dir, sku, run_str)
        os.makedirs(sku_dir, exist_ok=True)
        
        results = []
        logs = {}
        
        for store_info in urls:
            store_name = store_info["store"]
            url = store_info["url"]
            print(f"Extraindo CrUX para {store_name}...")
            
            start_time = time.time()
            crux_data = get_crux_data(url, CRUX_API_KEY)
            duration = time.time() - start_time
            
            results.append({
                "store": store_name,
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "crux": crux_data
            })
            
            # Log preparation
            errors = []
            status = "success"
            
            if crux_data.get("error"):
                errors.append(crux_data["error"])
                status = "error"
            
            mobile_err = crux_data.get("mobile", {}).get("error")
            desktop_err = crux_data.get("desktop", {}).get("error")
            
            if mobile_err:
                errors.append(f"Mobile error: {mobile_err}")
            if desktop_err:
                errors.append(f"Desktop error: {desktop_err}")
            
            if mobile_err and desktop_err:
                status = "error"
                
            metrics_found = []
            for factor in ["mobile", "desktop"]:
                metrics = crux_data.get(factor, {}).get("metrics", {})
                for metric_name, val in metrics.items():
                    if val is not None and metric_name not in metrics_found:
                        metrics_found.append(metric_name)
            
            logs[store_name] = {
                "status": status,
                "errors": errors,
                "duration_seconds": round(duration, 2),
                "metrics_found": metrics_found
            }
            
        save_json(results, f"{sku}/{run_str}/crux_{run_str}.json")
        save_json(logs, f"{sku}/{run_str}/crux_log_{run_str}.json")

if __name__ == "__main__":
    main()
