import os
import sys
import shutil

def main():
    # Define Google Drive base directories
    drive_base = "/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA"
    vault_dir = os.path.join(drive_base, "mba-notes")
    
    if not os.path.exists(drive_base):
        print(f"Erro: Pasta base do Drive não encontrada em {drive_base}")
        return
        
    if not os.path.exists(vault_dir):
        print(f"Erro: Cofre 'mba-notes' não encontrado em {vault_dir}. Rode o bootstrap primeiro.")
        return

    # Define how old folders map to the new structured milestones in Obsidian vault
    mappings = {
        # Old folder name -> New milestone folder name suffix
        "estatistica_para_cd": "02 - Estatística para Ciência de Dados 2026",
        "técnicas_avançadas_captura_tratamento_dados": "03 - Técnicas Avançadas de Captura e Tratamento de Dados 2026",
        "Gestão Ágil de Projetos em Ciência de Dados e Inteligência Artificial": "05 - Gestão Ágil de Projetos em Ciência de Dados e Inteligência Artificial 2026",
        "Metodologia e Projeto para Ciências de Dados 2026": "06 - Metodologia e Projeto para Ciências de Dados 2026",
        "Introducao_a_ciencia_de_dados": "07 - Introdução a Ciências de Dados 2026",
        "programacao_para_ciencia_de_dados": "08 - Programação para Ciência de Dados 2026",
        "programacao_para_iniciantes": "08 - Programação para Ciência de Dados 2026",
        "Livros": "pdfs & books"

    }

    print("Iniciando organização automatizada dos seus PDFs e Livros...")
    
    # 1. Move folders mapped in the dictionary
    for old_name, new_name in mappings.items():
        src_path = os.path.join(drive_base, old_name)
        dest_path = os.path.join(vault_dir, new_name)
        
        # If dest is not "pdfs & books" and it's a milestone folder, we create an "anexos" subfolder to avoid cluttering the notes
        if new_name != "pdfs & books":
            dest_path = os.path.join(dest_path, "anexos")
            
        if os.path.exists(src_path) and os.path.isdir(src_path):
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
                
            print(f"\nMovendo arquivos de '{old_name}' para '{new_name}/anexos'...")
            
            # Move all contents
            for item in os.listdir(src_path):
                if item == ".DS_Store":
                    continue
                s_item = os.path.join(src_path, item)
                d_item = os.path.join(dest_path, item)
                
                try:
                    if os.path.exists(d_item):
                        # Avoid overwriting, rename if duplicate
                        base, ext = os.path.splitext(item)
                        d_item = os.path.join(dest_path, f"{base}_copia{ext}")
                    
                    shutil.move(s_item, d_item)
                    print(f"   -> Movido: {item}")
                except Exception as e:
                    print(f"   x Erro ao mover {item}: {e}")
            
            # Remove old directory if empty
            try:
                if not os.listdir(src_path) or (len(os.listdir(src_path)) == 1 and os.listdir(src_path)[0] == ".DS_Store"):
                    shutil.rmtree(src_path)
                    print(f"   -> Limpa pasta antiga vazia: {old_name}")
            except Exception as e:
                pass
        else:
            print(f"Nota: Pasta de origem '{old_name}' não encontrada ou já movida.")

    # 2. Move loose TCC / research files from the root of USP_MBA to "04 - TCC"
    tcc_dest = os.path.join(vault_dir, "04 - TCC", "anexos")
    if not os.path.exists(tcc_dest):
        os.makedirs(tcc_dest)
        
    print("\nOrganizando arquivos de TCC avulsos da raiz...")
    for item in os.listdir(drive_base):
        if item.endswith((".docx", ".gdoc", ".pdf", ".xlsx")) and ("projeto_pesquisa" in item.lower() or "tcc" in item.lower() or "artigo" in item.lower()):
            s_item = os.path.join(drive_base, item)
            d_item = os.path.join(tcc_dest, item)
            try:
                if os.path.exists(d_item):
                    base, ext = os.path.splitext(item)
                    d_item = os.path.join(tcc_dest, f"{base}_copia{ext}")
                shutil.move(s_item, d_item)
                print(f"   -> Movido para TCC/anexos: {item}")
            except Exception as e:
                print(f"   x Erro ao mover {item}: {e}")

    print("\n" + "="*60)
    print("ORGANIZAÇÃO DE ARQUIVOS CONCLUÍDA!")
    print("Todos os seus PDFs, livros e artigos foram organizados no cofre.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
