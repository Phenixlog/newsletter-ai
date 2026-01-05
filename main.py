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
        
        # Save backup locally (HTML)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"newsletter_{timestamp}.html"
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML saved to {backup_file}")

        # Save for Dashboard (JSON)
        archive_dir = "archives"
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        json_content = content.model_dump_json(indent=2)
        json_file = os.path.join(archive_dir, f"news_{timestamp}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json_content)
        print(f"📂 Archive JSON saved to {json_file}")

        # NEW: Save to Database
        try:
            from src.db import save_newsletter_to_db
            save_newsletter_to_db(
                content_json=json_content,
                week_number=content.week_number,
                date_start=content.date_start,
                date_end=content.date_end
            )
            print("💾 Newsletter saved to Database.")
        except Exception as db_err:
            print(f"⚠️ Warning: Could not save to DB: {db_err}")

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
