import pypdf
import os
import re

pdf_files = [
    '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/regras_tcc/MBA CD_Met - Módulo 2 - Parte 1 - Modelo USP e Normas_2026.pdf',
    '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/regras_tcc/MBA CD_Met  - Módulo 2 - Parte 2 - LaTex_2026.pdf',
    '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/regras_tcc/MBA CD_Met  - Módulo 2 - Parte 3 - Turnitin_2026.pdf',
    '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/regras_tcc/Norma NBR 14724 atualizada - 2024.pdf'
]

output_path = '/Users/evabettinaacostadepaula/thesisUSP/tcc_rules_extracted.txt'

keywords = [
    r'pág', r'pag', r'limite', r'capítulo', r'tamanho', r'máximo', r'mínimo', r'max', r'min', r'regras', r'recomenda'
]

with open(output_path, 'w', encoding='utf-8') as out:
    for filepath in pdf_files:
        out.write("="*80 + "\n")
        out.write(f"FILE: {os.path.basename(filepath)}\n")
        out.write("="*80 + "\n")
        
        if not os.path.exists(filepath):
            out.write("❌ File not found.\n\n")
            continue
            
        try:
            reader = pypdf.PdfReader(filepath)
            total_pages = len(reader.pages)
            out.write(f"Total pages: {total_pages}\n\n")
            
            # Print entire PDF content if small (e.g. < 15 pages) to be thorough
            if total_pages < 25:
                for idx in range(total_pages):
                    out.write(f"--- PAGE {idx+1} ---\n")
                    out.write(reader.pages[idx].extract_text() + "\n\n")
            else:
                # Search by keywords
                out.write("--- KEYWORD SEARCH RESULTS (Long PDF) ---\n")
                for idx in range(total_pages):
                    text = reader.pages[idx].extract_text()
                    sentences = re.split(r'\. |\n', text)
                    for s in sentences:
                        s_clean = s.strip()
                        if not s_clean:
                            continue
                        for kw in keywords:
                            if re.search(kw, s_clean, re.IGNORECASE):
                                out.write(f"[p. {idx+1}] ({kw}): {s_clean}\n")
                                break
                out.write("\n")
        except Exception as e:
            out.write(f"❌ Error reading PDF: {str(e)}\n\n")

print(f"Done. Wrote results to {output_path}")
