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

    # Query to test project milestones details
    query = """
    query {
      projects {
        nodes {
          name
          projectMilestones {
            nodes {
              id
              name
              targetDate
              createdAt
            }
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
