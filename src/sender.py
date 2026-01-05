import os
import resend
from dotenv import load_dotenv

load_dotenv()

def send_newsletter(html_content: str, subject: str, to_email: str):
    """Sends the newsletter via Resend API."""
    
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
    
    if not api_key:
        raise ValueError("RESEND_API_KEY is missing in .env")

    print(f"📧 Sending email to {to_email}...")
    
    resend.api_key = api_key
    
    try:
        r = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        print(f"✅ Email sent successfully! ID: {r.get('id')}")
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
