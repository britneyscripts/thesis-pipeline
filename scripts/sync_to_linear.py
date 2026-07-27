import os
import re
import sys
import json
import requests
from dotenv import load_dotenv

LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"

def parse_linear_backlog_md(filepath):
    """Parse linear_backlog.md into Milestones (Epics), Tasks (Issues), and Subtasks."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by Epic headers
    epic_sections = re.split(r'###\ 📌\ EPIC\ \d+:\ ', content)
    
    milestones = []
    
    for section in epic_sections[1:]:
        lines = section.strip().split("\n")
        epic_name = lines[0].strip()
        
        # Parse tasks within epic
        task_blocks = re.split(r'####\ `\[', section)
        tasks = []
        
        for tb in task_blocks[1:]:
            tb_lines = ("`[" + tb).strip().split("\n")
            task_title_line = tb_lines[0].strip()
            
            # Extract Task ID & Name e.g. `[EDA-01]` Title
            match = re.search(r'`\[(.*?)\]` (.*)', task_title_line)
            if match:
                task_id = match.group(1)
                task_name = match.group(2)
            else:
                task_id = "TASK"
                task_name = task_title_line
                
            priority = "High"
            description = ""
            subtasks = []
            deliverable = ""
            
            in_subtasks = False
            for line in tb_lines[1:]:
                line_str = line.strip()
                if line_str.startswith("* **Priority**:") or "* **Priority**:" in line_str:
                    if "High" in line_str:
                        priority = "High"
                    elif "Medium" in line_str:
                        priority = "Medium"
                    else:
                        priority = "Low"
                elif line_str.startswith("* **Description**:") or "* **Description**:" in line_str:
                    description = line_str.replace("* **Description**:", "").strip()
                elif line_str.startswith("* **Subtasks**:") or "* **Subtasks**:" in line_str:
                    in_subtasks = True
                elif line_str.startswith("* **Deliverable**:") or "* **Deliverable**:" in line_str:
                    deliverable = line_str.replace("* **Deliverable**:", "").strip()
                    in_subtasks = False
                elif in_subtasks and line_str.startswith("- ["):
                    is_completed = line_str.startswith("- [x]")
                    subtask_text = line_str[5:].strip()
                    subtasks.append({"text": subtask_text, "completed": is_completed})

            tasks.append({
                "id": task_id,
                "title": f"[{task_id}] {task_name}",
                "priority": priority,
                "description": description,
                "deliverable": deliverable,
                "subtasks": subtasks
            })
            
        milestones.append({
            "epic_name": epic_name,
            "tasks": tasks
        })
        
    return milestones

def execute_linear_query(api_key, query, variables=None):
    """Send GraphQL query/mutation to Linear API."""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
        
    resp = requests.post(LINEAR_GRAPHQL_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Linear API error ({resp.status_code}): {resp.text}")
    data = resp.json()
    if "errors" in data:
        raise Exception(f"Linear GraphQL error: {data['errors']}")
    return data.get("data", {})

def main():
    load_dotenv()
    api_key = os.getenv("LINEAR_API_KEY")
    
    if not api_key:
        print("=================================================================")
        print("🔑 LINEAR API KEY REQUIRED")
        print("=================================================================")
        print("Please set LINEAR_API_KEY in your .env file or environment.")
        print("Generate your key at: https://linear.app/settings/account/security/api")
        print("=================================================================")
        sys.exit(1)

    backlog_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "linear_backlog.md")
    print(f"Parsing backlog from: {backlog_file}")
    milestones = parse_linear_backlog_md(backlog_file)
    
    # 1. Fetch Linear Team ID
    team_query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    team_data = execute_linear_query(api_key, team_query)
    teams = team_data.get("teams", {}).get("nodes", [])
    if not teams:
        print("Error: No Linear teams found for this API key.")
        sys.exit(1)
        
    team = teams[0]
    team_id = team["id"]
    print(f"Connected to Linear Team: {team['name']} (Key: {team['key']}, ID: {team_id})")
    
    # 2. Get or Create Linear Initiative: "USP MBA (The Foundation)"
    initiative_name = "USP MBA (The Foundation)"
    initiative_query = """
    query {
      initiatives {
        nodes {
          id
          name
        }
      }
    }
    """
    initiative_id = None
    try:
        init_data = execute_linear_query(api_key, initiative_query)
        existing_inits = init_data.get("initiatives", {}).get("nodes", [])
        for i in existing_inits:
            if "foundation" in i["name"].lower() or "usp mba" in i["name"].lower():
                initiative_id = i["id"]
                print(f"Found existing Initiative: '{i['name']}' (ID: {initiative_id})")
                break
    except Exception:
        pass
        
    # 3. Get or Create Linear Project: "MBA USP"
    project_name = "MBA USP"
    project_query = """
    query {
      projects {
        nodes {
          id
          name
        }
      }
    }
    """
    project_data = execute_linear_query(api_key, project_query)
    existing_projects = project_data.get("projects", {}).get("nodes", [])
    
    project_id = None
    for p in existing_projects:
        if p["name"].strip().lower() == project_name.lower():
            project_id = p["id"]
            print(f"Found existing Linear Project: '{p['name']}' (ID: {project_id})")
            break
            
    if not project_id:
        print(f"Creating new Linear Project: '{project_name}'...")
        create_project_mutation = """
        mutation CreateProject($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project {
              id
              name
            }
          }
        }
        """
        p_input = {
            "name": project_name,
            "teamIds": [team_id],
            "description": "MBA USP thesis pipeline, GEE panel logistic regression, and ARS scoring framework."
        }
        if initiative_id:
            p_input["initiativeId"] = initiative_id
            
        p_res = execute_linear_query(api_key, create_project_mutation, {"input": p_input})
        project_id = p_res.get("projectCreate", {}).get("project", {}).get("id")
        print(f"Created Linear Project: '{project_name}' (ID: {project_id})")
        
    # Priority mapping for Linear GraphQL (0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low)
    priority_map = {"High": 2, "Medium": 3, "Low": 4}
    
    created_count = 0
    for milestone in milestones:
        epic_name = milestone["epic_name"]
        print(f"\n📌 Processing Milestone/Epic: {epic_name}")
        
        # 3. Create Project Milestone
        create_milestone_mutation = """
        mutation CreateMilestone($input: ProjectMilestoneCreateInput!) {
          projectMilestoneCreate(input: $input) {
            success
            projectMilestone {
              id
              name
            }
          }
        }
        """
        milestone_id = None
        try:
            m_res = execute_linear_query(api_key, create_milestone_mutation, {
                "input": {
                    "projectId": project_id,
                    "name": epic_name
                }
            })
            milestone_id = m_res.get("projectMilestoneCreate", {}).get("projectMilestone", {}).get("id")
            print(f"  📌 Created Milestone: '{epic_name}' (ID: {milestone_id})")
        except Exception as e:
            print(f"  Notice (Milestone creation): {str(e)}")

        for task in milestone["tasks"]:
            # Format markdown description including subtask checkboxes
            desc_markdown = f"{task['description']}\n\n### Subtasks:\n"
            for st in task["subtasks"]:
                chk = "[x]" if st["completed"] else "[ ]"
                desc_markdown += f"- {chk} {st['text']}\n"
                
            if task["deliverable"]:
                desc_markdown += f"\n**Deliverable**: {task['deliverable']}\n"
                
            issue_create_mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id
                  title
                  url
                }
              }
            }
            """
            
            variables = {
                "input": {
                    "teamId": team_id,
                    "projectId": project_id,
                    "title": task["title"],
                    "description": desc_markdown,
                    "priority": priority_map.get(task["priority"], 3)
                }
            }
            if milestone_id:
                variables["input"]["projectMilestoneId"] = milestone_id
                
            try:
                res = execute_linear_query(api_key, issue_create_mutation, variables)
                issue = res.get("issueCreate", {}).get("issue", {})
                print(f"  ✅ Created Issue: {issue.get('title')} ({issue.get('url')})")
                created_count += 1
            except Exception as e:
                print(f"  ❌ Error creating issue {task['title']}: {str(e)}")

    print(f"\n=================================================================")
    print(f"🎉 LINEAR SYNC COMPLETED: {created_count} Issues successfully created/synced!")
    print("=================================================================")

if __name__ == "__main__":
    main()
