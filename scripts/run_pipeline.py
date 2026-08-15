import os
import sys
import subprocess
import time
import datetime

def log_pipeline(log_path, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def main():
    # Set directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    extractions_dir = os.path.join(base_dir, "extractions")
    os.makedirs(extractions_dir, exist_ok=True)
    
    pipeline_log = os.path.join(extractions_dir, "pipeline_runs.log")
    
    # Locate virtual env python
    # We prioritize the local venv in ~/mba_thesis/venv
    venv_python = os.path.join(base_dir, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        # Fallback to .venv if present
        venv_python = os.path.join(base_dir, ".venv", "bin", "python")
        if not os.path.exists(venv_python):
            # Fallback to current sys.executable
            venv_python = sys.executable
            
    scripts_to_run = [
        ("Content Extraction", os.path.join(script_dir, "extract_content.py")),
        ("CrUX Extraction", os.path.join(script_dir, "extract_crux.py")),
        ("PageSpeed Extraction", os.path.join(script_dir, "extract_pagespeed.py"))
    ]
    
    run_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    env = os.environ.copy()
    env["RUN_STR"] = run_str

    log_pipeline(pipeline_log, f"=== START PIPELINE RUN {run_str} ===")
    print("=== Starting E-commerce Extraction Pipeline ===")
    
    pipeline_start = time.time()
    results = {}
    
    for name, path in scripts_to_run:
        print(f"\n---> Executing {name}...")
        log_pipeline(pipeline_log, f"Running {name} ({os.path.basename(path)})...")
        
        script_start = time.time()
        try:
            # We run the script using the environment's python bin
            process = subprocess.Popen(
                [venv_python, path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Stream stdout in real-time to pipeline_cron.log
            stdout_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    stdout_lines.append(line)
                    
            process.communicate()
            exit_code = process.returncode
            duration = time.time() - script_start
            success = (exit_code == 0)
            
            results[name] = {
                "success": success,
                "duration": duration,
                "exit_code": exit_code
            }
            
            status_str = "SUCCESS" if success else f"FAILED (Exit Code {exit_code})"
            log_msg = f"{name} finished: {status_str} | Duration: {duration:.2f}s"
            log_pipeline(pipeline_log, log_msg)
            print(f"---> {log_msg}")
            
        except Exception as e:
            duration = time.time() - script_start
            results[name] = {
                "success": False,
                "duration": duration,
                "exit_code": -99
            }
            log_msg = f"Error running {name}: {str(e)} | Duration: {duration:.2f}s"
            log_pipeline(pipeline_log, log_msg)
            print(f"---> ERROR: {log_msg}", file=sys.stderr)
            
    total_duration = time.time() - pipeline_start
    
    # Calculate overall status
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(scripts_to_run)
    
    if success_count == total_count:
        overall_status = "All Succeeded"
    elif success_count > 0:
        overall_status = "Some Succeeded"
    else:
        overall_status = "None Succeeded"
        
    summary_msg = f"=== PIPELINE FINISHED | Status: {overall_status} ({success_count}/{total_count} passed) | Total Duration: {total_duration:.2f}s ==="
    log_pipeline(pipeline_log, summary_msg)
    log_pipeline(pipeline_log, "=== END PIPELINE RUN ===\n")
    print(f"\n{summary_msg}")
    
    # Exit with code reflecting overall status
    if overall_status == "All Succeeded":
        sys.exit(0)
    elif overall_status == "Some Succeeded":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
