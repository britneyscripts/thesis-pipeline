import os
import sys
import shutil
import subprocess
from generate_roadmap import fetch_linear_data, process_data, generate_html

def run_git_command(args, cwd):
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return stderr or empty if error
        return f"Error: {e.stderr.strip()}"

def main():
    try:
        # 1. Define paths
        pipeline_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        parent_dir = os.path.dirname(pipeline_dir)
        public_dir = os.path.join(parent_dir, "thesis-roadmap-public")
        
        print("1. Gerando os dados mais recentes do Linear...")
        data = fetch_linear_data()
        processed = process_data(data)
        
        # Temp file path in pipeline
        temp_html_path = os.path.join(pipeline_dir, "roadmap.html")
        generate_html(processed, temp_html_path)
        
        # 2. Setup public folder
        if not os.path.exists(public_dir):
            print(f"2. Criando diretório público em: {public_dir}")
            os.makedirs(public_dir)
            
        # Initialize Git in public folder if not already done
        git_folder = os.path.join(public_dir, ".git")
        if not os.path.exists(git_folder):
            print("   -> Inicializando repositório Git no diretório público...")
            run_git_command(["git", "init", "-b", "main"], public_dir)
            
        # 3. Copy file to index.html (renamed for GitHub Pages)
        public_index_path = os.path.join(public_dir, "index.html")
        shutil.copy2(temp_html_path, public_index_path)
        print("3. Copiado e renomeado para index.html no diretório público.")
        
        # Create a basic README for the public repo
        readme_path = os.path.join(public_dir, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("# MBA USP & TCC - Roadmap Public\n\nEste repositório contém o painel visual estático da timeline do MBA. Atualizado automaticamente via pipeline privado.\n")
            print("   -> Criado README.md padrão no repositório público.")
            
        # 4. Check git status in public folder
        status = run_git_command(["git", "status", "--porcelain"], public_dir)
        if not status:
            print("4. Nenhuma mudança detectada na timeline. O repositório público já está atualizado!")
            return
            
        print("4. Alterações detectadas no repositório público. Commitando...")
        run_git_command(["git", "add", "index.html"], public_dir)
        if os.path.exists(readme_path):
            run_git_command(["git", "add", "README.md"], public_dir)
            
        run_git_command(["git", "commit", "-m", "update: sync roadmap timeline"], public_dir)
        
        # Check if remote exists
        remotes = run_git_command(["git", "remote"], public_dir)
        if "origin" not in remotes:
            print("\n" + "="*60)
            print("ATENÇÃO: Repositório público criado e commitado localmente!")
            print("Para publicar na nuvem e ativar o GitHub Pages, faça o seguinte:")
            print("1. Crie um repositório PÚBLICO no seu GitHub com o nome: thesis-roadmap-public")
            print("2. No terminal do seu Mac, rode os seguintes comandos:")
            print(f"   cd {public_dir}")
            print("   git remote add origin https://github.com/britneyscripts/thesis-roadmap-public.git")
            print("   git push -u origin main")
            print("="*60 + "\n")
        else:
            print("5. Empurrando atualizações para o GitHub público...")
            push_res = run_git_command(["git", "push", "origin", "main"], public_dir)
            print("Push concluído com sucesso!")
            print(f"Sua timeline atualizada está sendo implantada em: https://britneyscripts.github.io/thesis-roadmap-public/")
            
    except Exception as e:
        print(f"Erro ao publicar: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
