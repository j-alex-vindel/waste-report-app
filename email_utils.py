import smtplib
import ssl
from email.message import EmailMessage
import os
import re

def send_email_with_reports(sender_email=None, sender_password=None, recipient_email=None, subject=None, body=None, pdf_paths=None):
    """
    Send an email with one or more PDF attachments.
    
    Parameters:
        sender_email (str): The app email address (e.g., your Gmail).
        sender_password (str): App-specific password or your email password.
        recipient_email (str): The recipient’s email address.
        subject (str): Subject line for the email.
        body (str): The plain-text body message.
        pdf_paths (list): List of full paths to PDF files to attach.
    """

    # Prepare email message
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach PDFs
    attached_any = False
    for path in pdf_paths:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                file_data = f.read()
                filename = os.path.basename(path)
                msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=filename)
                attached_any = True

    if not attached_any:
        raise FileNotFoundError("No valid report PDFs were provided.")

    # Send the email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email: {e}")

def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None
