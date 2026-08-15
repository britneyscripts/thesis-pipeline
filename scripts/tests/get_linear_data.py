import os
import sys
import json
import requests
from dotenv import load_dotenv

def main():
    # Load .env file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"Error: .env not found at {env_path}")
        return

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY not found in .env.")
        return

    url = "https://api.linear.app/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }

    # GraphQL Query to pull projects and issues/tasks
    query = """
    query {
      viewer {
        name
      }
      projects {
        nodes {
          id
          name
          description
        }
      }
      issues {
        nodes {
          id
          identifier
          title
          description
          state {
            name
            type
          }
          project {
            name
          }
          projectMilestone {
            name
          }
          labels {
            nodes {
              name
            }
          }
        }
      }
    }
    """

    print("Fetching data from Linear API...")
    try:
        response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return
            
        res_json = response.json()
        if "errors" in res_json:
            print(f"GraphQL Errors: {json.dumps(res_json['errors'], indent=2)}")
            return
            
        data = res_json.get("data", {})
        viewer = data.get("viewer", {})
        projects = data.get("projects", {}).get("nodes", [])
        issues = data.get("issues", {}).get("nodes", [])
        
        print(f"\nConnected as: {viewer.get('name')}")
        
        print("\n=== PROJECTS ===")
        if not projects:
            print("No projects found.")
        for p in projects:
            print(f"- {p['name']}")
            if p.get('description'):
                print(f"  Description: {p['description']}")
                
        print("\n=== TASKS (ISSUES) ===")
        if not issues:
            print("No tasks found.")
        else:
            # Group issues by project and milestone
            hierarchy = {}
            for issue in issues:
                proj_name = issue.get("project", {}).get("name") or "No Project"
                milestone_name = issue.get("projectMilestone", {}).get("name") if issue.get("projectMilestone") else "No Milestone"
                
                hierarchy.setdefault(proj_name, {}).setdefault(milestone_name, []).append(issue)
                
            for proj, milestones in hierarchy.items():
                print(f"\nProject: {proj}")
                for milestone, ms_issues in milestones.items():
                    print(f"  Milestone: {milestone}")
                    for issue in ms_issues:
                        labels = [l['name'] for l in issue.get("labels", {}).get("nodes", [])]
                        label_str = f" [{', '.join(labels)}]" if labels else ""
                        print(f"    [{issue['identifier']}] {issue['title']} - State: {issue['state']['name']}{label_str}")
                    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
