from fastapi import FastAPI, File, UploadFile, Form
import zipfile
import io
import requests
import os
from datetime import datetime

app = FastAPI()

XANO_API_KEY = os.getenv("XANO_API_KEY")
XANO_BASE_URL = os.getenv("XANO_BASE_URL")

headers = {
    "Authorization": f"Bearer {XANO_API_KEY}",
    "Content-Type": "application/json"
}

@app.post("/import-gtfs")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    version_name: str = Form(...)
):
    # 1. Créer la version GTFS
    version_payload = {
        "name": version_name,
        "import_date": datetime.now().isoformat(),
        "status": "active",
        "company_id": company_id
    }
    
    version_res = requests.post(f"{XANO_BASE_URL}/gtfs_versions", json=version_payload, headers=headers)
    if version_res.status_code != 200:
        return JSONResponse(status_code=400, content={"error": "Impossible de créer gtfs_versions"})
    
    version_id = version_res.json().get("id")

    # 2. Dézipper et traiter les fichiers
    content = await file.read()
    created_files = []

    with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
        for filename in zip_ref.namelist():
            if filename.endswith(".txt"):
                file_content = zip_ref.read(filename)
                
                # Upload du fichier dans Xano
                upload_res = requests.post(
                    f"{XANO_BASE_URL}/file",
                    files={"file": (filename, file_content, "text/plain")},
                    headers={"Authorization": f"Bearer {XANO_API_KEY}"}
                )
                
                if upload_res.status_code != 200:
                    continue  # on saute ce fichier si erreur
                
                file_url = upload_res.json().get("url")
                
                # Créer l'enregistrement dans gtfs_files
                file_payload = {
                    "company_id": company_id,
                    "gtfs_version_id": version_id,
                    "file_type": filename.replace(".txt", ""),
                    "file_url": file_url,
                    "original_name": filename,
                    "uploaded_at": datetime.now().isoformat(),
                    "status": "not_started"
                }
                
                file_res = requests.post(f"{XANO_BASE_URL}/gtfs_files", json=file_payload, headers=headers)
                file_id = file_res.json().get("id")

                # Créer le job pour la Background Task
                job_payload = {
                    "type": f"import_{filename.replace('.txt', '')}",
                    "file_id": file_id,
                    "status": "pending",
                    "company_id": company_id,
                    "created_at": datetime.now().isoformat(),
                    "total_rows": 0,        # on mettra à jour plus tard
                    "processed_rows": 0
                }
                
                requests.post(f"{XANO_BASE_URL}/jobs", json=job_payload, headers=headers)
                
                created_files.append(filename)

    return {
        "message": "Import lancé avec succès",
        "version_id": version_id,
        "files_count": len(created_files),
        "files": created_files
    }
