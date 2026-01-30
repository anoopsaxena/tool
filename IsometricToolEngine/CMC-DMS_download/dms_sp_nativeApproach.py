import psycopg2
import requests
import io
import sys
import os
import argparse
from sharePointConnectionTest import upload_csv_to_datewise_folder, get_sharepoint_token_function


utils_path = os.path.abspath(r"D:\ismometricFiles\IsometricToolEngine\ToolEngine\utils")
if utils_path not in sys.path:
    sys.path.append(utils_path)
from NotificationScript import send_email_notification

# Database configuration
db_config = {
    "host": "192.168.22.54",
    "database": "document-manage",
    "user": "postgres",
    "password": "sa",
    "port": "5432",
}

# Function to execute a query and fetch results
def fetch_query_results(query, params=None):
    try:
        # Connect to the PostgreSQL database
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

# Function to download from API and upload to SharePoint
def download_and_upload_file(doc_id, token_func, site_url, parent_folder_url):
    api_url = f"https://dms.ccc.com.qa/nfs-doc-manage-api/api/mail/file?docId={doc_id}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        filename = data.get("filename")
        file_url = data.get("link")
        
        # Fetch file content
        file_response = requests.get(file_url)
        if file_response.status_code == 200:
            file_content = io.BytesIO(file_response.content)
            # Upload to SharePoint
            upload_csv_to_datewise_folder(token_func, site_url, parent_folder_url, file_content, filename)
            print(f"Uploaded: {filename} to SharePoint")
        else:
            print(f"Failed to download file: {file_url} (Status Code: {file_response.status_code})")
    else:
        print(f"Failed to fetch data for docId {doc_id} (Status Code: {response.status_code})")

# Main function
def main(dcg_internal_trns):
    # Handling leading/trailing spaces
    dcg_internal_trns = dcg_internal_trns.strip()
    # Query for documents
    documents_query = """
        SELECT id, file_name 
        FROM documents 
        WHERE custom_form_params::jsonb->>'dcg_internal_trns' = %s
        AND documents_number LIKE %s
    """
    params = (dcg_internal_trns, '%Native')
    documents = fetch_query_results(documents_query, params)
    #{dcg_internal_trns}
    if not documents:
        print(f" Given transmittal:  is Not available in table.")
        subject = "Transmittal Notification for Processing Spool Files!!!"
        body = "Transmittal not found."
        send_email_notification(subject, body)
        #send_notification()
        return
         
    # Initialize SharePoint credentials
    token_func = get_sharepoint_token_function()
    site_url = "https://cccgroup.sharepoint.com/sites/NFSProject2"
    #parent_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Talisman_Files"
    parent_folder_url = "/sites/NFSProject2/Shared Documents/02- Talisman Files/Isometric_Files"

    # Process documents
    doc_ids = []
    for doc_id, file_name in documents:
        isometric_query = """
            SELECT * 
            FROM isometric_tracker 
            WHERE file_name LIKE %s
        """
        isometric_results = fetch_query_results(isometric_query, (f"{file_name}%",))
        if isometric_results:
            doc_ids.append(doc_id)

    # Download and upload files directly
    for doc_id in doc_ids:
        download_and_upload_file(doc_id, token_func, site_url, parent_folder_url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process document files and upload to SharePoint.")
    parser.add_argument("dcg_internal_trns", type=str, help="The dcg_internal_trns value passing to query')")
    args = parser.parse_args()
    main(args.dcg_internal_trns)