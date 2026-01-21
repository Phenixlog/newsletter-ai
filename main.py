import os
import sys
import json
from dotenv import load_dotenv
from src.collector import AINewsCollector
from src.generator import generate_html
from src.sender import send_newsletter
from datetime import datetime

# Load env vars
load_dotenv()

def load_newsletters_config():
    config_path = "newsletters.json"
    if not os.path.exists(config_path):
        print(f"⚠️ Warning: {config_path} not found. Using defaults.")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("newsletters", [])

def run_newsletter(news_config: dict):
    news_id = news_config.get("id", "unknown")
    news_name = news_config.get("name", "IA Hebdo")
    
    print(f"\n🚀 PROCESSING: {news_name} ({news_id})")
    print("-" * 40)
    
    try:
        # STEP 1: COLLECT & ANALYZE
        print("📡 STEP 1: Collection & Analysis...")
        collector = AINewsCollector(config=news_config)
        content = collector.collect_and_analyze()
        print(f"✅ Content generated: {content.highlight.name}")

        # STEP 2: GENERATE HTML
        print("🎨 STEP 2: Generating HTML...")
        html = generate_html(content)
        
        # Save backup locally (HTML)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = os.path.join(backup_dir, f"newsletter_{news_id}_{timestamp}.html")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML saved to {backup_file}")

        # Save for Dashboard (JSON)
        archive_dir = "archives"
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        json_content = content.model_dump_json(indent=2)
        json_file = os.path.join(archive_dir, f"news_{news_id}_{timestamp}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json_content)
        print(f"📂 Archive JSON saved to {json_file}")

        # Save to Database
        try:
            from src.db import save_newsletter_to_db
            save_newsletter_to_db(
                content_json=json_content,
                newsletter_id=news_id,
                week_number=content.week_number,
                date_start=content.date_start,
                date_end=content.date_end
            )
            print("💾 Newsletter saved to Database.")
        except Exception as db_err:
            print(f"⚠️ Warning: Could not save to DB: {db_err}")

        # STEP 3: SEND EMAIL
        print("📧 STEP 3: Sending Email...")
        # Get from name if exists, else default
        from_name = news_config.get("from_name", "IA Hebdo")
        subject = f"🤖 {from_name} #{content.week_number} : {content.highlight.name}"
        
        # Use config's recipients if available, else .env
        config_recipients = news_config.get("recipients")
        if config_recipients:
            to_email = ",".join(config_recipients)
        else:
            to_email = os.getenv("TO_EMAIL")
            
        if not to_email:
            print(f"❌ Error: No recipients found for {news_id}")
            return False

        send_newsletter(html, subject, to_email)
        print(f"✅ [{news_id}] Finished successfully.")
        return True

    except Exception as e:
        print(f"💥 ERROR processing {news_id}: {e}")
        return False

def main():
    print("🚀 AI NEWSLETTER MULTI-ENGINE")
    print("==============================")
    
    # Check Critical Env Vars
    if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("RESEND_API_KEY"):
        print("❌ CRITICAL: API Keys missing in .env")
        return

    configs = load_newsletters_config()
    
    # Handle command line arg for specific newsletter ID
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if target_id:
        target_config = next((c for c in configs if c["id"] == target_id), None)
        if target_config:
            run_newsletter(target_config)
        else:
            print(f"❌ Error: Newsletter ID '{target_id}' not found in config.")
    else:
        # Run all active newsletters
        print(f"📋 Running all active newsletters...")
        for config in configs:
            if config.get("active", True):
                run_newsletter(config)

if __name__ == "__main__":
    main()
