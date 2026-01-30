import os
import requests
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def send_email_notification(subject, body):
    sender_email = "noreply@rax.net"
    receiver_email =["asaxena@rax.net"]
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
        
def upload_csv_to_datewise_folder(token_func, site_url, parent_folder_url, file_content, filename):
    ctx = ClientContext(site_url).with_access_token(token_func)
    today = datetime.now().strftime("%d-%m-%Y")
    date_folder_url = ensure_datewise_folder(ctx, parent_folder_url, today)

    try:
        target_folder = ctx.web.get_folder_by_server_relative_url(date_folder_url)
        target_folder.upload_file(filename, file_content.getvalue())
        ctx.execute_query()
        print(f"Uploaded: {filename} to {date_folder_url}")
    except Exception as e:
        print(f"Failed to upload {filename} to SharePoint: {e}")

  
#dateWise folder
def ensure_datewise_folder(ctx, parent_folder_url, date_folder_name):

    folder_url = f"{parent_folder_url}/{date_folder_name}"
    folder = ctx.web.get_folder_by_server_relative_url(parent_folder_url)
    folders = folder.folders
    ctx.load(folders)
    ctx.execute_query()

    # Check if the folder exists
    for subfolder in folders:
        if subfolder.properties["Name"] == date_folder_name:
            print(f"Folder '{date_folder_name}' already exists.")
            return folder_url

    # Folder does not exist, create it
    print(f"Creating folder '{date_folder_name}'...")
    folder.folders.add(f"{parent_folder_url}/{date_folder_name}")
    ctx.execute_query()
    print(f"Folder '{date_folder_name}' created successfully.")
    return folder_url

    # Returns a function to fetch the SharePoint token when needed.

def get_sharepoint_token_function():
    
    def fetch_token():
        tenant_id = "ce4ac0be-ae77-4bec-8e8b-464207afffde"
        client_id = "88bab5f9-402d-4e44-b9bb-2bbe3cd43a45"
        client_assertion = "eyJ4NXQiOiJwdE15RlFXL1pmanc3OWcrUGdqNFNxS2pNcFE9IiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJleHAiOjE4MjgzNDQ0NTksInN1YiI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSIsIm5iZiI6MTczMzY1MDA1OSwianRpIjoiZmJjNzRmY2MtYWQ0ZC00N2Q3LTk1M2UtNjA0Y2NlNmQ4M2ZlIiwiYXVkIjoiaHR0cHM6Ly9sb2dpbi5taWNyb3NvZnRvbmxpbmUuY29tL2NlNGFjMGJlLWFlNzctNGJlYy04ZThiLTQ2NDIwN2FmZmZkZS9vYXV0aDIvdjIuMC90b2tlbiIsImlzcyI6Ijg4YmFiNWY5LTQwMmQtNGU0NC1iOWJiLTJiYmUzY2Q0M2E0NSJ9.aJHHoEEw_otVyzBJUQ1Mki7nSrNNz-v2fRf-JC-uv1d6hRedl88ThNW3xuvxINPlexlIBMqZtDGSFve4mxnL7x1yPx4zKpAG4ROdNah4YnzpBPaEG_qTB25a8nc47PB8PyOetSBSH3uAdR2aU_3UcE-sQ0maiacDRJlpnz2CAp1iwIs3FHP5eGvKR6zCcD_unWg_D8Qe5PZZLEUM7ig6GnpFoDbKytrgW6SdAiw7_JePK67tj-tO2MGAeVbdSS3DJpwI1tAvMNho7pGl6ayGrMYdgKyY8HP9aPpVj8KQPOoiAQWK5BcNKLT6LjUdI208yrFKW01m2rD9vH7VaGRkog"  # Replace with your dynamically generated assertion
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

#wrapper class for tokenType and accessToken
class Token:

    def __init__(self, token_str):
        self.tokenType = "Bearer"  # Standard token type
        self.accessToken = token_str
def main():
    site_url = "https://raxgroup.sharepoint.com/sites/NFSProject2"
    source_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Isometric_Files"
    local_input_dir = 'D:/ismometricFiles/zipFiles'
    local_output_dir = 'D:/ismometricFiles'

    token_func = get_sharepoint_token_function()
    print("Acquired SharePoint token function.")

            
            
if __name__ == "__main__":
    main()


