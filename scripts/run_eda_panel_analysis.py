import os
import sys
import json
import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

# Allow imports from scripts/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_panel_data_from_local():
    """Load local JSON extractions for offline/local EDA calculation."""
    extractions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extractions")
    
    # 1. Load content extractions
    content_files = glob.glob(os.path.join(extractions_dir, "content", "*", "*.json"))
    content_rows = []
    for filepath in content_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                content_rows.append(data)
        except Exception:
            continue
            
    df_content = pd.DataFrame(content_rows) if content_rows else pd.DataFrame()
    
    # 2. Load CrUX extractions
    crux_files = glob.glob(os.path.join(extractions_dir, "crux", "*", "*.json"))
    crux_rows = []
    for filepath in crux_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                crux_rows.append(data)
        except Exception:
            continue
            
    df_crux = pd.DataFrame(crux_rows) if crux_rows else pd.DataFrame()

    # 3. Load PageSpeed extractions
    ps_files = glob.glob(os.path.join(extractions_dir, "pagespeed", "*", "*.json"))
    ps_rows = []
    for filepath in ps_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                ps_data = data.get("pagespeed", {})
                mobile = ps_data.get("mobile", {})
                metrics = mobile.get("metrics", {})
                row = {
                    "run_str": data.get("run_str"),
                    "sku": data.get("sku"),
                    "store": data.get("store"),
                    "mobile_score": mobile.get("score"),
                    "mobile_ttfb": metrics.get("TTFB"),
                    "mobile_lcp": metrics.get("LCP"),
                    "mobile_cls": metrics.get("CLS")
                }
                ps_rows.append(row)
        except Exception:
            continue
            
    df_ps = pd.DataFrame(ps_rows) if ps_rows else pd.DataFrame()

    # 4. Load Agent Responses & Citations
    resp_files = glob.glob(os.path.join(extractions_dir, "agent-responses", "*", "*", "*.json"))
    resp_rows = []
    for filepath in resp_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    resp_rows.extend(data)
                elif isinstance(data, dict):
                    resp_rows.append(data)
        except Exception:
            continue
            
    df_resp = pd.DataFrame(resp_rows) if resp_rows else pd.DataFrame()
    
    return df_content, df_crux, df_ps, df_resp

def load_panel_data_from_bigquery():
    """Load panel dataset directly from BigQuery thesisusp dataset."""
    from google.cloud import bigquery
    client = bigquery.Client()
    project = client.project
    
    q_content = f"SELECT * FROM `{project}.thesisusp.content_extractions`"
    q_crux = f"SELECT * FROM `{project}.thesisusp.crux_extractions`"
    q_ps = f"SELECT * FROM `{project}.thesisusp.pagespeed_extractions`"
    q_resp = f"SELECT * FROM `{project}.thesisusp.agent_responses`"
    
    df_content = client.query(q_content).to_dataframe()
    df_crux = client.query(q_crux).to_dataframe()
    df_ps = client.query(q_ps).to_dataframe()
    df_resp = client.query(q_resp).to_dataframe()
    
    return df_content, df_crux, df_ps, df_resp

def calculate_dispersion_stats(df, col_name, group_col=None):
    """Compute Mean, Median, Std, IQR, Min, Max, and Skewness for a numerical column."""
    if df.empty or col_name not in df.columns:
        return pd.DataFrame()
        
    def stats_fn(s):
        s_clean = s.dropna()
        if len(s_clean) == 0:
            return pd.Series({
                "count": 0, "mean": np.nan, "std": np.nan, "median": np.nan,
                "q1": np.nan, "q3": np.nan, "iqr": np.nan, "min": np.nan, "max": np.nan, "skew": np.nan
            })
        q1 = np.percentile(s_clean, 25)
        q3 = np.percentile(s_clean, 75)
        return pd.Series({
            "count": len(s_clean),
            "mean": np.mean(s_clean),
            "std": np.std(s_clean, ddof=1) if len(s_clean) > 1 else 0.0,
            "median": np.median(s_clean),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
            "min": np.min(s_clean),
            "max": np.max(s_clean),
            "skew": float(pd.Series(s_clean).skew()) if len(s_clean) > 2 else 0.0
        })

    if group_col and group_col in df.columns:
        res = df.groupby(group_col)[col_name].apply(stats_fn).unstack().reset_index()
    else:
        res = stats_fn(df[col_name]).to_frame().T
        res.insert(0, "metric", col_name)
        
    return res

def main():
    load_dotenv()
    print("=================================================================")
    print("📊 STARTING EXPLORATORY DATA ANALYSIS (EDA) ON PANEL DATA [EDA-01]")
    print("=================================================================")
    
    # Try BigQuery first, fallback to local extractions if BigQuery is unavailable
    try:
        print("\nAttempting connection to BigQuery 'thesisusp'...")
        df_content, df_crux, df_ps, df_resp = load_panel_data_from_bigquery()
        source_label = "BigQuery (thesisusp)"
    except Exception as e:
        print(f"Notice: BigQuery connection unavailable ({str(e)}). Falling back to local extractions...")
        df_content, df_crux, df_ps, df_resp = load_panel_data_from_local()
        source_label = "Local Extractions Mirror"

    print(f"\nData Source Active: {source_label}")
    print(f"  - Content extractions:   {len(df_content)} rows")
    print(f"  - CrUX extractions:      {len(df_crux)} rows")
    print(f"  - PageSpeed extractions: {len(df_ps)} rows")
    print(f"  - Agent responses:       {len(df_resp)} rows")
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extractions")
    os.makedirs(output_dir, exist_ok=True)
    
    # ---------------------------------------------------------------------------
    # 1. PageSpeed & Technical Health Dispersion Analysis
    # ---------------------------------------------------------------------------
    print("\n--- 1. TECHNICAL PERFORMANCE METRICS (Central Tendency & Dispersion) ---")
    
    metrics_summary = []
    if not df_ps.empty:
        for metric_col in ["mobile_score", "mobile_ttfb", "mobile_lcp", "mobile_cls"]:
            if metric_col in df_ps.columns:
                stats_df = calculate_dispersion_stats(df_ps, metric_col)
                metrics_summary.append(stats_df)
                
    if metrics_summary:
        df_tech_summary = pd.concat(metrics_summary, ignore_index=True)
        print(df_tech_summary.round(3).to_string(index=False))
        
        # Save to CSV
        csv_path = os.path.join(output_dir, "eda_technical_metrics_summary.csv")
        df_tech_summary.round(4).to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

    # ---------------------------------------------------------------------------
    # 2. D2C Shopify Benchmark vs. General Retail Channel Comparison
    # ---------------------------------------------------------------------------
    print("\n--- 2. SHOPIFY DNVB BENCHMARK VS. RETAIL CHANNELS COMPARISON ---")
    
    if not df_ps.empty and "store" in df_ps.columns:
        # Tag D2C Shopify Benchmark vs Retail
        shopify_dnvbs = ["Sallve", "Beyoung", "Creamy Skincare", "Principia"]
        df_ps["channel_group"] = df_ps["store"].apply(
            lambda s: "Shopify D2C Benchmark" if any(b.lower() in str(s).lower() for b in shopify_dnvbs) else "General Retail / Farma"
        )
        
        comp_ttfb = calculate_dispersion_stats(df_ps, "mobile_ttfb", group_col="channel_group")
        print("\nTTFB (ms) by Channel Group:")
        print(comp_ttfb.round(2).to_string(index=False))
        
        comp_score = calculate_dispersion_stats(df_ps, "mobile_score", group_col="channel_group")
        print("\nPageSpeed Mobile Score by Channel Group:")
        print(comp_score.round(2).to_string(index=False))
        
        # Plot Boxplot Comparison
        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")
        
        plt.subplot(1, 2, 1)
        sns.boxplot(data=df_ps, x="channel_group", y="mobile_score", palette="Set2")
        plt.title("PageSpeed Mobile Score (0-100)")
        plt.xlabel("")
        plt.ylabel("Score")
        
        plt.subplot(1, 2, 2)
        sns.boxplot(data=df_ps, x="channel_group", y="mobile_ttfb", palette="Set2")
        plt.title("Time to First Byte (TTFB ms)")
        plt.xlabel("")
        plt.ylabel("Latency (ms)")
        
        plt.tight_layout()
        plot_path = os.path.join(output_dir, "eda_channel_comparison_boxplots.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"\nGenerated Boxplot Visualization: {plot_path}")

    # ---------------------------------------------------------------------------
    # 3. Agent Response Latency & Zero-Citation Rate Analysis
    # ---------------------------------------------------------------------------
    print("\n--- 3. AGENT RESPONSE DISPERSION & LATENCY ---")
    if not df_resp.empty and "latency_ms" in df_resp.columns:
        df_agent_lat = calculate_dispersion_stats(df_resp, "latency_ms", group_col="agent" if "agent" in df_resp.columns else None)
        print(df_agent_lat.round(2).to_string(index=False))

    print("\n=================================================================")
    print("✅ EDA PANEL DATA ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    main()
