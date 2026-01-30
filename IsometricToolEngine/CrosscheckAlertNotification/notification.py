import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import shutil

def send_email_notification(subject, body, attachments=None):
    sender_email = "noreply@rax.net"
    receiver_email = ["asaxena@rax.net","malatif@rax.net"]

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)
    msg['Subject'] = subject

    # Attach the body to the email
    msg.attach(MIMEText(body, 'plain'))

    # Attach files if provided
    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):  # Check if the file exists
                try:
                    with open(file_path, 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                        msg.attach(part)
                except Exception as e:
                    print(f"Failed to attach file {file_path}: {e}")
            else:
                print(f"File not found: {file_path}")

    # Send the email
    try:
        # Set up the server
        server = smtplib.SMTP('mailhost.rax.net', 25)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email notification sent successfully.")
    except Exception as e:
        print("Failed to send email notification:", e)


def notify_on_discrepancies():
    logs_dir = "logs/"
    # Clear logs directory before running checks
    #if os.path.exists(logs_dir):
     #   shutil.rmtree(logs_dir)
    #os.makedirs(logs_dir, exist_ok=True)
    # testingto generate fresh CSVs
    #from cross_checks import run_cross_checks
    #run_cross_checks()
    discrepancies = [f for f in os.listdir(logs_dir) if f.endswith(".csv")]
    if discrepancies:
        body = "The following discrepancies were found:\n\n"
        body += "\n".join(discrepancies)
        body += "\n\nPlease find the detailed logs attached.\n\n\n"
        body += "\nThanks & regards,\n\n"
        body += "Talisman Support team."
        attachments = [os.path.join(logs_dir, file) for file in discrepancies]
        send_email_notification("Cross-Check Discrepancies Found", body, attachments)
    else:
        print("No discrepancies found.")
        body = "No discrepancies found:\n\n"
        body += "\nThanks & regards,\n\n"
        body += "Talisman Support team."
        send_email_notification("No discrepancies found in cross-check script.", body)
if __name__ == "__main__":
    notify_on_discrepancies()
