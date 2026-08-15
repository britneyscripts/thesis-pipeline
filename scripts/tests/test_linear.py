import os
import requests
from dotenv import load_dotenv

def test_connection():
    # Load environment variables from .env
    # We look for .env in the parent directory of scripts/tests/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"Error: .env file not found at {env_path}")
        return

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY not found in .env file.")
        return

    # Linear GraphQL Endpoint
    url = "https://api.linear.app/graphql"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    
    # Query to fetch the authenticated user profile
    query = """
    query {
      viewer {
        id
        name
        email
      }
    }
    """
    
    print("Testing connection to Linear API...")
    try:
        response = requests.post(url, json={"query": query}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "viewer" in data["data"]:
                viewer = data["data"]["viewer"]
                print("\n=============================================")
                print("🎉 CONNECTION SUCCESSFUL!")
                print(f"User ID: {viewer.get('id')}")
                print(f"Name:    {viewer.get('name')}")
                print(f"Email:   {viewer.get('email')}")
                print("=============================================")
            else:
                print(f"API Response error: {data.get('errors')}")
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
