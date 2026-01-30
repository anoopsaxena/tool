import subprocess
import logging
import os
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# executed subprocess 
def run_script(script_name):
    try:
        logging.info(f"Starting {script_name}...")
        result = subprocess.run(["python", script_name], capture_output=True, text=True, check=True)
        logging.info(f"Completed {script_name} successfully.")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred while running {script_name}: {e.stderr}")
        return False
    return True

# Main processor
def main():
    base_dir = r"D:\ismometricFiles\IsometricToolEngine\CrosscheckAlertNotification"
    os.chdir(base_dir)
    # Clear logs directory before running scripts
    logs_dir = "logs/"
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)
    os.makedirs(logs_dir, exist_ok=True)
    
    scripts = [
        #os.path.join(base_dir, "feed_processing.py"),  # Process feed files
        #os.path.join(base_dir, "cross_checks.py"),     # Run cross-checks
        #os.path.join(base_dir, "notification.py")      # Send notifications
        "feed_processing.py",  # Process feed files
        "cross_checks.py",     # check cross-checks scripts
        "notification.py"
    ]

    for script in scripts:
        logging.info(f"Attempting to run: {script}")
        success = run_script(script)
        if success:
            logging.info(f"Script {script} ran successfully.")
        else:
            logging.error(f"Script {script} failed. Aborting.")
            break

if __name__ == "__main__":
    main()
