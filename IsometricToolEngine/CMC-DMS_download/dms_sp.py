import psycopg2
import requests
import os
import io
import shutil
import zipfile
import argparse
from sharePointConnectionTest import upload_csv_to_datewise_folder, get_sharepoint_token_function


#This script was used to download metadata files from S3.
##Now, we are downloading the files instead of ZIP/Native.
#Later, instead of downloading, we will process them through an alternative method.

# Database configuration
db_config = {
    "host": "192.168.22.54",
    "database": "document-manage",
    "user": "postgres",
    "password": "sa",
    "port": "5432",
}

# Path 4 downloading files
download_dir = r"D:\ismometricFiles\zipFiles"
if os.path.exists(download_dir):
    shutil.rmtree(download_dir)
    os.makedirs(download_dir, exist_ok=True)

#cleaning the directory
#if os.path.exists(download_dir):
#   shutil.rmtree(download_dir)
#  os.makedirs(download_dir, exist_ok=True)

#fetches result from DB
def fetch_query_results(query, params=None):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching query results: {e}")
        return []

# Fetch files and zip file.
# due to native/zip is not available in DMS.
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure a requests session with retries
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def fetch_and_zip_files(doc_id, dcg_internal_trns):
    api_url = f"https://dms.rax.com.qa/nfs-doc-manage-api/api/mail/files?docId={doc_id}"
    print("api_url  ###", api_url)
    response = session.get(api_url, timeout=60, verify=True)

    print(" response ####", response.status_code)
    if response.status_code == 200:
        files = response.json()  # List of file metadata (filename and link)
        zip_file_name = f"{doc_id}_{dcg_internal_trns}_files.zip"
        zip_file_path = os.path.join(download_dir, zip_file_name)

        # Create a zip file
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for file_data in files:
                filename = file_data.get("filename")
                file_url = file_data.get("link")

                print(f"Downloading file: {filename}")
                try:
                    file_response = session.get(file_url, timeout=60, verify=True)
                    if file_response.status_code == 200:
                        # Save the file temporarily
                        file_path = os.path.join(download_dir, filename)
                        with open(file_path, "wb") as temp_file:
                            temp_file.write(file_response.content)

                        # Add the file to the zip
                        zip_file.write(file_path, arcname=filename)

                        # Remove the temporary file
                        os.remove(file_path)
                    else:
                        print(f"Failed to download file: {filename} (Status Code: {file_response.status_code})")
                except requests.exceptions.SSLError as ssl_err:
                    print(f"SSL error downloading {filename}: {ssl_err}")
                except Exception as e:
                    print(f"Error downloading {filename}: {e}")

        print(f"Packaged files into zip: {zip_file_path}")
        return zip_file_path
    else:
        print(f"Failed to fetch file metadata for docId {doc_id} (Status Code: {response.status_code})")
        return None

# Upload the generated zip  to SharePoint.
def upload_zip_to_sharepoint(zip_file_path, token_func, site_url, parent_folder_url):
    if not zip_file_path or not os.path.exists(zip_file_path):
        print("No zip file found to upload.")
        return

    filename = os.path.basename(zip_file_path)
    with open(zip_file_path, "rb") as zip_file:
        upload_csv_to_datewise_folder(token_func, site_url, parent_folder_url, zip_file, filename)
        print(f"Uploaded zip file: {filename} to SharePoint")

    # Cleanup: Remove the zip file after uploading
    #os.remove(zip_file_path)
    #print(f"Deleted local zip file: {zip_file_path}")
    
#Main Trigger point  ..Main FUNCTION  

def main(dcg_internal_trns):
    
    #  query without Native :26January2025
    documents_query = """
        SELECT id, file_name 
        FROM documents 
        WHERE custom_form_params::jsonb->>'dcg_internal_trns' = %s
    """
    params = (dcg_internal_trns,)
    documents = fetch_query_results(documents_query, params)

    if not documents:
        print(f"Given transmittal: {dcg_internal_trns} is not available in the table.")
        return

    # SharePoint credentials
    token_func = get_sharepoint_token_function()
    site_url = "https://raxgroup.sharepoint.com/sites/NFSProject2"
    parent_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Isometric_Files"

    # Process documents
    for doc_id, file_name in documents:
        # Fetch and zip files
        zip_file_path = fetch_and_zip_files(doc_id, dcg_internal_trns)
        if zip_file_path:
            # Upload the zip file to SharePoint
            print("upload to share point....")
            #upload_zip_to_sharepoint(zip_file_path, token_func, site_url, parent_folder_url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process document files and upload to SharePoint.")
    parser.add_argument("dcg_internal_trns", type=str, help="The dcg_internal_trns value to query.")
    args = parser.parse_args()
    main(args.dcg_internal_trns)
