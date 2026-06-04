import os
import json
from dotenv import load_dotenv

def get_api_key(name):
    # 1. Try local environment variable / .env first
    load_dotenv()
    key = os.getenv(name)
    if key:
        return key

    # 2. Try GCP Secret Manager if local env is missing the key
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print(f"Warning: {name} not found in environment, and no GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT set.")
        return None

    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        # Secret path: projects/{project_id}/secrets/{name}/versions/latest
        secret_name = f"projects/{project_id}/secrets/{name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Error accessing Secret Manager for {name} in project {project_id}: {str(e)}")
        return None

def save_json(data, blob_path):
    # Determine local vs GCP mode
    load_dotenv()
    is_local = not bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    if is_local:
        # Save to local filesystem: extractions/{blob_path}
        local_path = os.path.join(base_dir, "extractions", blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved locally to {local_path}")
            return True
        except Exception as e:
            print(f"Error saving local JSON to {local_path}: {str(e)}")
            return False
    else:
        # Save to GCS: gs://{bucket}/{blob_path}
        bucket_name = os.getenv("GCS_BUCKET_NAME", "ghostprod-extractions")
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            blob.upload_from_string(json_str, content_type="application/json")
            print(f"Uploaded to GCS gs://{bucket_name}/{blob_path}")
            return True
        except Exception as e:
            print(f"Error uploading JSON to GCS gs://{bucket_name}/{blob_path}: {str(e)}")
            return False

