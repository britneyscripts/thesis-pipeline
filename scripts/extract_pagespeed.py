import os
import json
import datetime
import requests
import time
from config import get_api_key, save_json

PAGESPEED_API_KEY = get_api_key('PAGESPEED_API_KEY')

def get_pagespeed_data(url, api_key):
    if not api_key:
        return {"error": "PAGESPEED_API_KEY not found"}
        
    endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
    
    def query_psi(strategy):
        try:
            resp = requests.get(f"{endpoint}&strategy={strategy}", timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
                metrics = {}
                if strategy == "mobile" and "loadingExperience" in data and "metrics" in data["loadingExperience"]:
                    metric_map = {
                        "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
                        "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
                        "INTERACTION_TO_NEXT_PAINT": "INP",
                        "FIRST_CONTENTFUL_PAINT_MS": "FCP",
                        "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB"
                    }
                    for m_key, m_val in data["loadingExperience"]["metrics"].items():
                        if m_key in metric_map:
                            metrics[metric_map[m_key]] = m_val.get("percentile")
                return {"score": score * 100 if score is not None else None, "metrics": metrics}
            else:
                return {"error": f"API returned {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    mobile_data = query_psi("mobile")
    desktop_data = query_psi("desktop")
    
    return {
        "mobile": mobile_data,
        "desktop": {
            "score": desktop_data.get("score"),
            "error": desktop_data.get("error") if "error" in desktop_data else None
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
        print(f"Processing SKU for PageSpeed: {sku}")
        
        sku_dir = os.path.join(extractions_dir, sku, run_str)
        os.makedirs(sku_dir, exist_ok=True)
        
        results = []
        logs = {}
        
        for store_info in urls:
            store_name = store_info["store"]
            url = store_info["url"]
            print(f"Extraindo PageSpeed para {store_name}...")
            
            start_time = time.time()
            psi_data = get_pagespeed_data(url, PAGESPEED_API_KEY)
            duration = time.time() - start_time
            
            results.append({
                "store": store_name,
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "pagespeed": psi_data
            })
            
            # Log preparation following the same strict pattern as extract_content
            errors = []
            status = "success"
            
            if psi_data.get("error"):
                errors.append(psi_data["error"])
                status = "error"
                
            mobile_err = psi_data.get("mobile", {}).get("error")
            desktop_err = psi_data.get("desktop", {}).get("error")
            
            if mobile_err:
                errors.append(f"Mobile error: {mobile_err}")
            if desktop_err:
                errors.append(f"Desktop error: {desktop_err}")
                
            if mobile_err and desktop_err:
                status = "error"
                
            metrics_found = []
            # Check mobile metrics
            mobile_metrics = psi_data.get("mobile", {}).get("metrics", {})
            for metric_name, val in mobile_metrics.items():
                if val is not None:
                    metrics_found.append(metric_name)
                    
            logs[store_name] = {
                "status": status,
                "errors": errors,
                "duration_seconds": round(duration, 2),
                "metrics_found": metrics_found
            }
            
        save_json(results, f"{sku}/{run_str}/pagespeed_{run_str}.json")
        save_json(logs, f"{sku}/{run_str}/pagespeed_log_{run_str}.json")

if __name__ == "__main__":
    main()
