
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd

pmsisohFilePath = 'D:/ismometricFiles/FeedFiles/Output_PMSISOH.csv'
output_csv_file = 'D:/ismometricFiles/FeedFiles/mailAttach.csv'


def send_email_notification(subject, body):
    sender_email = "noreply@rax.net"
    receiver_email =["asaxena@rax.net","skassab@rax.net","msantina@rax.net" ,"audwan@rax.net","sjoy@rax.net"]   
    #msg = MIMEMultipart()  ::30Dec
    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)
    msg['Subject'] = subject
    #msg.attach(MIMEText(body, 'plain'))
    html_part = MIMEText(body, "html")
    msg.attach(html_part)
    try:
        server = smtplib.SMTP('mailhost.rax.net', 25)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email notification sent successfully.")
    except Exception as e:
        print("Failed to send email notification:", e)
        
        
#Attachment with ISo ,Rev
def readAttachmentDF():
    # Read the CSV file
    df = pd.read_csv(pmsisohFilePath)
    
    # reading the columns index from ISOH file
    # Select columns 0 (Isono) and 39 (RevNo)
    selected_columns = df.iloc[:, [0, 39]]  
    
    # Add a serial number column (starting from 1)
    selected_columns.insert(0, 'srno', range(1, len(selected_columns) + 1))
    # debugging purpose
    print("Selected Columns with Serial Number:\n", selected_columns)
    
    # Write to CSV file
    selected_columns.to_csv(output_csv_file, index=False)    