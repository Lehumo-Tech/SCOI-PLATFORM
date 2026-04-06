from fastapi import APIRouter
from fastapi.responses import FileResponse
import subprocess
import os

router = APIRouter(prefix="/download", tags=["download"])

@router.get("/project-zip")
async def download_project_zip():
    """One-click download of the full SCOI project as ZIP"""
    zip_path = "/app/scoi-project.zip"

    # Regenerate the zip to capture latest changes
    subprocess.run([
        "zip", "-r", zip_path,
        "backend/server.py",
        "backend/.env",
        "backend/requirements.txt",
        "backend/routes/",
        "backend/services/",
        "backend/models/",
        "backend/utils/",
        "frontend/src/",
        "frontend/package.json",
        "frontend/tailwind.config.js",
        "frontend/postcss.config.js",
        "frontend/.env",
        "frontend/craco.config.js",
        "frontend/public/",
        "memory/",
        "-x", "*.pyc", "__pycache__/*", "node_modules/*", ".git/*"
    ], cwd="/app", capture_output=True)

    if not os.path.exists(zip_path):
        return {"error": "ZIP generation failed"}

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="scoi-project.zip"
    )
