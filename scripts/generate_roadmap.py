import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_linear_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        raise FileNotFoundError(f".env file not found at {env_path}")
        
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        raise ValueError("LINEAR_API_KEY not found in .env file.")
        
    url = "https://api.linear.app/graphql"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    
    # GraphQL Query pulling viewer, projects, milestones, and issues with parent/child relationships
    query = """
    query {
      viewer {
        name
        avatarUrl
      }
      projects(first: 50) {
        nodes {
          id
          name
          description
          projectMilestones(first: 50) {
            nodes {
              id
              name
              targetDate
              createdAt
            }
          }
        }
      }
      issues(first: 250) {
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
            id
            name
          }
          projectMilestone {
            id
            name
          }
          parent {
            id
            identifier
          }
          children(first: 50) {
            nodes {
              id
              identifier
              title
              description
              state {
                name
                type
              }
              labels {
                nodes {
                  name
                }
              }
            }
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
    
    response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP Error {response.status_code}: {response.text}")
        
    res_json = response.json()
    if "errors" in res_json:
        raise RuntimeError(f"GraphQL Errors: {json.dumps(res_json['errors'], indent=2)}")
        
    return res_json.get("data", {})

def process_data(data):
    viewer = data.get("viewer", {})
    raw_projects = data.get("projects", {}).get("nodes", [])
    raw_issues = data.get("issues", {}).get("nodes", [])
    
    projects_map = {}
    
    # Initialize projects and milestones
    for p in raw_projects:
        p_id = p["id"]
        milestones_list = []
        
        raw_milestones = p.get("projectMilestones", {}).get("nodes", [])
        sorted_milestones = sorted(
            raw_milestones, 
            key=lambda x: x.get("createdAt") or ""
        )
        
        for ms in sorted_milestones:
            milestones_list.append({
                "id": ms["id"],
                "name": ms["name"],
                "targetDate": ms.get("targetDate"),
                "issues": []
            })
            
        projects_map[p_id] = {
            "name": p["name"],
            "description": p.get("description") or "",
            "milestones": milestones_list,
            "no_milestone_issues": []
        }
        
    # Categorize issues, keeping parent/child hierarchy.
    # To prevent duplicates, we only list top-level issues (parent is None) at the milestone level.
    # We embed child subtasks directly inside the parent issue.
    for issue in raw_issues:
        proj = issue.get("project")
        if not proj:
            continue
            
        proj_id = proj["id"]
        if proj_id not in projects_map:
            projects_map[proj_id] = {
                "name": proj["name"],
                "description": "",
                "milestones": [],
                "no_milestone_issues": []
            }
            
        # If this issue is a subtask (it has a parent), we SKIP adding it at the top-level.
        # It will be rendered nested under its parent task instead.
        if issue.get("parent"):
            continue
            
        milestone = issue.get("projectMilestone")
        
        # Build children list (subtasks)
        subtasks = []
        raw_children = issue.get("children", {}).get("nodes", [])
        # Sort subtasks by identifier/name
        raw_children_sorted = sorted(raw_children, key=lambda x: x["identifier"])
        for child in raw_children_sorted:
            subtasks.append({
                "id": child["id"],
                "identifier": child["identifier"],
                "title": child["title"],
                "description": child.get("description") or "",
                "state_name": child["state"]["name"],
                "state_type": child["state"]["type"],
                "labels": [l["name"] for l in child.get("labels", {}).get("nodes", [])]
            })
            
        # Parent issue details
        issue_data = {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue.get("description") or "",
            "state_name": issue["state"]["name"],
            "state_type": issue["state"]["type"],
            "labels": [l["name"] for l in issue.get("labels", {}).get("nodes", [])],
            "subtasks": subtasks
        }
        
        if milestone:
            ms_id = milestone["id"]
            ms_found = False
            for ms in projects_map[proj_id]["milestones"]:
                if ms["id"] == ms_id:
                    ms["issues"].append(issue_data)
                    ms_found = True
                    break
            
            if not ms_found:
                projects_map[proj_id]["milestones"].append({
                    "id": ms_id,
                    "name": milestone["name"],
                    "targetDate": None,
                    "issues": [issue_data]
                })
        else:
            projects_map[proj_id]["no_milestone_issues"].append(issue_data)

    # For each project, compute metrics & sort issues
    processed_projects = []
    for p_id, p_info in projects_map.items():
        if p_info["no_milestone_issues"]:
            p_info["milestones"].append({
                "id": "no-milestone",
                "name": "Outras Atividades & TCC",
                "targetDate": None,
                "issues": p_info["no_milestone_issues"]
            })
            
        total_project_tasks = 0
        completed_project_tasks = 0
        
        active_milestones = []
        for ms in p_info["milestones"]:
            # Sort top-level milestone tasks alphabetically/numerically by title to follow coursework sequence
            ms["issues"] = sorted(ms["issues"], key=lambda x: x["title"])
            
            total_ms = 0
            completed_ms = 0
            
            for issue in ms["issues"]:
                # If a parent issue has subtasks, progress counts the subtasks.
                # If it doesn't, it counts the parent task itself.
                if issue["subtasks"]:
                    sub_total = len(issue["subtasks"])
                    sub_completed = sum(1 for sub in issue["subtasks"] if sub["state_type"] == "completed")
                    total_ms += sub_total
                    completed_ms += sub_completed
                else:
                    total_ms += 1
                    if issue["state_type"] == "completed":
                        completed_ms += 1
            
            pct = round((completed_ms / total_ms) * 100) if total_ms > 0 else 0
            
            ms["total_count"] = total_ms
            ms["completed_count"] = completed_ms
            ms["progress_pct"] = pct
            
            total_project_tasks += total_ms
            completed_project_tasks += completed_ms
            
            active_milestones.append(ms)
            
        p_info["milestones"] = active_milestones
        p_info["total_issues"] = total_project_tasks
        p_info["completed_issues"] = completed_project_tasks
        p_info["progress_pct"] = round((completed_project_tasks / total_project_tasks) * 100) if total_project_tasks > 0 else 0
        p_info["id"] = p_id
        processed_projects.append(p_info)
        
    processed_projects.sort(key=lambda x: (0 if "MBA USP" in x["name"] else 1, x["name"]))
    
    return {
        "viewer": viewer,
        "projects": processed_projects,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

def generate_html(data, output_path):
    data_json = json.dumps(data, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MBA USP & TCC - Timeline Dashboard</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- Tailwind CSS (via CDN) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        heading: ['Outfit', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    colors: {
                        zinc: {
                            950: '#09090b',
                            900: '#18181b',
                            800: '#27272a',
                            700: '#3f3f46',
                            600: '#52525b',
                            400: '#a1a1aa',
                            300: '#d4d4d8',
                            200: '#e4e4e7',
                            100: '#f4f4f5',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #09090b;
        }
        .font-heading {
            font-family: 'Outfit', sans-serif;
        }
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #09090b;
        }
        ::-webkit-scrollbar-thumb {
            background: #27272a;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #3f3f46;
        }
    </style>
</head>
<body class="text-zinc-200 min-h-screen pb-16">
    <div id="app" class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-xl">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/10">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14v7" />
                    </svg>
                </div>
                <div>
                    <h1 class="text-2xl font-bold font-heading text-white tracking-tight">Timeline MBA USP</h1>
                    <p class="text-sm text-zinc-400">Marcos Cronológicos, Aulas e Subtarefas do Programa</p>
                </div>
            </div>
            
            <div class="flex items-center gap-3 bg-zinc-950/60 py-2 px-4 rounded-xl border border-zinc-800">
                <div class="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center overflow-hidden">
                    <span id="user-avatar-placeholder" class="text-xs font-semibold text-zinc-300 font-heading"></span>
                    <img id="user-avatar" class="hidden w-full h-full object-cover" src="" alt="">
                </div>
                <div class="text-left">
                    <div id="user-name" class="text-xs font-medium text-zinc-300">Carregando...</div>
                    <div class="text-[10px] text-zinc-500">Sync: <span id="sync-time"></span></div>
                </div>
            </div>
        </header>

        <!-- Stats Panel -->
        <section id="stats-panel" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-1 block">Progresso Geral</span>
                <div class="flex items-baseline gap-2 mb-2">
                    <span id="project-pct" class="text-3xl font-bold font-heading text-white">0%</span>
                    <span class="text-xs text-zinc-500">completado</span>
                </div>
                <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                    <div id="project-pct-bar" class="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-center">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-1 block">Módulos Concluídos</span>
                <div class="flex items-baseline gap-2">
                    <span id="courses-completed" class="text-3xl font-bold font-heading text-white">0</span>
                    <span class="text-xs text-zinc-500">/ <span id="total-courses-count">0</span> concluídos</span>
                </div>
            </div>
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-center">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-1 block">Métricas de Aulas (Fases)</span>
                <div class="flex items-baseline gap-2">
                    <span id="total-completed-tasks" class="text-3xl font-bold font-heading text-white">0</span>
                    <span class="text-zinc-500 text-sm font-semibold font-heading">/ <span id="total-tasks">0</span></span>
                </div>
            </div>
        </section>

        <!-- Navigation Tabs -->
        <nav class="flex border-b border-zinc-800 mb-8 overflow-x-auto" id="tabs-container">
            <!-- Tabs dynamically injected -->
        </nav>

        <!-- Controls -->
        <section class="flex flex-col md:flex-row gap-4 items-center justify-between mb-8">
            <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
                <button onclick="setFilter('all')" id="btn-filter-all" class="px-4 py-2 text-xs font-medium rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 transition-all">
                    Tudo
                </button>
                <button onclick="setFilter('pending')" id="btn-filter-pending" class="px-4 py-2 text-xs font-medium rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-all">
                    Pendentes
                </button>
                <button onclick="setFilter('completed')" id="btn-filter-completed" class="px-4 py-2 text-xs font-medium rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-all">
                    Concluídos
                </button>
            </div>

            <div class="flex items-center gap-3 w-full md:w-auto">
                <div class="relative w-full md:w-64">
                    <input type="text" id="search-input" oninput="handleSearch(this.value)" placeholder="Buscar aulas ou subtarefas..." class="w-full pl-9 pr-4 py-2 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder-zinc-500">
                    <svg class="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>
        </section>

        <!-- Vertical Timeline Path -->
        <main class="relative pl-6 sm:pl-10">
            <!-- Central timeline track line -->
            <div class="absolute left-[33px] sm:left-[49px] top-6 bottom-6 w-0.5 bg-gradient-to-b from-indigo-500 via-purple-500 to-zinc-800 z-0"></div>
            
            <div id="timeline-container" class="space-y-12 relative z-10">
                <!-- Milestones and issues injected here -->
            </div>
        </main>
        
    </div>

    <!-- Data Injection & Interactive Logic -->
    <script>
        const roadmapData = __ROADMAP_DATA__;
        let activeProjectId = '';
        let currentFilter = 'all'; // all, pending, completed
        let searchQuery = '';

        function init() {
            if (roadmapData.projects && roadmapData.projects.length > 0) {
                activeProjectId = roadmapData.projects[0].id;
            }
            
            const viewer = roadmapData.viewer || {};
            document.getElementById('user-name').innerText = viewer.name || 'Estudante';
            document.getElementById('sync-time').innerText = roadmapData.generated_at || '';
            
            if (viewer.avatarUrl) {
                const avatarImg = document.getElementById('user-avatar');
                avatarImg.src = viewer.avatarUrl;
                avatarImg.classList.remove('hidden');
                document.getElementById('user-avatar-placeholder').classList.add('hidden');
            } else {
                document.getElementById('user-avatar-placeholder').innerText = (viewer.name || 'E').substring(0, 2).toUpperCase();
            }

            renderTabs();
            updateDashboard();
        }

        function renderTabs() {
            const container = document.getElementById('tabs-container');
            container.innerHTML = '';
            
            roadmapData.projects.forEach(project => {
                const isActive = project.id === activeProjectId;
                const activeClasses = 'border-indigo-500 text-white font-semibold';
                const inactiveClasses = 'border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700';
                
                const button = document.createElement('button');
                button.className = `py-4 px-6 text-sm border-b-2 font-heading tracking-wide transition-all whitespace-nowrap ${isActive ? activeClasses : inactiveClasses}`;
                button.innerText = project.name;
                button.onclick = () => selectProject(project.id);
                container.appendChild(button);
            });
        }

        function selectProject(projectId) {
            activeProjectId = projectId;
            document.getElementById('search-input').value = '';
            searchQuery = '';
            renderTabs();
            updateDashboard();
        }

        function updateDashboard() {
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (!project) return;

            document.getElementById('project-pct').innerText = `${project.progress_pct}%`;
            document.getElementById('project-pct-bar').style.width = `${project.progress_pct}%`;
            
            const totalMilestones = project.milestones.length;
            const completedMilestones = project.milestones.filter(m => m.progress_pct === 100 && m.total_count > 0).length;
            document.getElementById('courses-completed').innerText = completedMilestones;
            document.getElementById('total-courses-count').innerText = totalMilestones;
            
            document.getElementById('total-completed-tasks').innerText = project.completed_issues;
            document.getElementById('total-tasks').innerText = project.total_issues;

            renderTimeline(project);
        }

        function setFilter(filter) {
            currentFilter = filter;
            
            const btnAll = document.getElementById('btn-filter-all');
            const btnPending = document.getElementById('btn-filter-pending');
            const btnCompleted = document.getElementById('btn-filter-completed');
            
            const activeBtnClasses = 'border-indigo-500/30 bg-indigo-500/10 text-indigo-400';
            const inactiveBtnClasses = 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200';
            
            btnAll.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'all' ? activeBtnClasses : inactiveBtnClasses}`;
            btnPending.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'pending' ? activeBtnClasses : inactiveBtnClasses}`;
            btnCompleted.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'completed' ? activeBtnClasses : inactiveBtnClasses}`;
            
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (project) renderTimeline(project);
        }

        function handleSearch(query) {
            searchQuery = query.toLowerCase();
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (project) renderTimeline(project);
        }

        function renderTimeline(project) {
            const container = document.getElementById('timeline-container');
            container.innerHTML = '';
            
            if (!project.milestones || project.milestones.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-12 bg-zinc-900/30 border border-zinc-800 rounded-2xl">
                        <p class="text-sm text-zinc-500 font-heading">Nenhuma milestone mapeada.</p>
                    </div>
                `;
                return;
            }
            
            project.milestones.forEach((milestone, mIdx) => {
                // Filter issues
                let filteredIssues = milestone.issues.map(issue => {
                    // Filter subtasks
                    let filteredSubtasks = issue.subtasks;
                    if (currentFilter === 'pending') {
                        filteredSubtasks = issue.subtasks.filter(s => s.state_type !== 'completed');
                    } else if (currentFilter === 'completed') {
                        filteredSubtasks = issue.subtasks.filter(s => s.state_type === 'completed');
                    }
                    
                    if (searchQuery) {
                        filteredSubtasks = filteredSubtasks.filter(s => 
                            s.title.toLowerCase().includes(searchQuery) ||
                            s.identifier.toLowerCase().includes(searchQuery)
                        );
                    }
                    
                    // Return a clone with filtered subtasks
                    return {
                        ...issue,
                        subtasks: filteredSubtasks
                    };
                });
                
                // Filter top-level tasks based on state and search
                if (currentFilter === 'pending') {
                    filteredIssues = filteredIssues.filter(i => 
                        // Show if the task itself is not complete, OR if it has pending subtasks
                        (i.subtasks.length > 0) || (i.subtasks.length === 0 && i.state_type !== 'completed')
                    );
                } else if (currentFilter === 'completed') {
                    filteredIssues = filteredIssues.filter(i => 
                        (i.subtasks.length > 0 && i.subtasks.every(s => s.state_type === 'completed')) || 
                        (i.subtasks.length === 0 && i.state_type === 'completed')
                    );
                }
                
                if (searchQuery) {
                    filteredIssues = filteredIssues.filter(i => 
                        i.title.toLowerCase().includes(searchQuery) || 
                        i.identifier.toLowerCase().includes(searchQuery) ||
                        i.subtasks.length > 0
                    );
                }
                
                // Hide milestones with no matching issues if search/filter is active
                if (filteredIssues.length === 0 && (currentFilter !== 'all' || searchQuery)) {
                    return;
                }
                
                // Construct Milestone Timeline Section
                const milestoneSection = document.createElement('section');
                milestoneSection.className = 'relative timeline-milestone';
                
                // Dynamic styling for Milestone progress node
                let milestoneGlow = 'border-zinc-700 bg-zinc-900 text-zinc-400';
                if (milestone.progress_pct === 100 && milestone.total_count > 0) {
                    milestoneGlow = 'border-emerald-500 bg-emerald-950/80 text-emerald-400 shadow-md shadow-emerald-500/10';
                } else if (milestone.progress_pct > 0) {
                    milestoneGlow = 'border-indigo-500 bg-indigo-950/80 text-indigo-400 shadow-md shadow-indigo-500/10';
                }
                
                // Generate Tasks List HTML within the milestone
                let tasksHtml = '';
                if (filteredIssues.length === 0) {
                    tasksHtml = `
                        <div class="pl-6 py-4 text-xs text-zinc-500 italic">
                            Nenhuma aula cadastrada ou correspondente aos filtros.
                        </div>
                    `;
                } else {
                    tasksHtml = `<div class="relative space-y-6 mt-4 pl-4 sm:pl-8 border-l border-dashed border-zinc-800 ml-4 sm:ml-6">`;
                    
                    filteredIssues.forEach(issue => {
                        // Task node styling
                        let taskNodeClass = 'border-zinc-700 bg-zinc-900 text-zinc-500';
                        let taskTextClass = 'text-zinc-300';
                        
                        if (issue.state_type === 'completed') {
                            taskNodeClass = 'border-emerald-500 bg-emerald-950 text-emerald-400';
                            taskTextClass = 'text-zinc-400 line-through decoration-zinc-700';
                        } else if (issue.state_type === 'started') {
                            taskNodeClass = 'border-amber-500 bg-amber-950 text-amber-400 animate-pulse';
                            taskTextClass = 'text-white font-medium';
                        } else if (issue.state_type === 'unstarted') {
                            taskNodeClass = 'border-indigo-500 bg-indigo-950 text-indigo-400';
                        }
                        
                        // Construct subtasks HTML
                        let subtasksHtml = '';
                        if (issue.subtasks && issue.subtasks.length > 0) {
                            subtasksHtml = `<div class="mt-3.5 space-y-2.5 pl-4 sm:pl-6 border-l border-zinc-800">`;
                            
                            issue.subtasks.forEach(sub => {
                                let subDot = 'bg-zinc-800 border-zinc-700';
                                let subText = 'text-zinc-400';
                                
                                if (sub.state_type === 'completed') {
                                    subDot = 'bg-emerald-500 border-emerald-400';
                                    subText = 'text-zinc-500 line-through decoration-zinc-800';
                                } else if (sub.state_type === 'started') {
                                    subDot = 'bg-amber-500 border-amber-400 animate-pulse';
                                    subText = 'text-zinc-200';
                                }
                                
                                subtasksHtml += `
                                    <div class="flex items-center gap-3 relative group/sub">
                                        <!-- Subtask bullet node -->
                                        <div class="w-2 h-2 rounded-full border ${subDot} shrink-0 -ml-[21px] sm:-ml-[29px] z-20"></div>
                                        <div class="flex items-baseline justify-between w-full gap-2">
                                            <span class="text-xs ${subText} group-hover/sub:text-zinc-200 select-all">
                                                <span class="font-mono text-[10px] text-zinc-600 mr-1.5 select-all">${sub.identifier}</span>${sub.title}
                                            </span>
                                            <span class="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 font-semibold text-zinc-500 shrink-0">
                                                ${sub.state_name}
                                            </span>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            subtasksHtml += `</div>`;
                        }
                        
                        const labelsHtml = issue.labels.map(l => `
                            <span class="text-[9px] bg-zinc-800 text-zinc-500 px-1.5 py-0.5 rounded font-mono shrink-0">${l}</span>
                        `).join('');

                        tasksHtml += `
                            <div class="relative group">
                                <!-- Task timeline dot node -->
                                <div class="absolute -left-[23px] sm:-left-[39px] top-1.5 w-3.5 h-3.5 rounded-full border-2 ${taskNodeClass} shrink-0 z-10 flex items-center justify-center">
                                    <div class="w-1 h-1 rounded-full bg-current"></div>
                                </div>
                                
                                <!-- Task Card Details -->
                                <div class="bg-zinc-900/30 border border-zinc-800/80 rounded-xl p-4 hover:border-zinc-700/60 transition-all">
                                    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                                        <div class="flex flex-wrap items-center gap-2">
                                            <span class="font-mono text-xs text-indigo-400/80 font-bold tracking-tight select-all">${issue.identifier}</span>
                                            <h4 class="text-sm font-semibold ${taskTextClass} select-all">${issue.title}</h4>
                                        </div>
                                        <div class="flex items-center gap-2 shrink-0">
                                            ${labelsHtml}
                                            <span class="text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wide bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                                                ${issue.state_name}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    ${issue.description ? `<p class="text-xs text-zinc-500 mt-1.5 max-w-3xl leading-relaxed">${issue.description}</p>` : ''}
                                    
                                    <!-- Nested Subtasks list if any -->
                                    ${subtasksHtml}
                                </div>
                            </div>
                        `;
                    });
                    
                    tasksHtml += `</div>`;
                }

                // Append milestone layout
                const orderNumber = String(mIdx + 1).padStart(2, '0');
                
                milestoneSection.innerHTML = `
                    <!-- Milestone timeline badge/node -->
                    <div class="absolute -left-[23px] sm:-left-[39px] top-0 w-12 h-12 rounded-2xl border-2 ${milestoneGlow} flex flex-col items-center justify-center z-10 font-heading font-bold select-none">
                        <span class="text-[10px] text-zinc-500 uppercase leading-none tracking-tighter mb-0.5">Milestone</span>
                        <span class="text-sm leading-none">${orderNumber}</span>
                    </div>
                    
                    <!-- Milestone Card Header -->
                    <div class="pl-12 sm:pl-16">
                        <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl">
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-baseline gap-2 mb-3">
                                <h3 class="text-lg font-bold font-heading text-white tracking-wide select-all">${milestone.name}</h3>
                                <div class="flex items-center gap-2 font-mono text-xs text-zinc-400">
                                    <span>${milestone.completed_count}/${milestone.total_count} concluídos</span>
                                    <span class="text-zinc-600">•</span>
                                    <span class="text-indigo-400 font-semibold">${milestone.progress_pct}%</span>
                                </div>
                            </div>
                            <!-- Milestone Progress Bar -->
                            <div class="w-full bg-zinc-800/80 h-1.5 rounded-full overflow-hidden">
                                <div class="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-300" style="width: ${milestone.progress_pct}%"></div>
                            </div>
                            
                            <!-- Nested tasks timeline -->
                            ${tasksHtml}
                        </div>
                    </div>
                `;
                
                container.appendChild(milestoneSection);
            });
            
            if (container.children.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-12 bg-zinc-900/30 border border-zinc-800 rounded-2xl">
                        <p class="text-sm text-zinc-500 font-heading">Nenhuma atividade corresponde aos filtros atuais.</p>
                    </div>
                `;
            }
        }

        window.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""
    
    html_content = html_template.replace("__ROADMAP_DATA__", data_json)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Roadmap HTML compiled and saved successfully to {output_path}")

def main():
    try:
        print("1. Extracting data from Linear API...")
        data = fetch_linear_data()
        
        print("2. Processing project structures and milestones...")
        processed = process_data(data)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_file = os.path.join(base_dir, "roadmap.html")
        
        print("3. Generating interactive timeline HTML...")
        generate_html(processed, output_file)
        
        print("Dashboard timeline update completed!")
        
    except Exception as e:
        print(f"Error during roadmap generation: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
