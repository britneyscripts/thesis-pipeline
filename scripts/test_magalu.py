import os
import sys
import requests
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    url = "https://www.magazineluiza.com.br/samsung-galaxy-s26-ultra-5g-512gb-galaxy-ai-preto-69-12gb-ram-cam-quadrupla-200-50-10-50mp-bateria-5000mah-dual-chip/p/241159000/te/g26u/?seller_id=magazineluiza"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"1. Fetching Magazine Luiza URL:\n{url}\n")
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        status = resp.status_code
        content_len = len(resp.content)
        print(f"Status Code: {status}")
        print(f"Content Length: {content_len} bytes")
        
        soup = BeautifulSoup(resp.content, "html.parser")
        title = soup.title.string if soup.title else "N/A"
        print(f"Page Title: {title}")
        
        # Check if we were blocked
        is_blocked = False
        if status != 200:
            is_blocked = True
        elif title and ("Just a moment" in title or "Não é possível acessar" in title or "Block" in title or "Forbidden" in title):
            is_blocked = True
        elif content_len < 2000:
            is_blocked = True
            
        print(f"Is Blocked by Firewall/Cloudflare? {'YES' if is_blocked else 'NO'}")
        
        # Grab a preview of text to send to Gemini
        body_text = ""
        if soup.body:
            # clean up scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            body_text = soup.body.get_text(separator=" ", strip=True)[:4000] # send up to 4000 chars of text
            
        print(f"\nFetched text preview (first 300 chars):\n{body_text[:300]}...\n")
        
    except Exception as e:
        print(f"Failed to fetch: {e}")
        status = 500
        body_text = "FAILED TO FETCH"
        is_blocked = True
        title = "N/A"
        
    print("2. Calling Gemini 2.5 Flash via Vertex AI...")
    try:
        client = genai.Client(
            vertexai=True,
            project="thesisusp",
            location="us-central1"
        )
        
        prompt = (
            "You are a shopping assistant. Read the following scraped webpage data from a store. "
            "Extract the product name, price, and availability status (in stock vs out of stock). "
            "If the page indicates a Cloudflare block, access denied, captcha, or lacks product information, "
            "explicitly report that the content is blocked or missing. Answer in Portuguese.\n\n"
            f"URL: {url}\n"
            f"HTTP Status: {status}\n"
            f"Title: {title}\n"
            f"Page Text Preview:\n{body_text}\n"
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        print("\n--- Gemini 2.5 Flash Response ---")
        print(response.text)
        print("---------------------------------")
        
    except Exception as e:
        print(f"Gemini call failed: {e}")

if __name__ == "__main__":
    main()
