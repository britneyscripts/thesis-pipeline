import os
import json
import datetime
import requests
import time
from urllib.parse import urlparse
from config import get_api_key, save_json

CRUX_API_KEY = get_api_key('CRUX_API_KEY')

METRIC_MAP = {
    "largest_contentful_paint": "LCP",
    "cumulative_layout_shift": "CLS",
    "interaction_to_next_paint": "INP",
    "first_contentful_paint": "FCP",
    "experimental_time_to_first_byte": "TTFB"
}

def format_date_obj(d_obj):
    if not d_obj:
        return ""
    year = d_obj.get("year")
    month = d_obj.get("month")
    day = d_obj.get("day")
    if year is not None and month is not None and day is not None:
        return f"{year:04d}-{month:02d}-{day:02d}"
    return ""

def format_collection_periods(raw_periods):
    collection_periods = []
    for period in raw_periods:
        collection_periods.append({
            "first": format_date_obj(period.get("firstDate")),
            "last": format_date_obj(period.get("lastDate"))
        })
    return collection_periods

def extract_metrics_timeseries(raw_metrics):
    metrics = {}
    for raw_k, new_k in METRIC_MAP.items():
        if raw_k in raw_metrics:
            m_data = raw_metrics[raw_k]
            p75s = m_data.get("percentilesTimeseries", {}).get("p75s", [])
            histogram = []
            for bin_item in m_data.get("histogramTimeseries", []):
                new_bin = {}
                if "start" in bin_item:
                    new_bin["start"] = bin_item["start"]
                if "end" in bin_item:
                    new_bin["end"] = bin_item["end"]
                new_bin["densities"] = bin_item.get("densities", [])
                histogram.append(new_bin)
            
            metrics[new_k] = {
                "p75s": p75s,
                "histogram": histogram
            }
        else:
            metrics[new_k] = {
                "p75s": [],
                "histogram": []
            }
    return metrics

def extract_device_fractions(overall_data):
    device_fractions = {
        "desktop": [],
        "phone": [],
        "tablet": []
    }
    if overall_data and "record" in overall_data and "metrics" in overall_data["record"]:
        ff_metric = overall_data["record"]["metrics"].get("form_factors", {})
        fraction_ts = ff_metric.get("fractionTimeseries", {})
        for device in ["desktop", "phone", "tablet"]:
            if device in fraction_ts:
                device_fractions[device] = fraction_ts[device].get("fractions", [])
    return device_fractions

def get_crux_history_data(url, api_key):
    if not api_key:
        return {"error": "CRUX_API_KEY not found"}
        
    endpoint = f"https://chromeuxreport.googleapis.com/v1/records:queryHistoryRecord?key={api_key}"
    
    def query_crux(url, form_factor, use_origin=False, include_form_factors=False):
        payload = {
            "metrics": [
                "largest_contentful_paint",
                "cumulative_layout_shift", 
                "interaction_to_next_paint",
                "first_contentful_paint",
                "experimental_time_to_first_byte"
            ]
        }
        if form_factor:
            payload["formFactor"] = form_factor
        if include_form_factors:
            payload["metrics"].append("form_factors")
            
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
                return query_crux(url, form_factor, use_origin=True, include_form_factors=include_form_factors)
            else:
                return {"error": f"API returned {resp.status_code}", "message": resp.text}, None
        except Exception as e:
            return {"error": str(e)}, None

    mobile_data, mobile_source = query_crux(url, "PHONE")
    desktop_data, desktop_source = query_crux(url, "DESKTOP")
    overall_data, overall_source = query_crux(url, None, include_form_factors=True)

    device_fractions = extract_device_fractions(overall_data)

    def process_factor_data(data, source):
        if not data:
            return {
                "source": None,
                "collection_periods": [],
                "metrics": {},
                "device_fractions": device_fractions,
                "error": "No response data"
            }
        if "error" in data:
            return {
                "source": source,
                "collection_periods": [],
                "metrics": {},
                "device_fractions": device_fractions,
                "error": data.get("error")
            }
            
        record = data.get("record", {})
        raw_periods = record.get("collectionPeriods", [])
        collection_periods = format_collection_periods(raw_periods)
        metrics = extract_metrics_timeseries(record.get("metrics", {}))
        
        return {
            "source": source,
            "collection_periods": collection_periods,
            "metrics": metrics,
            "device_fractions": device_fractions,
            "error": None
        }

    return {
        "mobile": process_factor_data(mobile_data, mobile_source),
        "desktop": process_factor_data(desktop_data, desktop_source)
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
        print(f"Processing SKU for CrUX History: {sku}")
        
        sku_dir = os.path.join(extractions_dir, sku, run_str)
        os.makedirs(sku_dir, exist_ok=True)
        
        results = []
        logs = {}
        
        for store_info in urls:
            store_name = store_info["store"]
            url = store_info["url"]
            print(f"Extraindo CrUX History para {store_name}...")
            
            start_time = time.time()
            crux_data = get_crux_history_data(url, CRUX_API_KEY)
            duration = time.time() - start_time
            
            results.append({
                "store": store_name,
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "crux_history": crux_data
            })
            
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
                for metric_name, m_data in metrics.items():
                    if m_data and m_data.get("p75s") and metric_name not in metrics_found:
                        metrics_found.append(metric_name)
            
            logs[store_name] = {
                "status": status,
                "errors": errors,
                "duration_seconds": round(duration, 2),
                "metrics_found": metrics_found
            }
            
        save_json(results, f"{sku}/{run_str}/crux_history_{run_str}.json")
        save_json(logs, f"{sku}/{run_str}/crux_history_log_{run_str}.json")

if __name__ == "__main__":
    main()
