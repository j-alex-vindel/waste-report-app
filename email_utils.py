import smtplib
import ssl
import os
import re
from email.message import EmailMessage
import streamlit as st

def validate_email(email):
    """Simple email validation using regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, email) is not None

def get_email_config():
    """
    Load email credentials from Streamlit secrets or environment variables.
    Supports local development and cloud deployment.
    """
    try:
        return {
            "sender_email": st.secrets["email"]["address"],
            "sender_password": st.secrets["email"]["password"],
            "smtp_server": st.secrets["email"].get("smtp_server", "smtp.gmail.com"),
            "smtp_port": int(st.secrets["email"].get("smtp_port", 587))
        }
    except (KeyError, AttributeError):
        return {
            "sender_email": os.getenv("EMAIL_ADDRESS"),
            "sender_password": os.getenv("EMAIL_PASSWORD"),
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", 587))
        }

def send_email_with_reports(sender_email, sender_password, recipient_email, subject, body, pdf_paths, smtp_server="smtp.gmail.com", smtp_port=587):
    """
    Sends an email with the given PDF attachments to the recipient.
    """
    try:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(body)

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                continue
            with open(pdf_path, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(pdf_path)
                msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email failed: {e}")
        return False
