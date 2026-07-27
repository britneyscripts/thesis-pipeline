import os
import json
import glob
from load_to_bigquery import load_agent_responses

def main():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "extractions", "agent-responses")
    
    # Find all JSON files
    pattern = os.path.join(base_dir, "**", "responses_*.json")
    files = glob.glob(pattern, recursive=True)
    
    all_results = []
    
    for file_path in files:
        if "log" in file_path:
            continue
        print(f"Loading {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                all_results.extend(data)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
    print(f"Total agent responses found: {len(all_results)}")
    
    if all_results:
        print("Loading to BigQuery...")
        load_agent_responses(all_results)
        print("Done!")

if __name__ == "__main__":
    main()
