from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import os
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="MMO – Material & Moisture Observer",
    description="Web front-end for the MMO vision model + Google Sheets logger.",
    version="0.1.0",
)

# Set this environment variable in your host, or hardcode for now (not ideal for public repos)
APPS_SCRIPT_WEBHOOK_URL = os.getenv(
    "APPS_SCRIPT_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbxXrQBud-llIMQPLgDqSq882kZ8DXLvDjAFFXMp7bl-JDEgdEs2jdW0RuB-9jNm8NSnPQ/exec"  # <-- replace this
)

# -----------------------------
# Pydantic schema for AI result
# -----------------------------

class AIResult(BaseModel):
    materials: List[str]
    damage: str
    angleDegrees: Optional[float] = None
    dimensions: Optional[str] = None
    confidence: Optional[float] = None
    summary: str


# -----------------------------
# HTML upload form
# -----------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
      <head>
        <title>MMO – Upload</title>
      </head>
      <body>
        <h2>MMO – Inspection Image Upload</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
          <label>Image:</label>
          <input type="file" name="file" accept="image/*" required><br><br>

          <label>Project / Location (optional):</label>
          <input type="text" name="project" placeholder="Site name"><br><br>

          <button type="submit">Upload & Analyze</button>
        </form>
      </body>
    </html>
    """


# -----------------------------
# Placeholder MMO "model" call
# -----------------------------

async def call_mmo_model(image_bytes: bytes) -> AIResult:
    """
    This is the brain of MMO. For now, it's a hard-coded stub
    that returns realistic-looking data in the correct shape.

    Later, you’ll replace the body of this function with an actual
    AI vision API call.
    """
    fake = {
        "materials": ["wood", "concrete"],
        "damage": "minor",
        "angleDegrees": 32.0,
        "dimensions": "Height ~3.2m, Width ~5.0m (rough estimate)",
        "confidence": 0.78,
        "summary": "Wood framing on concrete slab; minor staining at base suggesting possible water ingress."
    }
    return AIResult(**fake)


# -----------------------------
# Upload endpoint
# -----------------------------

@app.post("/upload")
async def upload(file: UploadFile = File(...), project: str = Form("")):
    # 1) Basic validation
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(
            {"error": f"File must be an image. Got content_type={file.content_type!r}"},
            status_code=400
        )

    image_bytes = await file.read()

    # 2) Run MMO model
    ai_result = await call_mmo_model(image_bytes)

    # 3) Build payload for Google Apps Script
    payload = {
        "imageName": file.filename,
        "project": project,
        "materials": ai_result.materials,
        "damage": ai_result.damage,
        "angleDegrees": ai_result.angleDegrees,
        "dimensions": ai_result.dimensions,
        "summary": ai_result.summary,
        "confidence": ai_result.confidence,
    }

    # 4) Send to Apps Script web app (Sheet logger)
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(APPS_SCRIPT_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
        except Exception as e:
            # If logging fails, still show result
            return JSONResponse(
                {
                    "status": "analysis_ok_logging_failed",
                    "error": str(e),
                    "ai_result": ai_result.dict(),
                },
                status_code=500
            )

    # 5) One-line human confirmation
    one_line = ai_result.summary
    return HTMLResponse(f"""
    <html>
      <head><title>MMO – Result</title></head>
      <body>
        <p><strong>Upload complete.</strong></p>
        <p><strong>Image:</strong> {file.filename}</p>
        <p><strong>Project:</strong> {project or "(none)"} </p>
        <p><strong>Summary:</strong> {one_line}</p>
        <p>Row logged in Google Sheet.</p>
        <a href="/">Upload another</a>
      </body>
    </html>
    """)
