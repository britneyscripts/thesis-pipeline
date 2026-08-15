import os
import pypdf

files = {
    '11VO': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/Agentic Commerce Applications How Autonomous AI Is Redefining the Retail and ECommerce Industry.pdf',
    '15gj': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/Agentic Commerce_ o que é, como funciona e por que vai mudar o varejo - Conversion.pdf',
    '1Vbm': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/the-agentic-commerce-opportunity-how-ai-agents-are-ushering-in-a-new-era-for-consumers-and-merchants_final.pdf',
    '1UHUn': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/the-automation-curve-in-agentic-commerce_copia.pdf',
    '1bhhF': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/pdfs & books/A new era of agentic commerce is here _ Google Cloud Blog.pdf'
}

output_path = '/Users/evabettinaacostadepaula/thesisUSP/extracted_intro.txt'

with open(output_path, 'w', encoding='utf-8') as out:
    for name, filepath in files.items():
        out.write('='*80 + '\n')
        out.write(f'FILE KEY: {name}\n')
        out.write(f'BASENAME: {os.path.basename(filepath)}\n')
        out.write('='*80 + '\n')
        
        if not os.path.exists(filepath):
            out.write('ERROR: File does not exist\n\n')
            continue
            
        try:
            reader = pypdf.PdfReader(filepath)
            out.write(f'Total pages: {len(reader.pages)}\n\n')
            
            # Write first 3 pages
            for idx in range(min(3, len(reader.pages))):
                out.write(f'--- PAGE {idx+1} ---\n')
                text = reader.pages[idx].extract_text()
                out.write(text + '\n\n')
        except Exception as e:
            out.write(f'ERROR reading PDF: {str(e)}\n\n')

print(f"Successfully wrote intros to {output_path}")
