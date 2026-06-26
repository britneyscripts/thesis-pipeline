import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("Initializing Gemini Client with Vertex AI...")
    client = genai.Client(
        vertexai=True,
        project="thesisusp",
        location="us-central1"
    )
    
    query = (
        "Qual é o preço e a disponibilidade do 'Samsung Galaxy S26 Ultra' no site do Magazine Luiza "
        "no Brasil atualmente? Por favor, cite as fontes se encontrar."
    )
    
    print(f"\nSending Query to Gemini 2.5 Flash WITH Google Search Grounding:\n'{query}'\n")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        print("--- Gemini 2.5 Flash Response (With Search Grounding) ---")
        print(response.text)
        print("---------------------------------------------------------")
        
        # Check if there is grounding metadata
        print("\n--- Grounding Metadata & Sources ---")
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            metadata = candidate.grounding_metadata
            print("Web Search Queries Executed:")
            if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                for q in metadata.web_search_queries:
                    print(f"  - {q}")
            else:
                print("  No search queries logged.")
                
            print("\nSources Cited:")
            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        print(f"  - Title: {chunk.web.title}")
                        print(f"    URL: {chunk.web.uri}")
            else:
                print("  No grounding sources logged.")
        else:
            print("No grounding metadata available.")
            
    except Exception as e:
        print(f"Error calling Gemini with Grounding: {e}")

if __name__ == "__main__":
    main()
