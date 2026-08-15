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

    # Query issues with dueDate
    query = """
    query {
      issues(first: 100) {
        nodes {
          identifier
          title
          dueDate
          projectMilestone {
            name
            targetDate
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
        res = response.json()
        issues = res.get("data", {}).get("issues", {}).get("nodes", [])
        
        has_due_date = [i for i in issues if i.get("dueDate")]
        print(f"Total issues fetched: {len(issues)}")
        print(f"Issues with dueDate: {len(has_due_date)}")
        for i in has_due_date[:5]:
            print(f"- {i['identifier']}: {i['title']} (Due: {i['dueDate']})")
            
        milestones_with_target = []
        for i in issues:
            ms = i.get("projectMilestone")
            if ms and ms.get("targetDate"):
                if ms not in milestones_with_target:
                    milestones_with_target.append(ms)
        print(f"Milestones with targetDate: {len(milestones_with_target)}")
        for m in milestones_with_target:
            print(f"- {m['name']} (Target: {m['targetDate']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
