import os
import json
import subprocess
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List
from pydantic import BaseModel
from src.db import get_all_newsletters_from_db, get_newsletter_by_id

app = FastAPI(title="AI Newsletter Dashboard")
security = HTTPBasic()

DASHBOARD_DIR = "dashboard"

# Auth Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "newsletter2026")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials."""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Models for Configuration
class NewsletterConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    theme: str
    keywords: List[str]
    tone: str = "professionnel"
    language: str = "fr"
    recipients: List[str] = []
    active: bool = True
    from_name: str = "IA Hebdo"

def load_config():
    if not os.path.exists("newsletters.json"):
        return {"newsletters": []}
    with open("newsletters.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open("newsletters.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# API Endpoints (Protected)
@app.get("/api/health")
async def health():
    """Diagnostic endpoint to check DB connection."""
    from src.db import DATABASE_URL, engine
    from sqlalchemy import text
    db_type = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    status = "Connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        status = f"Error: {str(e)}"
    
    return {
        "status": status,
        "database_type": db_type,
        "url_detected": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local_file"
    }

@app.get("/api/config")
async def get_all_configs(username: str = Depends(verify_credentials)):
    """Get all newsletter configurations."""
    return load_config()

@app.post("/api/config")
async def update_config(config: NewsletterConfig, username: str = Depends(verify_credentials)):
    """Create or update a newsletter configuration."""
    data = load_config()
    newsletters = data.get("newsletters", [])
    
    # Check if exists
    idx = next((i for i, n in enumerate(newsletters) if n["id"] == config.id), -1)
    if idx >= 0:
        newsletters[idx] = config.model_dump()
    else:
        newsletters.append(config.model_dump())
    
    data["newsletters"] = newsletters
    save_config(data)
    return {"status": "success", "config": config}

@app.get("/api/news")
async def list_news(newsletter_id: str = None, username: str = Depends(verify_credentials)):
    """List archived newsletters from Database, optionally filtered by ID."""
    newsletters = get_all_newsletters_from_db(newsletter_id=newsletter_id)
    return {
        "files": [
            {
                "id": n.id,
                "newsletter_id": n.newsletter_id,
                "week_number": n.week_number,
                "date_str": n.created_at.strftime("%Y%m%d_%H%M%S"),
                "display_date": n.created_at.strftime("%d/%m/%Y")
            } for n in newsletters
        ]
    }

@app.get("/api/news/{news_id}")
async def get_news(news_id: int, username: str = Depends(verify_credentials)):
    """Retrieve the content of a specific newsletter from DB."""
    item = get_newsletter_by_id(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    return json.loads(item.content_json)

@app.post("/api/run")
async def run_now(background_tasks: BackgroundTasks, newsletter_id: str = None, username: str = Depends(verify_credentials)):
    """Trigger the main automation script in the background."""
    def execute_script(target_id: str):
        cmd = ["python", "main.py"]
        if target_id:
            cmd.append(target_id)
        subprocess.run(cmd, check=True)

    background_tasks.add_task(execute_script, newsletter_id)
    return {"status": "started", "message": f"Automation for {newsletter_id or 'all active'} is running"}

# Cron Endpoint for Railway (no Basic Auth, uses secret key)
CRON_SECRET = os.getenv("CRON_SECRET", "")

@app.post("/api/cron/run")
async def cron_run(background_tasks: BackgroundTasks, secret: str = None):
    """
    Endpoint for Railway Cron Job.
    Protected by CRON_SECRET instead of Basic Auth for automated calls.
    """
    if not CRON_SECRET or secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    
    def execute_all_active():
        import subprocess
        subprocess.run(["python", "main.py"], check=True)
    
    background_tasks.add_task(execute_all_active)
    return {"status": "started", "message": "Cron triggered: running all active newsletters"}


# Static Files with Auth
@app.get("/")
async def protected_index(username: str = Depends(verify_credentials)):
    """Serve dashboard with auth."""
    return FileResponse(f"{DASHBOARD_DIR}/index.html")

@app.get("/{path:path}")
async def protected_static(path: str, username: str = Depends(verify_credentials)):
    """Serve static files with auth."""
    file_path = f"{DASHBOARD_DIR}/{path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
