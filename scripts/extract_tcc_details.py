import pypdf

files = {
    '1Vbm': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/the-agentic-commerce-opportunity-how-ai-agents-are-ushering-in-a-new-era-for-consumers-and-merchants_final.pdf',
    '1bhhF': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/pdfs & books/A new era of agentic commerce is here _ Google Cloud Blog.pdf'
}

output_path = '/Users/evabettinaacostadepaula/thesisUSP/extracted_details.txt'

with open(output_path, 'w', encoding='utf-8') as out:
    # Let's extract pages 4, 5, 6, 7 of 1Vbm (McKinsey report)
    out.write("="*80 + "\n")
    out.write("MCKINSEY REPORT (1Vbm) - Pages 4-8\n")
    out.write("="*80 + "\n")
    reader_vbm = pypdf.PdfReader(files['1Vbm'])
    for page_idx in range(3, min(8, len(reader_vbm.pages))):
        out.write(f"--- PAGE {page_idx+1} ---\n")
        out.write(reader_vbm.pages[page_idx].extract_text() + "\n\n")
        
    # Let's extract pages 4, 5, 6 of 1bhhF (Google Cloud Blog)
    out.write("="*80 + "\n")
    out.write("GOOGLE CLOUD BLOG (1bhhF) - Pages 4-7\n")
    out.write("="*80 + "\n")
    reader_g = pypdf.PdfReader(files['1bhhF'])
    for page_idx in range(3, min(7, len(reader_g.pages))):
        out.write(f"--- PAGE {page_idx+1} ---\n")
        out.write(reader_g.pages[page_idx].extract_text() + "\n\n")

print("Done writing details.")
