# Daily Workflow: Thesis Pipeline

This guide outlines the exact steps you should take every time you start working on your `thesis-pipeline` project. Following these steps ensures your environment is correctly configured and all tools (`gcloud` and `python`) are ready to use.

## 1. Open the Terminal and Navigate to the Project
Always start by ensuring your terminal is in the correct project directory:
```bash
cd ~/thesisUSP/thesis-pipeline
```

## 2. Activate Your Conda Environment
Activate the dedicated conda environment:
```bash
conda activate tcc_usp
```

To verify it worked, you can run:
```bash
python3 --version
```

## 3. Authenticate with Google Cloud (If needed)
If your credentials have expired, or if you restarted your computer, re-authenticate with Google Cloud so Python scripts can communicate with BigQuery and Vertex AI:
```bash
gcloud auth application-default login
```
This will open a browser window for you to log in with your Google account.

## 4. Ensure Your GCP Project is Set
It's a good practice to ensure your terminal is pointing to the correct Google Cloud project:
```bash
gcloud config set project thesisusp
```

---

## 🚀 You are ready to work!
Once the above steps are done, your local setup is fully connected to BigQuery and Vertex AI. You can now run your Python scripts safely.
