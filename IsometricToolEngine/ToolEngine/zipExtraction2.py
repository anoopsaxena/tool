import os
import zipfile
from collections import defaultdict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_notification(subject, body):
    sender_email = "noreply@ccc.net"
    receiver_email = ["asaxena@ccc.net"]  # Add other recipients as needed
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

def recursively_find_files(directory, extensions):
    """ Recursively search for files with mentioned extensions. """
    found_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                found_files.append(os.path.join(root, file))
    return found_files

def unzip_and_validate(input_directory, required_extensions=(".pcf", ".txt")):
    """
    Unzip and validate folders for required files with specific extensions.
    """
    extracted_folders = []
    missing_folders = []

    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.zip'):
                zip_path = os.path.join(root, file)
                extract_folder = zip_path.replace('.zip', '')

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)
                    extracted_folders.append(extract_folder)

                # Recursively validate files with required extensions
                found_files = recursively_find_files(extract_folder, required_extensions)
                if not found_files:
                    missing_folders.append(extract_folder)

    # Send a single email if any folders are missing required files
    if missing_folders:
        missing_folders_list = "\n".join(missing_folders)
        subject = "Missing PCF Files in Extracted Folders"
        body = f"The following extracted folders are missing required PCF files:\n\n{missing_folders_list}"
        send_email_notification(subject, body)
        print(f"Missing files in the following folders:\n{missing_folders_list}")

    # Return only folders with valid files
    valid_folders = [folder for folder in extracted_folders if folder not in missing_folders]
    return valid_folders
