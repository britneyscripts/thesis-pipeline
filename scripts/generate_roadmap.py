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
    
    # Initialize projects and their milestones
    for p in raw_projects:
        p_id = p["id"]
        milestones_list = []
        
        # Sort milestones by creation date to reflect the order they were planned
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
        
    # Categorize issues into projects and milestones
    for issue in raw_issues:
        proj = issue.get("project")
        if not proj:
            continue  # Skip issues without project
            
        proj_id = proj["id"]
        if proj_id not in projects_map:
            # If project details weren't in the raw_projects (e.g. archived or pagination edge cases), initialize it
            projects_map[proj_id] = {
                "name": proj["name"],
                "description": "",
                "milestones": [],
                "no_milestone_issues": []
            }
            
        milestone = issue.get("projectMilestone")
        
        # Structure the issue content for the frontend
        issue_data = {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue.get("description") or "",
            "state_name": issue["state"]["name"],
            "state_type": issue["state"]["type"], # backlog, unstarted, started, completed, canceled
            "labels": [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
        }
        
        if milestone:
            ms_id = milestone["id"]
            # Find the milestone in the project's milestone list
            ms_found = False
            for ms in projects_map[proj_id]["milestones"]:
                if ms["id"] == ms_id:
                    ms["issues"].append(issue_data)
                    ms_found = True
                    break
            
            # If the milestone was not registered (e.g. newly created, or edge case), create it
            if not ms_found:
                projects_map[proj_id]["milestones"].append({
                    "id": ms_id,
                    "name": milestone["name"],
                    "targetDate": None,
                    "issues": [issue_data]
                })
        else:
            projects_map[proj_id]["no_milestone_issues"].append(issue_data)

    # For each project, compute metrics
    processed_projects = []
    for p_id, p_info in projects_map.items():
        # Append a virtual milestone for "Outras Atividades / Sem Milestone" if there are any issues
        if p_info["no_milestone_issues"]:
            p_info["milestones"].append({
                "id": "no-milestone",
                "name": "Outras Atividades & TCC",
                "targetDate": None,
                "issues": p_info["no_milestone_issues"]
            })
            
        # Calculate progress for milestones
        total_project_issues = 0
        completed_project_issues = 0
        
        active_milestones = []
        for ms in p_info["milestones"]:
            total_ms = len(ms["issues"])
            completed_ms = sum(1 for i in ms["issues"] if i["state_type"] == "completed")
            
            # Calculate percentage progress
            pct = round((completed_ms / total_ms) * 100) if total_ms > 0 else 0
            
            ms["total_count"] = total_ms
            ms["completed_count"] = completed_ms
            ms["progress_pct"] = pct
            
            # Track overall project counts
            total_project_issues += total_ms
            completed_project_issues += completed_ms
            
            # Keep all milestones
            active_milestones.append(ms)
            
        p_info["milestones"] = active_milestones
        p_info["total_issues"] = total_project_issues
        p_info["completed_issues"] = completed_project_issues
        p_info["progress_pct"] = round((completed_project_issues / total_project_issues) * 100) if total_project_issues > 0 else 0
        p_info["id"] = p_id
        processed_projects.append(p_info)
        
    # Sort projects: put "MBA USP" first, then others alphabetically
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
    <title>MBA USP & TCC - Roadmap Dashboard</title>
    
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
    <div id="app" class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-xl">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/10">
                    <!-- Academic Cap SVG Icon -->
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14v7" />
                    </svg>
                </div>
                <div>
                    <h1 class="text-2xl font-bold font-heading text-white tracking-tight">MBA USP & TCC</h1>
                    <p class="text-sm text-zinc-400">Roadmap do Programa de Pós-Graduação & Projetos de Apoio</p>
                </div>
            </div>
            
            <div class="flex items-center gap-3 bg-zinc-950/60 py-2 px-4 rounded-xl border border-zinc-800">
                <div class="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center overflow-hidden">
                    <span id="user-avatar-placeholder" class="text-xs font-semibold text-zinc-300 font-heading"></span>
                    <img id="user-avatar" class="hidden w-full h-full object-cover" src="" alt="">
                </div>
                <div class="text-left">
                    <div id="user-name" class="text-xs font-medium text-zinc-300">Carregando...</div>
                    <div class="text-[10px] text-zinc-500">Última sync: <span id="sync-time"></span></div>
                </div>
            </div>
        </header>

        <!-- Main Stats Panel -->
        <section id="stats-panel" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-between">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-2">Status do Projeto</span>
                <div class="flex items-baseline gap-2">
                    <span id="project-pct" class="text-4xl font-bold font-heading text-white">0%</span>
                    <span class="text-sm text-zinc-500">concluído</span>
                </div>
                <div class="w-full bg-zinc-800 h-1.5 rounded-full mt-4 overflow-hidden">
                    <div id="project-pct-bar" class="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-between">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-2">Matérias & Milestones</span>
                <div class="flex items-baseline gap-2">
                    <span id="courses-completed" class="text-4xl font-bold font-heading text-white">0</span>
                    <span class="text-sm text-zinc-500">concluídas</span>
                </div>
                <p id="courses-subtext" class="text-xs text-zinc-400 mt-4">Total de 0 módulos mapeados</p>
            </div>
            <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-between">
                <span class="text-xs font-medium text-zinc-400 tracking-wider uppercase mb-2">Total de Tarefas</span>
                <div class="flex items-baseline gap-2">
                    <span id="total-completed-tasks" class="text-4xl font-bold font-heading text-white">0</span>
                    <span class="text-zinc-500 text-xl font-medium font-heading">/ <span id="total-tasks">0</span></span>
                </div>
                <p class="text-xs text-zinc-400 mt-4">Aulas e atividades registradas no Linear</p>
            </div>
        </section>

        <!-- Navigation Tabs -->
        <nav class="flex border-b border-zinc-800 mb-8 overflow-x-auto" id="tabs-container">
            <!-- Tabs dynamically injected here -->
        </nav>

        <!-- Controls (Filters and Search) -->
        <section class="flex flex-col md:flex-row gap-4 items-center justify-between mb-6">
            <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
                <button onclick="setFilter('all')" id="btn-filter-all" class="px-4 py-2 text-xs font-medium rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 transition-all">
                    Todas
                </button>
                <button onclick="setFilter('pending')" id="btn-filter-pending" class="px-4 py-2 text-xs font-medium rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-all">
                    Não Concluídas
                </button>
                <button onclick="setFilter('completed')" id="btn-filter-completed" class="px-4 py-2 text-xs font-medium rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-all">
                    Concluídas
                </button>
            </div>

            <div class="flex items-center gap-3 w-full md:w-auto">
                <div class="relative w-full md:w-64">
                    <input type="text" id="search-input" oninput="handleSearch(this.value)" placeholder="Buscar aulas ou tarefas..." class="w-full pl-9 pr-4 py-2 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder-zinc-500">
                    <svg class="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <button onclick="toggleAllMilestones()" class="px-3 py-2 text-xs font-medium bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-zinc-300 hover:text-white transition-all shrink-0">
                    Expandir/Recolher Tudo
                </button>
            </div>
        </section>

        <!-- Milestones Container -->
        <main id="milestones-container" class="space-y-6">
            <!-- Course cards/milestones injected here -->
        </main>
        
    </div>

    <!-- Data Injection -->
    <script>
        const roadmapData = __ROADMAP_DATA__;
        let activeProjectId = '';
        let currentFilter = 'all'; // all, pending, completed
        let searchQuery = '';
        let expandedMilestones = {};

        function init() {
            // Select first project by default
            if (roadmapData.projects && roadmapData.projects.length > 0) {
                activeProjectId = roadmapData.projects[0].id;
            }
            
            // Set up user profile
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

            // Render components
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
            // Clear search when switching projects
            document.getElementById('search-input').value = '';
            searchQuery = '';
            expandedMilestones = {}; // reset expansions
            renderTabs();
            updateDashboard();
        }

        function updateDashboard() {
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (!project) return;

            // Update stats
            document.getElementById('project-pct').innerText = `${project.progress_pct}%`;
            document.getElementById('project-pct-bar').style.width = `${project.progress_pct}%`;
            
            const totalMilestones = project.milestones.length;
            const completedMilestones = project.milestones.filter(m => m.progress_pct === 100 && m.total_count > 0).length;
            document.getElementById('courses-completed').innerText = completedMilestones;
            document.getElementById('courses-subtext').innerText = `Total de ${totalMilestones} módulos/milestones`;
            
            document.getElementById('total-completed-tasks').innerText = project.completed_issues;
            document.getElementById('total-tasks').innerText = project.total_issues;

            // Render milestones
            renderMilestones(project);
        }

        function setFilter(filter) {
            currentFilter = filter;
            
            // Toggle active filter button styles
            const btnAll = document.getElementById('btn-filter-all');
            const btnPending = document.getElementById('btn-filter-pending');
            const btnCompleted = document.getElementById('btn-filter-completed');
            
            const activeBtnClasses = 'border-indigo-500/30 bg-indigo-500/10 text-indigo-400';
            const inactiveBtnClasses = 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-200';
            
            btnAll.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'all' ? activeBtnClasses : inactiveBtnClasses}`;
            btnPending.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'pending' ? activeBtnClasses : inactiveBtnClasses}`;
            btnCompleted.className = `px-4 py-2 text-xs font-medium rounded-xl border transition-all ${filter === 'completed' ? activeBtnClasses : inactiveBtnClasses}`;
            
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (project) renderMilestones(project);
        }

        function handleSearch(query) {
            searchQuery = query.toLowerCase();
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (project) renderMilestones(project);
        }

        function toggleMilestone(milestoneId) {
            expandedMilestones[milestoneId] = !expandedMilestones[milestoneId];
            
            const el = document.getElementById(`issues-list-${milestoneId}`);
            const chevron = document.getElementById(`chevron-${milestoneId}`);
            
            if (expandedMilestones[milestoneId]) {
                el.classList.remove('hidden');
                chevron.style.transform = 'rotate(180deg)';
            } else {
                el.classList.add('hidden');
                chevron.style.transform = 'rotate(0deg)';
            }
        }

        function toggleAllMilestones() {
            const project = roadmapData.projects.find(p => p.id === activeProjectId);
            if (!project) return;
            
            // Check if at least one is collapsed to determine action (default to expand all)
            let anyCollapsed = project.milestones.some(m => !expandedMilestones[m.id]);
            
            project.milestones.forEach(m => {
                expandedMilestones[m.id] = anyCollapsed;
                
                const el = document.getElementById(`issues-list-${m.id}`);
                const chevron = document.getElementById(`chevron-${m.id}`);
                
                if (el && chevron) {
                    if (anyCollapsed) {
                        el.classList.remove('hidden');
                        chevron.style.transform = 'rotate(180deg)';
                    } else {
                        el.classList.add('hidden');
                        chevron.style.transform = 'rotate(0deg)';
                    }
                }
            });
        }

        function renderMilestones(project) {
            const container = document.getElementById('milestones-container');
            container.innerHTML = '';
            
            if (!project.milestones || project.milestones.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-12 bg-zinc-900/30 border border-zinc-800 rounded-2xl">
                        <p class="text-sm text-zinc-500 font-heading">Nenhuma milestone mapeada para este projeto.</p>
                    </div>
                `;
                return;
            }
            
            project.milestones.forEach((milestone, idx) => {
                // Filter issues
                let filteredIssues = milestone.issues;
                
                if (currentFilter === 'pending') {
                    filteredIssues = milestone.issues.filter(i => i.state_type !== 'completed');
                } else if (currentFilter === 'completed') {
                    filteredIssues = milestone.issues.filter(i => i.state_type === 'completed');
                }
                
                if (searchQuery) {
                    filteredIssues = filteredIssues.filter(i => 
                        i.title.toLowerCase().includes(searchQuery) || 
                        i.identifier.toLowerCase().includes(searchQuery) ||
                        (i.description && i.description.toLowerCase().includes(searchQuery))
                    );
                }
                
                // Hide milestones with no issues if we are filtering
                if (filteredIssues.length === 0 && (currentFilter !== 'all' || searchQuery)) {
                    return;
                }
                
                // If expansion state not set, default to expanding the first milestone or if search is active
                if (expandedMilestones[milestone.id] === undefined) {
                    expandedMilestones[milestone.id] = (idx === 0 || searchQuery !== '');
                }
                
                const isExpanded = expandedMilestones[milestone.id];
                
                // Milestone card element
                const milestoneDiv = document.createElement('div');
                milestoneDiv.className = 'bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700/80 rounded-2xl transition-all duration-300 overflow-hidden';
                
                // Construct inner HTML
                let issuesListHtml = '';
                if (filteredIssues.length === 0) {
                    issuesListHtml = `
                        <div class="py-4 text-center text-xs text-zinc-500 italic">
                            Nenhuma aula/tarefa pendente neste módulo.
                        </div>
                    `;
                } else {
                    filteredIssues.forEach(issue => {
                        let stateBadgeClass = 'bg-zinc-800/40 text-zinc-400 border border-zinc-700/50';
                        if (issue.state_type === 'completed') {
                            stateBadgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
                        } else if (issue.state_type === 'started') {
                            stateBadgeClass = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
                        } else if (issue.state_type === 'unstarted') {
                            stateBadgeClass = 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
                        }
                        
                        const labelsHtml = issue.labels.map(l => `
                            <span class="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-md font-medium">${l}</span>
                        `).join('');
                        
                        issuesListHtml += `
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center py-3.5 px-6 border-b border-zinc-800 last:border-0 hover:bg-zinc-800/20 transition-all gap-2 group">
                                <div class="flex items-start sm:items-center gap-3">
                                    <span class="font-mono text-xs text-indigo-400 font-semibold group-hover:text-indigo-300 shrink-0 select-all">${issue.identifier}</span>
                                    <div>
                                        <div class="text-sm text-zinc-200 group-hover:text-white font-medium select-all">${issue.title}</div>
                                        ${issue.description ? `<p class="text-xs text-zinc-500 mt-1 max-w-2xl">${issue.description}</p>` : ''}
                                    </div>
                                </div>
                                <div class="flex items-center gap-2 shrink-0">
                                    ${labelsHtml}
                                    <span class="text-[10px] px-2.5 py-1 rounded-full font-semibold uppercase tracking-wider ${stateBadgeClass}">
                                        ${issue.state_name}
                                    </span>
                                </div>
                            </div>
                        `;
                    });
                }

                // Percentage details and text
                const totalText = milestone.total_count === 1 ? 'atividade' : 'atividades';
                const progressText = `${milestone.completed_count}/${milestone.total_count} ${totalText} (${milestone.progress_pct}%)`;
                
                milestoneDiv.innerHTML = `
                    <div class="flex justify-between items-center px-6 py-5 cursor-pointer hover:bg-zinc-800/10 select-none transition-all" onclick="toggleMilestone('${milestone.id}')">
                        <div class="flex-1 pr-4">
                            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-baseline gap-2 mb-2">
                                <h3 class="text-base font-semibold font-heading text-white select-all">${milestone.name}</h3>
                                <span class="text-xs font-medium text-zinc-400 shrink-0 font-mono">${progressText}</span>
                            </div>
                            <!-- Mini Progress Bar -->
                            <div class="w-full bg-zinc-800/80 h-1 rounded-full overflow-hidden">
                                <div class="bg-gradient-to-r from-violet-500 to-indigo-500 h-full rounded-full transition-all duration-300" style="width: ${milestone.progress_pct}%"></div>
                            </div>
                        </div>
                        <button class="w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-zinc-400 hover:text-white hover:border-zinc-600 transition-all shrink-0 ml-2" id="btn-chevron-${milestone.id}">
                            <svg id="chevron-${milestone.id}" class="w-4 h-4 transition-transform duration-300" style="transform: ${isExpanded ? 'rotate(180deg)' : 'rotate(0deg)'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                    </div>
                    <div id="issues-list-${milestone.id}" class="${isExpanded ? '' : 'hidden'} border-t border-zinc-800 bg-zinc-950/40">
                        ${issuesListHtml}
                    </div>
                `;
                
                container.appendChild(milestoneDiv);
            });
            
            // If all filtered out
            if (container.children.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-12 bg-zinc-900/30 border border-zinc-800 rounded-2xl">
                        <p class="text-sm text-zinc-500 font-heading">Nenhuma atividade corresponde aos filtros atuais.</p>
                    </div>
                `;
            }
        }

        // Run setup on load
        window.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""
    
    # We replace the placeholder __ROADMAP_DATA__ with data_json to avoid Python f-string errors
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
        
        # Output directory is the root of the workspace (thesis-pipeline)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_file = os.path.join(base_dir, "roadmap.html")
        
        print("3. Generating interactive roadmap HTML...")
        generate_html(processed, output_file)
        
        print("Dashboard update completed!")
        
    except Exception as e:
        print(f"Error during roadmap generation: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
