import os
import json
import subprocess
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# API Endpoints
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

@app.get("/api/news")
async def list_news(username: str = Depends(verify_credentials)):
    """List all archived newsletters from Database."""
    newsletters = get_all_newsletters_from_db()
    return {
        "files": [
            {
                "id": n.id,
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
async def run_now(background_tasks: BackgroundTasks, username: str = Depends(verify_credentials)):
    """Trigger the main automation script in the background."""
    def execute_script():
        subprocess.run(["python", "main.py"], check=True)

    background_tasks.add_task(execute_script)
    return {"status": "started", "message": "Newsletter automation is running in background"}

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
