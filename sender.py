import os, base64, time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = "token.json"

def get_creds():
    if not os.path.exists(TOKEN_FILE):
        raise Exception("token.json not found. Authorize the app via /authorize in the Flask dashboard first.")
    return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

def send_application(to_email, job_title, company, resume_path="resume.pdf"):
    try:
        creds = get_creds()
    except Exception as e:
        print("Creds error:", e)
        return False
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEMultipart()
        body = f"Hello,\n\nPlease find attached my resume for the position of Waiter.\n\nRegards,\nSaketh Vallapudasu"
        message.attach(MIMEText(body, "plain"))
        message["to"] = to_email
        message["subject"] = f"Application for Waiter Position"
        # attach resume
        part = MIMEBase('application', 'octet-stream')
        with open(resume_path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(resume_path)}"')
        message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        time.sleep(1)
        return True
    except Exception as e:
        print("send error", e)
        return False
