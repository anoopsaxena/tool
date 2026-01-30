#from zipExtraction import unzip_and_validate
from zipExtraction2 import unzip_and_validate
#from extraction_issue import process_files
from pcf import process_pcf_files
from pmsspl import process_pmsspl_files
#from pmsjnth import process_pmsjnth_files
from pmsjnth import process_pmsjnth_files,enrich_pmsjnth_with_pilewall
from pmsisod import process_pmsisod_files
from pmsmat import process_pmsmat_files
from pipe_fix import process_pipe_files
#23 Nov'25
from db_importer import import_feed_files_to_fabs
#11 June
from flange import process_pmsbolt_files
#from support_fix import process_support_files
import csv
import pandas as pd
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import shutil
import zipfile
import subprocess

#19March-2025 added all pcf files in one zip foldr
# Searches for all .pcf files in the given source directories and copies them into a zip file.

def copy_pcf_files(source_dirs, destination_zip):
    
    with zipfile.ZipFile(destination_zip, 'w') as zipf:
        for source_dir in source_dirs:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.lower().endswith(".pcf"):
                        source_file = os.path.join(root, file)
                        try:
                            zipf.write(source_file, os.path.basename(source_file))
                            print(f"Copied: {source_file} -> {destination_zip}")
                        except Exception as e:
                            print(f"Error copying {source_file}: {e}")
                            


# loading into dictionaries
def load_csv_data(file_path):
    
    data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error loading CSV data from {file_path}: {e}")
    return data

def send_email_notification(subject, body):
    sender_email = "noreply@ccc.net"
    receiver_email =["asaxena@ccc.net"]#,"skassab@ccc.net","msantina@ccc.net"] 
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('mailhost.ccc.net', 25)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email notification sent successfully.")
    except Exception as e:
        print("Failed to send email notification:", e)
# Main controller

# Merge two CSV files into a single file

def merge_csv(file1, file2, output_file):
    """
    Merge two CSV files, ensuring the `matsubcode` column remains a string.
    """
    try:
        # Read both CSV files
        df1 = pd.read_csv(file1, dtype={"matsubcode": str})
        df2 = pd.read_csv(file2, dtype={"matsubcode": str})

        # Check if column structures match
        if list(df1.columns) != list(df2.columns):
            raise ValueError("The two CSV files do not have the same columns and cannot be merged.")

        # Append the second CSV data to the first
        merged_df = pd.concat([df1, df2], ignore_index=True)

        # Force `matsubcode` to be a string (to prevent type coercion during saving)
        if "matsubcode" in merged_df.columns:
            merged_df["matsubcode"] = merged_df["matsubcode"].astype(str)

        # Write the merged data to a new file
        merged_df.to_csv(output_file, index=False)
        print(f"Merged CSV file saved as {output_file}")
    except Exception as e:
        print(f"Error while merging CSV files: {e}")

#07 March :: added for status update
# Call postToolStatusUpdt.py to update isometric_tracker status.
def update_isometric_status():
    
    print("Updating isometric_tracker status via postToolStatusUpdt.py...")
    try:
        result = subprocess.run(
            ["python", "postToolStatusUpdt.py"],
            capture_output=True,
            text=True,
            cwd=r'D:\ismometricFiles\IsometricToolEngine\ToolEngine'
        )
        print(f"Status update output: {result.stdout}")
        if result.stderr:
            print(f"Status update error: {result.stderr}")
    except Exception as e:
        print(f"Error running postToolStatusUpdt.py: {e}")
        raise
        
def main(): 
    
    input_directory = 'D:/ismometricFiles/zipFiles'
    output_directory = 'D:/ismometricFiles'
    pcfziplocation = 'D:/ismometricFiles/pcfZipFiles'
    pcf_zip_path = os.path.join(pcfziplocation, 'pcfs.zip')
    excel_path = "D:/ismometricFiles/referenceFiles/abs-nfs.xlsx"
    #pilewall_xlsx = "D:/ismometricFiles/referenceFiles/Pipe Wall Thickness Table (REV-00).xlsx"
    
    pilewall_xlsx = "D:/ismometricFiles/referenceFiles/Piping Wall Thickness Table (REV-01).xlsx"
    
    # File paths for  outputs
    output_pcf_csv = f"{output_directory}/FeedFiles/Output_PMSISOH.csv"
    output_pmsspl_csv = f"{output_directory}/FeedFiles/Output_PMSSPL.csv"
    #output_pmsjnth_csv = f"{output_directory}/temp_PMSJNTH_enriched.csv"
    output_pmsjnth_csv = f"{output_directory}/FeedFiles/Output_PMSJNTH.csv"
    output_pmsmat_csv = f"{output_directory}/FeedFiles/Output_PMSMAT.csv"
    pipe_pmsisod_csv = f"{output_directory}/Output_PMSISOD_PIPE.csv"
    nonPipe_pmsisod_csv = f"{output_directory}/Output_PMSISOD_NonPipe.csv"
    output_pmsisod_csv = f"{output_directory}/FeedFiles/Output_PMSISOD.csv"
    #11 June
    output_pmsflintch_csv = f"{output_directory}/FeedFiles/Output_FLANGE.csv"
    #support_pmsisod_csv = f"{output_directory}/Output_PMSISOD_SUPPORT.csv"
    # Step 1: Unzip and validate files
    required_extensions = (".pcf", ".txt")
    #extracted_folders = process_files(input_directory, required_extensions)
    extracted_folders = unzip_and_validate(input_directory, required_extensions)
    if not extracted_folders:
        print("Validation failed. Missing required files. Aborting...")
        subject = f"Missing required File in Folder {input_directory}"
        body = f"Required file found in extracted folder"
        send_email_notification(subject, body)
        return
    # Copy PCF files into a zip file
    os.makedirs(os.path.dirname(pcf_zip_path), exist_ok=True)
    copy_pcf_files(extracted_folders, pcf_zip_path)
    
    # PCF files
    process_pcf_files(extracted_folders, output_pcf_csv, excel_path, pilewall_xlsx)

    #   Process PMSJNTH files
    process_pmsjnth_files(extracted_folders, output_pmsjnth_csv, pilewall_xlsx)

    # r PMSISOD processing
    pmsisoh_data = load_csv_data(output_pcf_csv)  # Load PCF data
    pmsjnth_data = load_csv_data(output_pmsjnth_csv)  # Load PMSJNTH data
    
    #MAt process
    process_pmsmat_files(extracted_folders, output_pmsmat_csv)

    # Process PMSISOD files
    process_pmsisod_files(extracted_folders, nonPipe_pmsisod_csv, pmsisoh_data, pmsjnth_data)
    process_pipe_files(extracted_folders, pipe_pmsisod_csv, pmsisoh_data)
    #process_support_files(extracted_folders, support_pmsisod_csv, pmsisoh_data)
    
    merge_csv(pipe_pmsisod_csv,nonPipe_pmsisod_csv,output_pmsisod_csv)
    
    # Merge the three output files into one
    #csv_files_to_merge = [nonPipe_pmsisod_csv, pipe_pmsisod_csv, support_pmsisod_csv]
    #merge_csv_files(csv_files_to_merge, output_pmsisod_csv)
    #time.sleep(10)
    
    #enriched_pmsjnth_csv = f"{output_directory}/Enriched_PMSJNTH.csv"
    #enrich_pmsjnth_with_reference(output_pmsjnth_csv, pilewall_xlsx, enriched_pmsjnth_csv)
    time.sleep(10)
    enrich_pmsjnth_with_pilewall(output_pmsjnth_csv,pilewall_xlsx)
    
    time.sleep(20)
    process_pmsspl_files(extracted_folders, output_pmsspl_csv,output_pcf_csv,output_pmsisod_csv)
    #11-June
    process_pmsbolt_files(extracted_folders, output_pmsflintch_csv, output_pcf_csv)
    subject = "ISO Spool Processing Notification!"
    body = "Processing has started for the Isometric SPOOL files."      
    send_email_notification(subject, body)
    
    # Update isometric_tracker status ::07-May
    update_isometric_status()
    print("All processing completed successfully.")
    
    # call db_importer file 
    print("Starting DB Import to FABS staging (local db ...")
    import_feed_files_to_fabs()
    print("DB Import completed successfully.")
    

if __name__ == "__main__":
    main()
