import os
import resend
from dotenv import load_dotenv

load_dotenv()

def send_newsletter(html_content: str, subject: str, to_email: str):
    """Sends the newsletter via Resend API. Supports multiple recipients via comma-separated string."""
    
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
    
    if not api_key:
        raise ValueError("RESEND_API_KEY is missing in .env")

    # Handle multiple recipients
    if isinstance(to_email, str) and "," in to_email:
        recipients = [e.strip() for e in to_email.split(",") if e.strip()]
    else:
        recipients = to_email

    print(f"📧 Sending email to {recipients}...")
    
    resend.api_key = api_key
    
    try:
        r = resend.Emails.send({
            "from": from_email,
            "to": recipients,
            "subject": subject,
            "html": html_content
        })
        if hasattr(r, "get"):
             print(f"✅ Email sent successfully! ID: {r.get('id')}")
        else:
             print(f"✅ Email sent successfully!")
        return r
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise

if __name__ == "__main__":
    # Test sending the preview.html
    try:
        with open("preview.html", "r", encoding="utf-8") as f:
            html = f.read()
            
        test_email = os.getenv("TO_EMAIL")
        if not test_email:
            print("⚠️ TO_EMAIL not found in .env, checking CLI args or default...")
            # For safety, ask user to put it in env
            raise ValueError("Please set TO_EMAIL in .env to test sending.")
            
        send_newsletter(
            html_content=html, 
            subject="🔥 [TEST] IA Hebdo : GPT-5 et Impact Business", 
            to_email=test_email
        )
    except Exception as e:
        print(f"Skipping send test: {e}")
