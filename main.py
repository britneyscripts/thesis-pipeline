import os
import sys
import logging

# Ensure the scripts/ directory is in python path so that scripts can find config.py and each other.
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from extract_content import main as run_content
from extract_crux import main as run_crux  
from extract_pagespeed import main as run_pagespeed
from load_to_bigquery import load_all as run_bigquery_load

from datetime import datetime

def run_pipeline(request):
    run_str = datetime.now().strftime("%Y%m%d_%H%M")
    logging.info(f"=== START PIPELINE RUN {run_str} ===")
    
    for name, fn in [
        ("Content Extraction", run_content),
        ("CrUX Extraction", run_crux),
        ("PageSpeed Extraction", run_pagespeed)
    ]:
        try:
            logging.info(f"Running {name}...")
            fn(run_str)
            logging.info(f"{name} finished: SUCCESS")
        except Exception as e:
            logging.error(f"{name} FAILED: {str(e)}")
            # Continue running remaining scripts — partial data is better than none
            
    # Load new data to BigQuery after all extractions
    try:
        logging.info("Running BigQuery load...")
        run_bigquery_load()
        logging.info("BigQuery load: SUCCESS")
    except Exception as e:
        logging.error(f"BigQuery load FAILED: {str(e)}")

    logging.info("=== PIPELINE FINISHED ===")
    return "Pipeline completed", 200
