import os
import requests
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse

def get_sharepoint_token():
    tenant_id = "ce4ac0be-ae77-4bec-8e8b-464207afffde"
    client_id = "88bab5f9-402d-4e44-b9bb-2bbe3cd43a45"
    client_assertion = "eyJ4NXQiOiJwdE15RlFXL1pmanc3OWcrUGdqNFNxS2pNcFE9IiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJleHAiOjE4MjgzNDQ0NTksInN1YiI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSIsIm5iZiI6MTczMzY1MDA1OSwianRpIjoiZmJjNzRmY2MtYWQ0ZC00N2Q3LTk1M2UtNjA0Y2NlNmQ4M2ZlIiwiYXVkIjoiaHR0cHM6Ly9sb2dpbi5taWNyb3NvZnRvbmxpbmUuY29tL2NlNGFjMGJlLWFlNzctNGJlYy04ZThiLTQ2NDIwN2FmZmZkZS9vYXV0aDIvdjIuMC90b2tlbiIsImlzcyI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSJ9.aJHHoEEw_otVyzBJUQ1Mki7nSrNNz-v2fRf-JC-uv1d6hRedl88ThNW3xuvxINPlexlIBMqZtDGSFve4mxnL7x1yPx4zKpAG4ROdNah4YnzpBPaEG_qTB25a8nc47PB8PyOetSBSH3uAdR2aU_3UcE-sQ0maiacDRJlpnz2CAp1iwIs3FHP5eGvKR6zCcD_unWg_D8Qe5PZZLEUM7ig6GnpFoDbKytrgW6SdAiw7_JePK67tj-tO2MGAeVbdSS3DJpwI1tAvMNho7pGl6ayGrMYdgKyY8HP9aPpVj8KQPOoiAQWK5BcNKLT6LjUdI208yrFKW01m2rD9vH7VaGRkog"
    sharepoint_scope = "https://raxgroup.sharepoint.com/.default"
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "scope": sharepoint_scope,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    print("response ::",response)
    return response.json().get("access_token")

def download_zip_files_from_sharepoint(token_func, site_url, folder_url, local_dir):
    current_date = datetime.now().strftime("%d-%m-%Y")
    date_folder_url = f"{folder_url}/{current_date}"
    
    ctx = ClientContext(site_url).with_access_token(token_func)
    folder = ctx.web.get_folder_by_server_relative_url(date_folder_url)
    files = folder.files
    ctx.load(files)
    ctx.execute_query()

    os.makedirs(local_dir, exist_ok=True)

    for file in files:
        if file.properties["Name"].endswith(".zip"):
            local_file_path = os.path.join(local_dir, file.properties["Name"])
            with open(local_file_path, "wb") as local_file:
                file_response = File.open_binary(ctx, file.serverRelativeUrl)
                local_file.write(file_response.content)
            print(f"Downloaded: {file.properties['Name']} to {local_file_path}")

def send_email_notification(subject, body):
    sender_email = "noreply@rax.net"
    receiver_email =["asaxena@rax.net"]#,"skassab@rax.net","msantina@rax.net"]  
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('mailhost.rax.net', 25)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email notification sent successfully.")
    except Exception as e:
        print("Failed to send email notification:", e)
        
def upload_csv_to_datewise_folder(token_func, site_url, parent_folder_url, local_file_path, param):
    """
    Upload a CSV file to the date-wise folder in SharePoint.
    """
    ctx = ClientContext(site_url).with_access_token(token_func)
    subject = f"Notification for Feed Files Upload.!!!"
    body = f"Successfully uploaded the feed files for Talisman into the Sharepoint location. "
    # Generate today's date
    #today = datetime.now().strftime("%Y-%m-%d")
    today = datetime.now().strftime("%d-%m-%Y")
    
    transmittal_folder_url = ensure_datewise_folder(ctx, parent_folder_url, today, param)  # Ensure transmittal folder exists
   # date_folder_url = ensure_datewise_folder(ctx, parent_folder_url, today, param)

    # Upload the file to the date-wise folder
    file_name = os.path.basename(local_file_path)
    try:
        with open(local_file_path, "rb") as file_content:
            target_folder = ctx.web.get_folder_by_server_relative_url(transmittal_folder_url)
            target_folder.upload_file(file_name, file_content.read())
            ctx.execute_query()
        print(f"Uploaded: {file_name} to {transmittal_folder_url}")
       
        #send_email_notification(subject, body)
    except Exception as e:
        print(f"Failed to upload {file_name} to SharePoint: {e}")
  
#dateWise folder
def ensure_datewise_folder(ctx, parent_folder_url, date_folder_name, param):
    """
    Ensure that both the date-wise folder (DD-MM-YYYY) and the transmittal folder exist in SharePoint.
    """
    date_folder_url = f"{parent_folder_url}/{date_folder_name}"
    transmittal_folder_url = f"{date_folder_url}/{param}"  # Folder for the transmittal number

    # Load the parent folder
    folder = ctx.web.get_folder_by_server_relative_url(parent_folder_url)
    folders = folder.folders
    ctx.load(folders)
    ctx.execute_query()

    # Check if the date-wise folder exists
    date_folder_exists = any(subfolder.properties["Name"] == date_folder_name for subfolder in folders)

    if not date_folder_exists:
        print(f"Creating date folder: {date_folder_name} in {parent_folder_url}...")
        folder.folders.add(date_folder_url)
        ctx.execute_query()

    # Load the date folder and check if the transmittal folder exists
    date_folder = ctx.web.get_folder_by_server_relative_url(date_folder_url)
    transmittal_folders = date_folder.folders
    ctx.load(transmittal_folders)
    ctx.execute_query()

    transmittal_folder_exists = any(subfolder.properties["Name"] == param for subfolder in transmittal_folders)

    if not transmittal_folder_exists:
        print(f"Creating transmittal folder: {param} inside {date_folder_url}...")
        date_folder.folders.add(transmittal_folder_url)
        ctx.execute_query()

    print(f"Using folder path: {transmittal_folder_url}")
    return transmittal_folder_url  # Return the transmittal folder path


    # Returns a function to fetch the SharePoint token when needed.

def get_sharepoint_token_function():
    
    def fetch_token():
        tenant_id = "ce4ac0be-ae77-4bec-8e8b-464207afffde"
        client_id = "88bab5f9-402d-4e44-b9bb-2bbe3cd43a45"
        client_assertion = "eyJ4NXQiOiJwdE15RlFXL1pmanc3OWcrUGdqNFNxS2pNcFE9IiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJleHAiOjE4MjgzNDQ0NTksInN1YiI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSIsIm5iZiI6MTczMzY1MDA1OSwianRpIjoiZmJjNzRmY2MtYWQ0ZC00N2Q3LTk1M2UtNjA0Y2NlNmQ4M2ZlIiwiYXVkIjoiaHR0cHM6Ly9sb2dpbi5taWNyb3NvZnRvbmxpbmUuY29tL2NlNGFjMGJlLWFlNzctNGJlYy04ZThiLTQ2NDIwN2FmZmZkZS9vYXV0aDIvdjIuMC90b2tlbiIsImlzcyI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSJ9.aJHHoEEw_otVyzBJUQ1Mki7nSrNNz-v2fRf-JC-uv1d6hRedl88ThNW3xuvxINPlexlIBMqZtDGSFve4mxnL7x1yPx4zKpAG4ROdNah4YnzpBPaEG_qTB25a8nc47PB8PyOetSBSH3uAdR2aU_3UcE-sQ0maiacDRJlpnz2CAp1iwIs3FHP5eGvKR6zCcD_unWg_D8Qe5PZZLEUM7ig6GnpFoDbKytrgW6SdAiw7_JePK67tj-tO2MGAeVbdSS3DJpwI1tAvMNho7pGl6ayGrMYdgKyY8HP9aPpVj8KQPOoiAQWK5BcNKLT6LjUdI208yrFKW01m2rD9vH7VaGRkog" 
        sharepoint_scope = "https://raxgroup.sharepoint.com/.default"
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "scope": sharepoint_scope,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raise an error for bad responses
        
        token_str = response.json().get("access_token")
        print("Token acquired successfully.")
        return Token(token_str)

    return fetch_token


def sort_sharepoint_files_api():
    # SharePoint details
    site_url = "https://raxgroup.sharepoint.com/sites/NFSProject2"
    source_folder_url = "/sites/NFSProject2/Shared Documents/02 - Talisman Files/Talisman_Files"  # Fixed typo in folder name

    # Get the token
    token_func = get_sharepoint_token_function()
    token = token_func().accessToken  # Access the token string from the Token object

    # Set up headers for the SharePoint REST API
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose"
    }

    # Construct the API endpoint to list files in the folder
    api_url = f"{site_url}/_api/web/GetFolderByServerRelativeUrl('{source_folder_url}')/Files"

    # Fetch the files
    print("Fetching files from SharePoint...")
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()

    # Parse the response
    files_data = response.json().get("d", {}).get("results", [])

    # Extract file details and sort by Modified date (newer to older)
    files_list = []
    for file in files_data:
        file_name = file["Name"]
        modified_time = file["TimeLastModified"]
        # Convert the modified time to a datetime object for sorting
        modified_dt = datetime.strptime(modified_time, "%Y-%m-%dT%H:%M:%SZ")
        files_list.append({"name": file_name, "modified": modified_dt})

    # Sort files by modified date (newer to older)
    sorted_files = sorted(files_list, key=lambda x: x["modified"], reverse=True)  # Changed to newer to older

    # Print the sorted files for verification
    print("Sorted files (newer to older):")
    for file in sorted_files:
        print(f"File: {file['name']}, Modified: {file['modified']}")

    return sorted_files


#wrapper class for tokenType and accessToken
class Token:

    def __init__(self, token_str):
        self.tokenType = "Bearer"  # Standard token type
        self.accessToken = token_str
def main(param):
    site_url = "https://raxgroup.sharepoint.com/sites/NFSProject2"
    #param = (param)
    print("param :",param)

    #parent_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Talisman_Files"
    parent_folder_url = "/sites/NFSProject2/NFS_Data_Hub/03- rax_Workpacks/02- Cloud Apps Data/03-Talisman/02- Talisman and PCF Staging Export"
    source_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Isometric_Files"


    local_input_dir = 'D:/ismometricFiles/zipFiles'
    local_output_dir = 'D:/ismometricFiles'

    token_func = get_sharepoint_token_function()
    print("Acquired SharePoint token function.")

    # Step 1: Download ZIP files
    download_zip_files_from_sharepoint(token_func, site_url, source_folder_url, local_input_dir)

    pcf_zip_dir = 'D:/ismometricFiles/pcfZipFiles'
    # Upload CSV files to the date-wise folder
    output_csvs = [
        #f"{local_output_dir}/FeedFiles/Output_PMSISOH.csv",
        #f"{local_output_dir}/FeedFiles/Output_PMSSPL.csv",
        #f"{local_output_dir}/FeedFiles/Output_PMSJNTH.csv",
        #f"{local_output_dir}/FeedFiles/Output_PMSISOD.csv",
        #f"{local_output_dir}/FeedFiles/Output_PMSMAT.csv",
        #f"{local_output_dir}/FeedFiles/Output_FLANGE.csv",
        f"{pcf_zip_dir}/pcfs.zip",
        
    ]

    for csv_file in output_csvs:
        if os.path.exists(csv_file):
            upload_csv_to_datewise_folder(token_func, site_url, parent_folder_url, csv_file, param)
            
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process document files and upload to SharePoint.")
    parser.add_argument("dcg_internal_trns", type=str, help="dcg_internal_trns value used for Folder creation.")
    args = parser.parse_args()
    main(args.dcg_internal_trns)    


