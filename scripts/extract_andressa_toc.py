import pypdf
import os

pdf_path = '/Users/evabettinaacostadepaula/Downloads/MBA_Andressa.pdf'
output_path = '/Users/evabettinaacostadepaula/thesisUSP/andressa_text.txt'

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found.")
    exit(1)

try:
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")
    
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(f"ANALYSIS OF MBA_Andressa.pdf\n")
        out.write(f"Total Pages: {total_pages}\n")
        out.write("="*80 + "\n")
        
        # Read first 15 pages (covers cover, index, abstract, intro)
        for idx in range(min(15, total_pages)):
            out.write(f"--- PAGE {idx+1} ---\n")
            out.write(reader.pages[idx].extract_text() + "\n\n")
            
    print(f"Successfully wrote TOC and intro pages to {output_path}")
except Exception as e:
    print(f"Error reading PDF: {str(e)}")
