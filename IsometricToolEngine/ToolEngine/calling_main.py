import os
import shutil
import subprocess
from utils.sharePointConnectionTest import download_zip_files_from_sharepoint, upload_csv_to_datewise_folder, get_sharepoint_token_function
from utils.NotificationScript import send_email_notification
import argparse 
import io

def main(param):
    # SharePoint connection details
    print("param::", param)
    site_url = "https://cccgroup.sharepoint.com/sites/NFSProject2"
    source_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Isometric_Files"
    #destination_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Talisman_Files"
    destination_folder_url = "/sites/NFSProject2/NFS_Data_Hub/03- CCC_Workpacks/02- Cloud Apps Data/03-Talisman/02- Talisman and PCF Staging Export"
    #https://cccgroup.sharepoint.com/:f:/s/NFSProject2/EiwE1uLSxUxKpuHS1rr0nx4BJsQONYI3sTRq4gxAq_F-mg?e=4kMdSg
    # Local directories
    local_input_dir = 'D:/ismometricFiles/zipFiles'
    local_output_dir = 'D:/ismometricFiles'
    pcf_zip_dir = 'D:/ismometricFiles/pcfZipFiles'
    #cleaning the existing files
    clean_output_dir = r"D:\ismometricFiles\FeedFiles"
    if os.path.exists(clean_output_dir):
        shutil.rmtree(clean_output_dir)
        os.makedirs(clean_output_dir, exist_ok=True)
    
    # Cleaning the existing files in pcf_zip_dir
    if os.path.exists(pcf_zip_dir):
        shutil.rmtree(pcf_zip_dir)
        os.makedirs(pcf_zip_dir, exist_ok=True)
      

    # Step 1: Authenticate with SharePoint
    token_func = get_sharepoint_token_function()

    # Step 2: Download input files
    print("Downloading files from SharePoint...")
    #download_zip_files_from_sharepoint(token_func, site_url, source_folder_url, local_input_dir)
    import time
    time.sleep(25)
    # Step 3: Run centralizedRunnerScript.py
    print("Running centralizedRunnerScript.py...")
    #issue through MQ
    script_path = os.path.abspath("D:/ismometricFiles/IsometricToolEngine/ToolEngine/centralizedRunnerScript.py")
    print("Running centralizedRunnerScript.py...")
    subprocess.run(["python", script_path, local_input_dir, local_output_dir])
    #subprocess.run(["python", "centralizedRunnerScript.py", local_input_dir, local_output_dir])

    # Step 4: Upload generated CSVs to SharePoint
    print("Uploading processed CSV files to SharePoint...")
    output_csvs = [
        f"{local_output_dir}/FeedFiles/Output_PMSISOH.csv",
        f"{local_output_dir}/FeedFiles/Output_PMSSPL.csv",
        f"{local_output_dir}/FeedFiles/Output_PMSJNTH.csv",
        f"{local_output_dir}/FeedFiles/Output_PMSISOD.csv",
        f"{local_output_dir}/FeedFiles/Output_PMSMAT.csv",
        f"{local_output_dir}/FeedFiles/Output_FLANGE.csv",
        f"{pcf_zip_dir}/pcfs.zip",
    ]

    for csv_file in output_csvs:
        if os.path.exists(csv_file):
            print("upload to Sharepoint")
            #upload_csv_to_datewise_folder(token_func, site_url, destination_folder_url, csv_file)
            upload_csv_to_datewise_folder(token_func, site_url, destination_folder_url, csv_file, param)  ## issue here
            

    print("Workflow completed successfully.")
    #subject = f"Notification for Feed Files Upload.!!!"
    #body = f"Successfully uploaded the feed files for Talisman into the Sharepoint location. 
    ##send_email_notification(subject, body)
    #send_email_notification(subject, body, attachments=None)
    subject = "Notification for Feed Files Upload.!!!"
     # <a href="https://cccgroup.sharepoint.com/:f:/s/NFSProject2/EiwE1uLSxUxKpuHS1rr0nx4BJsQONYI3sTRq4gxAq_F-mg?e=DwTtQY">
     # <a href="https://cccgroup.sharepoint.com/:f:/s/NFSProject2/Eop95_sZUGdNispj0VaSbKwBPABtAuCtBC97x3iDq_8tkg?e=0aOPbF">   New SP link
     #body = f"""
     #share link on mail https://cccgroup.sharepoint.com/:f:/s/NFSProject2/Eop95_sZUGdNispj0VaSbKwBPABtAuCtBC97x3iDq_8tkg?e=0aOPbF
    body = """
    <html>
        <body>
            <p> Dear Team,</p>
            <p>Successfully uploaded the feed files for Talisman into the SharePoint.</p>
            <p> Processed tranmittalNumber: {0} </p>
            <p>
                Click here for SharePoint location link
               
               <a href="https://cccgroup.sharepoint.com/:f:/s/NFSProject2/IgCKfef7GVBnTYrKY9FWkmysAebCeaJrf-TYVjKnwCB6QMw?e=uKAjHb">
                
                    SharePoint Link
                </a>
            </p>
            <p> Thanks, </p>
            <p> Talisman Team </p>
        </body>
    </html>
    """.format(param)

    send_email_notification(subject, body)

 #  script `param` as a command-line argument
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload CSV files to SharePoint with a specific parameter.")
    parser.add_argument("dcg_internal_trns", type=str, help="dcg_internal_trns value used for folder creation.")
    args = parser.parse_args()

    main(args.dcg_internal_trns)  # Pass argument to main()