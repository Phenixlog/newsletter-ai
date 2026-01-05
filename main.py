import os
import sys
from dotenv import load_dotenv
from src.collector import AINewsCollector
from src.generator import generate_html
from src.sender import send_newsletter
from datetime import datetime

# Load env vars
load_dotenv()

def main():
    print("🚀 STARTING AI NEWSLETTER AUTOMATION")
    print("====================================")
    
    # Check Env Vars
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ CRITICAL: ANTHROPIC_API_KEY missing in .env")
        return
    if not os.getenv("RESEND_API_KEY"):
        print("❌ CRITICAL: RESEND_API_KEY missing in .env")
        return
    if not os.getenv("TO_EMAIL"):
        print("❌ CRITICAL: TO_EMAIL missing in .env")
        return

    try:
        # STEP 1: COLLECT & ANALYZE
        print("\n📡 STEP 1: Collection & Analysis...")
        collector = AINewsCollector()
        content = collector.collect_and_analyze()
        
        print(f"✅ Content generated: {content.highlight.name}")

        # STEP 2: GENERATE HTML
        print("\n🎨 STEP 2: Generating HTML...")
        html = generate_html(content)
        
        # Save backup locally
        backup_file = f"newsletter_{datetime.now().strftime('%Y%m%d')}.html"
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML saved to {backup_file}")

        # STEP 3: SEND EMAIL
        print("\n📧 STEP 3: Sending Email...")
        subject = f"🤖 IA Hebdo #{content.week_number} : {content.highlight.name}"
        to_email = os.getenv("TO_EMAIL")
        
        send_newsletter(html, subject, to_email)
        
        print("\n🎉 MISSION ACCOMPLISHED! Newsletter sent.")
        
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
