import os
import json
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from pydantic import BaseModel
from src.db import get_all_newsletters_from_db, get_newsletter_by_id

app = FastAPI(title="AI Newsletter Dashboard")

DASHBOARD_DIR = "dashboard"

# API Endpoints
@app.get("/api/news")
async def list_news():
    """List all archived newsletters from Database."""
    newsletters = get_all_newsletters_from_db()
    # Return a simplified list for the sidebar
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
async def get_news(news_id: int):
    """Retrieve the content of a specific newsletter from DB."""
    item = get_newsletter_by_id(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    return json.loads(item.content_json)

@app.post("/api/run")
async def run_now(background_tasks: BackgroundTasks):
    """Trigger the main automation script in the background."""
    def execute_script():
        subprocess.run(["python", "main.py"], check=True)

    background_tasks.add_task(execute_script)
    return {"status": "started", "message": "Automation script is running in background"}

# Static Files
if os.path.exists(DASHBOARD_DIR):
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
