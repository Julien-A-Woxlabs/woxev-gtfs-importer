from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import zipfile
import io
import requests
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

XANO_API_KEY = os.getenv("XANO_API_KEY")
XANO_BASE_URL = os.getenv("XANO_BASE_URL")

@app.post("/upload/GTFS_import")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    version_name: str = Form(...)
):
    try:
        print(f"DEBUG START - company: {company_id}, version: {version_name}, base_url: {XANO_BASE_URL}")

        # 1. Créer version
        version_payload = {
            "name": version_name,
            "import_date": datetime.now().isoformat(),
            "status": "active",
            "company_id": company_id
        }
        
        version_res = requests.post(f"{XANO_BASE_URL}/gtfs_versions", json=version_payload, headers={
            "Authorization": f"Bearer {XANO_API_KEY}",
            "Content-Type": "application/json"
        })

        print(f"DEBUG Version status: {version_res.status_code} - {version_res.text[:300]}")

        if version_res.status_code != 200:
            return JSONResponse(status_code=400, content={"error": version_res.text})

        version_id = version_res.json().get("id")
        if not version_id:
            return JSONResponse(status_code=400, content={"error": "No id returned from gtfs_versions"})

        # Pour l'instant on arrête là pour voir si on passe cette étape
        return {
            "message": "Version créée avec succès",
            "version_id": version_id
        }

    except Exception as e:
        print("EXCEPTION:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
