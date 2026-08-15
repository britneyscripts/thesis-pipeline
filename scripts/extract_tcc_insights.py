import os
import pypdf
import re

files = {
    '11VO (Agentic Commerce Applications)': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/Agentic Commerce Applications How Autonomous AI Is Redefining the Retail and ECommerce Industry.pdf',
    '15gj (Agentic Commerce - Conversion)': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/Agentic Commerce_ o que é, como funciona e por que vai mudar o varejo - Conversion.pdf',
    '1Vbm (Agentic Commerce Opportunity - Mastercard)': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/the-agentic-commerce-opportunity-how-ai-agents-are-ushering-in-a-new-era-for-consumers-and-merchants_final.pdf',
    '1UHUn (Automation Curve in Agentic Commerce)': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/bibliografia_post_projeto/the-automation-curve-in-agentic-commerce_copia.pdf',
    '1bhhF (A new era of agentic commerce is here - Google Cloud)': '/Users/evabettinaacostadepaula/Library/CloudStorage/GoogleDrive-bbet.eva@gmail.com/Mi unidad/USP_MBA/mba-notes/pdfs & books/A new era of agentic commerce is here _ Google Cloud Blog.pdf'
}

keywords = [
    r'search', r'seek', r'consume', r'paradigm', r'tradicional', r'comportamento', 
    r'adoption', r'popular', r'surgimento', r'shift', r'mudança', r'varejo', r'commerce'
]

print("Starting PDF analysis...")

for name, filepath in files.items():
    print("="*80)
    print(f"ANALYZING: {name}")
    print(f"Path: {filepath}")
    if not os.path.exists(filepath):
        print("❌ File does not exist!")
        continue
        
    try:
        reader = pypdf.PdfReader(filepath)
        total_pages = len(reader.pages)
        print(f"Total pages: {total_pages}")
        
        # 1. Print first 1000 characters of the document (to see Title/Intro/Abstract)
        print("\n--- INTRO / EXECUTIVE SUMMARY SNIPPET ---")
        first_page_text = reader.pages[0].extract_text()
        second_page_text = reader.pages[1].extract_text() if total_pages > 1 else ""
        intro = (first_page_text + "\n" + second_page_text)[:2000]
        print(intro)
        print("-"*80)
        
        # 2. Search for keyword contexts
        print("\n--- KEYWORD MATCHES ---")
        matches_found = 0
        for page_num in range(total_pages):
            text = reader.pages[page_num].extract_text()
            # Find lines or sentences containing keywords
            sentences = re.split(r'\. |\n', text)
            for sentence in sentences:
                sentence_clean = sentence.strip()
                if not sentence_clean:
                    continue
                # Check for any keyword
                for kw in keywords:
                    if re.search(kw, sentence_clean, re.IGNORECASE):
                        # Ensure we don't print too many matches
                        if matches_found < 10:
                            print(f"[p. {page_num+1}] ({kw}): {sentence_clean}")
                        matches_found += 1
                        break
        print(f"Total keyword matches: {matches_found}")
        
    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")
