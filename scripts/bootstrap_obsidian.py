import os
import sys
import re
from datetime import datetime
from generate_roadmap import fetch_linear_data, process_data


def sanitize_filename(name):
    # Remove characters that are unsafe for filenames/folders
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def main():
    try:
        # 1. Define paths
        pipeline_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load environment variables to read custom vault path
        from dotenv import load_dotenv
        env_path = os.path.join(pipeline_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            
        custom_vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if custom_vault_path:
            vault_dir = os.path.abspath(custom_vault_path)
            print(f"Usando caminho customizado do Vault: {vault_dir}")
        else:
            parent_dir = os.path.dirname(pipeline_dir)
            vault_dir = os.path.join(parent_dir, "mba-notes")
            print(f"Usando caminho padrão do Vault: {vault_dir}")

        
        print("1. Buscando dados do Linear API...")
        data = fetch_linear_data()
        processed = process_data(data)
        
        # We only want the "MBA USP" project
        mba_project = None
        for p in processed["projects"]:
            if "MBA USP" in p["name"]:
                mba_project = p
                break
                
        if not mba_project:
            print("Erro: Projeto 'MBA USP' não encontrado nos dados do Linear.")
            return
            
        print(f"2. Inicializando cofre do Obsidian em: {vault_dir}")
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)
            
        # Create a standard .gitignore for Obsidian Git
        gitignore_path = os.path.join(vault_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("""# Ignore macOS files
.DS_Store

# Ignore Obsidian workspace settings (avoid sync conflicts across screens)
.obsidian/workspace
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache/

# Ignore crash dumps / logs
*.log
""")
            print("   -> Criado .gitignore recomendado para Obsidian Git.")
            
        # Create a basic Welcome note
        readme_path = os.path.join(vault_dir, "index.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"""# Bem-vindo ao Cofre do MBA USP 🎓

Este cofre contém todas as anotações do seu MBA, estruturado de acordo com as Milestones do Linear.

Última sincronização/bootstrap: {processed['generated_at']}

## 📌 Atalhos Úteis
- [Link da Timeline Pública](https://britneyscripts.github.io/thesis-roadmap-public/)
- [Acesse seu Linear Workspace](https://linear.app/)
""")
            print("   -> Criado index.md principal.")

        print("3. Criando pastas de Cursos e arquivos de Aula...")
        for m_idx, milestone in enumerate(mba_project["milestones"]):
            # Create a clean folder name for the course
            folder_prefix = f"{m_idx + 1:02d} - "
            folder_name = folder_prefix + sanitize_filename(milestone["name"])
            course_dir = os.path.join(vault_dir, folder_name)
            
            if not os.path.exists(course_dir):
                os.makedirs(course_dir)
                
            print(f"   -> Curso: {milestone['name']}")
            
            for issue in milestone["issues"]:
                # Clean title for filename
                clean_title = sanitize_filename(issue["title"])
                file_name = f"{clean_title}.md"
                file_path = os.path.join(course_dir, file_name)
                
                # We skip overwriting existing files to preserve actual notes if they already exist
                if os.path.exists(file_path):
                    continue
                    
                # Format subtasks if any
                subtasks_section = ""
                if issue["subtasks"]:
                    subtasks_section = "\n## 📋 Subtarefas (Linear)\n"
                    for sub in issue["subtasks"]:
                        check = "x" if sub["state_type"] == "completed" else " "
                        subtasks_section += f"- [{check}] `{sub['identifier']}` {sub['title']}\n"
                
                # Write file content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"""---
id: {issue['id']}
code: {issue['identifier']}
title: "{issue['title'].replace('"', '\\"')}"
course: "{milestone['name'].replace('"', '\\"')}"
linear_url: https://linear.app/workspace/issue/{issue['identifier']}
status: {issue['state_name']}
created_at: {datetime.now().strftime("%Y-%m-%d")}
---

# {issue['title']}

## 📌 Links e Referências
- [Link da Tarefa no Linear](https://linear.app/workspace/issue/{issue['identifier']})
- [Slides da Aula e Materiais (Google Drive)]()
{subtasks_section}
## 📝 Anotações da Aula
*(Escreva suas anotações aqui)*

## 💡 Resumos & Insights
*(Resuma os pontos principais aprendidos nesta aula)*
""")
                    
        print("\n" + "="*60)
        print("BOOTSTRAP CONCLUÍDO COM SUCESSO!")
        print(f"Abra a pasta '{vault_dir}' como um Vault no Obsidian.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Erro no bootstrap: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
