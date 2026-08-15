import os
import sys
import json
import requests
from dotenv import load_dotenv

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY not found.")
        return

    url = "https://api.linear.app/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }

    # Query to fetch issues with parent details
    query = """
    query {
      issues(first: 50) {
        nodes {
          identifier
          title
          parent {
            id
            identifier
            title
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        res = response.json()
        
        # Print issues that have parents
        issues_with_parents = []
        for issue in res.get("data", {}).get("issues", {}).get("nodes", []):
            if issue.get("parent"):
                issues_with_parents.append(issue)
                
        if issues_with_parents:
            print("Found issues with parents:")
            print(json.dumps(issues_with_parents, indent=2, ensure_ascii=False))
        else:
            print("No issues with parents found in the first 50 issues.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
