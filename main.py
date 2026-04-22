from fastapi import FastAPI, File, UploadFile, Form
import zipfile
import io
import requests
import os
from datetime import datetime

app = FastAPI()

XANO_API_KEY = os.getenv("XANO_API_KEY")
XANO_BASE = os.getenv("XANO_BASE_URL")  # ex: https://mvpw34-42.xano.io/api:xxxxx

headers = {
    "Authorization": f"Bearer {XANO_API_KEY}",
    "Content-Type": "application/json"
}

@app.post("/import-gtfs")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: int = Form(...),
    version_name: str = Form(...)
):
    # 1. Créer la version GTFS
    version_payload = {
        "name": version_name,
        "import_date": datetime.now().isoformat(),
        "status": "active",
        "company_id": company_id
    }
    version_res = requests.post(f"{XANO_BASE}/gtfs_versions", json=version_payload, headers=headers)
    version_id = version_res.json()["id"]

    content = await file.read()
    created_files = []

    with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
        for filename in zip_ref.namelist():
            if filename.endswith(".txt"):
                file_content = zip_ref.read(filename)
                
                # Upload du fichier vers Xano
                files = {"file": (filename, file_content, "text/plain")}
                upload_res = requests.post(f"{XANO_BASE}/file", files=files, headers={"Authorization": f"Bearer {XANO_API_KEY}"})
                file_url = upload_res.json()["url"]
                
                # Créer l'enregistrement gtfs_files
                file_payload = {
                    "company_id": company_id,
                    "gtfs_version_id": version_id,
                    "file_type": filename.replace(".txt", ""),
                    "file_url": file_url,
                    "original_name": filename,
                    "uploaded_at": datetime.now().isoformat(),
                    "status": "not_started"
                }
                file_res = requests.post(f"{XANO_BASE}/gtfs_files", json=file_payload, headers=headers)
                file_id = file_res.json()["id"]
                
                # Créer le job
                job_payload = {
                    "type": f"import_{filename.replace('.txt', '')}",
                    "file_id": file_id,
                    "status": "pending",
                    "company_id": company_id,
                    "created_at": datetime.now().isoformat()
                }
                requests.post(f"{XANO_BASE}/jobs", json=job_payload, headers=headers)
                
                created_files.append(filename)

    return {"message": "Import lancé", "files": created_files, "version_id": version_id}
