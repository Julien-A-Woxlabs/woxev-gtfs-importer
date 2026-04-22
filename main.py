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

@app.post("/import-gtfs")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    version_name: str = Form(...)
):
    try:
        print(f"DEBUG START - company: {company_id} | version: {version_name} | base: {XANO_BASE_URL}")

        # 1. Créer la version GTFS
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

        print(f"DEBUG Version status: {version_res.status_code}")

        if version_res.status_code != 200:
            print("ERROR Version:", version_res.text)
            return JSONResponse(status_code=400, content={"error": version_res.text})

        version_id = version_res.json().get("id")
        print(f"DEBUG Version ID: {version_id}")

        # 2. Traiter les fichiers du ZIP
        content = await file.read()
        created_files = []

        with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(".txt"):
                    file_content = zip_ref.read(filename)
                    
                    # Upload du fichier
                    upload_res = requests.post(
                        f"{XANO_BASE_URL}/file",
                        files={"file": (filename, file_content, "text/plain")},
                        headers={"Authorization": f"Bearer {XANO_API_KEY}"}
                    )

                    print(f"DEBUG Upload {filename} status: {upload_res.status_code}")

                    if upload_res.status_code != 200:
                        continue

                    file_url = upload_res.json().get("url")

                    # Créer gtfs_files
                    file_payload = {
                        "company_id": company_id,
                        "gtfs_version_id": version_id,
                        "file_type": filename.replace(".txt", ""),
                        "file_url": file_url,
                        "original_name": filename,
                        "uploaded_at": datetime.now().isoformat(),
                        "status": "not_started"
                    }
                    
                    file_res = requests.post(f"{XANO_BASE_URL}/gtfs_files", json=file_payload, headers={
                        "Authorization": f"Bearer {XANO_API_KEY}",
                        "Content-Type": "application/json"
                    })

                    file_id = file_res.json().get("id")

                    # Créer le job
                    job_payload = {
                        "type": f"import_{filename.replace('.txt', '')}",
                        "file_id": file_id,
                        "status": "pending",
                        "company_id": company_id,
                        "created_at": datetime.now().isoformat(),
                        "total_rows": 0,
                        "processed_rows": 0
                    }
                    
                    requests.post(f"{XANO_BASE_URL}/jobs", json=job_payload, headers={
                        "Authorization": f"Bearer {XANO_API_KEY}",
                        "Content-Type": "application/json"
                    })

                    created_files.append(filename)
                    print(f"DEBUG Job créé pour {filename}")

        print(f"SUCCESS - {len(created_files)} fichiers traités")
        return {
            "message": "Import lancé avec succès",
            "version_id": version_id,
            "files_count": len(created_files),
            "files": created_files
        }

    except Exception as e:
        print("EXCEPTION:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
