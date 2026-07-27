import os
import sys
import time
import datetime
from dotenv import load_dotenv

# Allow running from project root or scripts/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_api_key, save_json

# ---------------------------------------------------------------------------
# Agent configuration
# ---------------------------------------------------------------------------

AGENTS = {
    "gemini-2.5-flash": {
        "model": "gemini-2.5-flash",
        "client": "google"
    },
    "gemini-2.5-pro": {
        "model": "gemini-2.5-pro",
        "client": "google"
    },
    "gemini-2.5-flash-grounded": {
        "model": "gemini-2.5-flash",
        "client": "google_grounded"
    },
    "gemini-2.5-pro-grounded": {
        "model": "gemini-2.5-pro",
        "client": "google_grounded"
    }
}

# ---------------------------------------------------------------------------
# Query definitions — 3 types × 7 products = 21 queries
# ---------------------------------------------------------------------------

QUERIES = [
    # --- NEW 3-TIER UNBIASED SKINCARE PROMPTS ---
    # Level 1 — Problem-Centric / Zero-Knowledge (Baseline Control)
    {"query": "Tenho pele mista a oleosa com manchas e quero comprar online no Brasil um serum facial de Vitamina C com acao antioxidante. Quais marcas voce recomenda e em quais e-commerces ou farmacias posso comprar", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_1_control"},
    {"query": "Qual o melhor serum antioxidante com vitamina C para pele mista com manchas vendida em e-commerce no Brasil", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_1_control"},

    # Level 2 — Channel Comparison (Natural Language: Direct Brand Site vs Pharmacy E-commerce)
    {"query": "Quais sao as melhores opcoes de serum de Vitamina C para comprar direto no site da marca versus em grandes farmacias online no Brasil", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_2_channel"},
    {"query": "Vale mais a pena comprar serum antioxidante de Vitamina C direto do site oficial da marca ou em e-commerce de farmacia no Brasil para conseguir preco bom e cupom", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_2_channel"},

    # Level 3 — Multi-Constraint Attributes (Unbiased Attribute-Based Search: Concentration, Texture, Price & Shipping)
    {"query": "Qual e o melhor preco online hoje para um serum facial de Vitamina C com concentracao entre 10% e 15% e textura leve para pele oleosa, e em quais lojas online confiaveis eu encontro no Brasil", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_3_attributes"},
    {"query": "Qual o melhor serum antioxidante de Vitamina C para pele mista considerando preco, frete e cupom de desconto em e-commerces no Brasil", "product": "vitamina-c-hero-cluster", "category": "skincare", "query_type": "level_3_attributes"},

    # --- LEGACY COEXISTENCE QUERIES (TRANSITION PERIOD) ---
    # PRODUCT EXACT
    {"query": "Natura Chronos Serum Antioxidante Vitamina C 15ml onde comprar", "product": "natura-chronos", "category": "skincare", "query_type": "product_exact"},
    {"query": "La Roche-Posay Pure Vitamin C12 Serum 30ml preco Brasil", "product": "la-roche-posay-vitamin-c12", "category": "skincare", "query_type": "product_exact"},
    {"query": "Neutrogena Hydro Boost Water Gel 50g preco onde comprar", "product": "neutrogena-hydro-boost", "category": "skincare", "query_type": "product_exact"},
    {"query": "Boticario Botik Serum Vitamina C 10% 30ml onde comprar Brasil", "product": "boticario-botik", "category": "skincare", "query_type": "product_exact"},
    {"query": "Sallve Antioxidante Hidratante Vitamina C 35g onde comprar Brasil", "product": "sallve-antioxidante-hidratante-35g", "category": "skincare", "query_type": "product_exact"},
    {"query": "Creamy Skincare Vitamina C Serum 30g onde comprar Brasil", "product": "creamy-skincare-vitamina-c-serum-30g", "category": "skincare", "query_type": "product_exact"},
    {"query": "Principia VC-10 Serum Vitamina C 10% 30ml onde comprar Brasil", "product": "principia-serum-vitamina-c-10-vc-10-30ml", "category": "skincare", "query_type": "product_exact"},
    {"query": "Beyoung Vita C 18 Serum 30ml onde comprar Brasil", "product": "beyoung-booster-antiaging-serum-30ml", "category": "skincare", "query_type": "product_exact"},
    {"query": "ADCOS Vitamina C 15 Oil Control 30ml onde comprar Brasil", "product": "adcos-derma-complex-vitamina-c-20-30ml", "category": "skincare", "query_type": "product_exact"},
    {"query": "Dermage Improve C 20 Biotic Serum 30g onde comprar Brasil", "product": "dermage-improve-c-20-serum-antioxidante-30ml", "category": "skincare", "query_type": "product_exact"},

    # BRAND / CHANNEL DISCOVERY
    {"query": "Quais sao as melhores marcas brasileiras D2C de serum vitamina C para pele oleosa", "product": "natura-chronos", "category": "skincare", "query_type": "brand"},
    {"query": "La Roche-Posay serum vitamina C onde encontrar Brasil", "product": "la-roche-posay-vitamin-c12", "category": "skincare", "query_type": "brand"},
    {"query": "Neutrogena Hydro Boost hidratante facial onde comprar", "product": "neutrogena-hydro-boost", "category": "skincare", "query_type": "brand"},
    {"query": "O Boticario Botik serum vitamina C onde comprar", "product": "boticario-botik", "category": "skincare", "query_type": "brand"},

    # GENERIC
    {"query": "melhor hidratante facial leve para pele oleosa", "product": "neutrogena-hydro-boost", "category": "skincare", "query_type": "generic"},
    {"query": "melhor serum vitamina C custo beneficio farmacia Brasil", "product": "boticario-botik", "category": "skincare", "query_type": "generic"},
]

SYSTEM_PROMPT = (
    "You are a helpful shopping assistant. Answer the user's question about products available "
    "in Brazil. Be specific about store names, prices if known, and availability. Answer in Portuguese."
)

# ---------------------------------------------------------------------------
# API client helpers
# ---------------------------------------------------------------------------

def call_claude(model: str, query: str, api_key: str) -> str:
    """Call the Anthropic Claude API and return the response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}]
    )
    return message.content[0].text


def call_gemini(model: str, query: str, api_key: str = None) -> tuple:
    """Call Gemini via Vertex AI using Application Default Credentials with temperature=0.0."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True,
        project="thesisusp",
        location="us-central1"
    )
    config = types.GenerateContentConfig(
        temperature=0.0
    )
    response = client.models.generate_content(
        model=model,
        contents=f"{SYSTEM_PROMPT}\n\n{query}",
        config=config
    )
    return response.text, []


def call_gemini_grounded(model: str, query: str, api_key: str = None) -> tuple:
    """Call Gemini via Vertex AI with Google Search Grounding enabled and temperature=0.0."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True,
        project="thesisusp",
        location="us-central1"
    )
    config = types.GenerateContentConfig(
        temperature=0.0,
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
    response = client.models.generate_content(
        model=model,
        contents=f"{SYSTEM_PROMPT}\n\n{query}",
        config=config
    )
    
    # Extract grounding URIs / links if present
    grounding_uris = []
    try:
        if response.candidates and response.candidates[0].grounding_metadata:
            metadata = response.candidates[0].grounding_metadata
            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web and hasattr(chunk.web, 'uri'):
                        grounding_uris.append(chunk.web.uri)
    except Exception as e:
        print(f"Notice: Could not parse grounding_metadata URIs: {str(e)}")

    return response.text, grounding_uris


def call_agent(agent_name: str, model: str, query: str, api_key: str) -> tuple:
    """Dispatch to the correct API client based on agent name."""
    client_type = AGENTS[agent_name]["client"]

    if client_type == "anthropic":
        return call_claude(model, query, api_key), []
    elif client_type == "google":
        return call_gemini(model, query, api_key)
    elif client_type == "google_grounded":
        return call_gemini_grounded(model, query, api_key)
    else:
        raise ValueError(f"Unsupported client type: {client_type}")

# ---------------------------------------------------------------------------
# API key loader
# ---------------------------------------------------------------------------

# Agents that authenticate via API key — Gemini uses ADC (no key needed)
API_KEY_NAMES = {
    "claude": "ANTHROPIC_API_KEY",
    # gemini: authenticated via Application Default Credentials (Vertex AI)
}

# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def query_agent(agent_name: str, agent_cfg: dict, query_info: dict, run_str: str, api_key: str) -> dict:
    """
    Query a single agent for a single query.

    Returns a result dict matching the output schema.
    """
    primary_model = agent_cfg["model"]

    base = {
        "run_str": run_str,
        "agent": agent_name,
        "model_used": primary_model,
        "fallback_used": False,
        "query_type": query_info["query_type"],
        "product": query_info["product"],
        "category": query_info["category"],
        "query": query_info["query"],
        "response_text": None,
        "grounding_uris": [],
        "response_length": 0,
        "latency_ms": 0,
        "error": None,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # --- Primary model attempt ---
    try:
        t0 = time.monotonic()
        text, uris = call_agent(agent_name, primary_model, query_info["query"], api_key)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        base["response_text"] = text
        base["grounding_uris"] = uris
        base["response_length"] = len(text) if text else 0
        base["latency_ms"] = elapsed_ms
        print(f"  [{agent_name}/{primary_model}] OK — {elapsed_ms} ms, {len(text) if text else 0} chars, {len(uris)} URIs")
        return base

    except Exception as e:
        base["error"] = str(e)
        print(f"  [{agent_name}/{primary_model}] ERROR: {e}")
        return base


# ---------------------------------------------------------------------------
# GCS / BigQuery save helpers
# ---------------------------------------------------------------------------

def save_responses(all_results: list, run_str: str) -> None:
    """
    Save all responses and a log summary to GCS (or local fallback).

    GCS paths:
      agent-responses/{product}/{run_str}/responses_{run_str}.json
      agent-responses/{product}/{run_str}/responses_log_{run_str}.json
    """
    # Group results by product
    by_product: dict = {}
    for row in all_results:
        product = row["product"]
        by_product.setdefault(product, []).append(row)

    for product, rows in by_product.items():
        blob_path = f"agent-responses/{product}/{run_str}/responses_{run_str}.json"
        save_json(rows, blob_path)
        print(f"Saved responses for product '{product}' → {blob_path}")

        # Build a concise log entry per (agent, query_type)
        log_entries = {}
        for row in rows:
            log_key = f"{row['agent']}__{row['query_type']}"
            log_entries[log_key] = {
                "agent": row["agent"],
                "model_used": row["model_used"],
                "fallback_used": row["fallback_used"],
                "query_type": row["query_type"],
                "status": "error" if row["error"] else "success",
                "error": row["error"],
                "latency_ms": row["latency_ms"],
                "response_length": row["response_length"],
                "timestamp": row["timestamp"],
            }

        log_blob_path = f"agent-responses/{product}/{run_str}/responses_log_{run_str}.json"
        save_json(log_entries, log_blob_path)
        print(f"Saved log for product '{product}' → {log_blob_path}")


def load_to_bigquery(all_results: list) -> None:
    """Load agent responses into BigQuery via load_to_bigquery.load_agent_responses()."""
    try:
        from load_to_bigquery import load_agent_responses
        load_agent_responses(all_results)
    except ImportError as e:
        print(f"Warning: Could not import load_to_bigquery: {e}")
    except Exception as e:
        print(f"Warning: BigQuery load failed: {e}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(run_str=None):
    load_dotenv()

    if run_str is None:
        run_str = os.environ.get("RUN_STR") or datetime.datetime.now().strftime("%Y%m%d_%H%M")

    print(f"=== extract_agent_responses — run_str={run_str} ===")
    print(f"Agents: {list(AGENTS.keys())}")
    print(f"Queries: {len(QUERIES)}")
    print(f"Total API calls: {len(AGENTS) * len(QUERIES)}\n")

    # Load API keys for agents that need them; ADC-based agents are always active
    api_keys = {}
    active_agents = {}
    for agent_name in AGENTS:
        if agent_name in API_KEY_NAMES:
            key_name = API_KEY_NAMES[agent_name]
            key = get_api_key(key_name)
            if key:
                api_keys[agent_name] = key
                active_agents[agent_name] = AGENTS[agent_name]
            else:
                print(f"WARNING: {key_name} not found — skipping agent '{agent_name}'")
        else:
            # No API key needed (e.g. Gemini via Vertex AI ADC)
            api_keys[agent_name] = None
            active_agents[agent_name] = AGENTS[agent_name]

    if not active_agents:
        print("ERROR: No active agents. Aborting.")
        return

    all_results = []

    for agent_name, agent_cfg in active_agents.items():
        print(f"\n--- Agent: {agent_name} (model={agent_cfg['model']}) ---")
        for i, query_info in enumerate(QUERIES, 1):
            print(f"  Query {i}/{len(QUERIES)}: [{query_info['query_type']}] {query_info['query'][:60]}...")
            result = query_agent(agent_name, agent_cfg, query_info, run_str, api_keys[agent_name])
            # Refresh timestamp to the moment the call completed
            result["timestamp"] = datetime.datetime.now().isoformat()
            all_results.append(result)

    # --- Persist results ---
    print(f"\n=== Saving {len(all_results)} results ===")
    save_responses(all_results, run_str)

    # --- Load to BigQuery ---
    print("\n=== Loading to BigQuery ===")
    load_to_bigquery(all_results)

    # --- Summary ---
    success_count = sum(1 for r in all_results if not r["error"])
    error_count = sum(1 for r in all_results if r["error"])
    fallback_count = sum(1 for r in all_results if r["fallback_used"])
    print("\n=== AGENT RESPONSE EXTRACTION STATISTICS ===")
    print(f"Total results:    {len(all_results):4d}")
    print(f"Successful:       {success_count:4d}")
    print(f"Errors:           {error_count:4d}")
    print(f"Fallbacks used:   {fallback_count:4d}")
    print("============================================")


if __name__ == "__main__":
    main()
