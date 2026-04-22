from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import zipfile
import io
import requests
import os                     # ← C'est cette ligne qui manquait !
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

@app.post("/import_gtfs")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: str = Form(...),
    version_name: str = Form(...)
):
    try:
        # Création version
        version_res = requests.post(
            f"{XANO_BASE_URL}/gtfs_versions",
            json={
                "name": version_name,
                "status": "active",
                "company_id": company_id
            },
            headers={"Authorization": f"Bearer {XANO_API_KEY}", "Content-Type": "application/json"}
        )

        if version_res.status_code != 200:
            return JSONResponse(status_code=400, content={"error": "Impossible de créer la version"})

        version_id = version_res.json().get("id")

        # Upload des .txt
        content = await file.read()
        count = 0

        with zipfile.ZipFile(io.BytesIO(content)) as z:
            for name in z.namelist():
                if name.endswith(".txt"):
                    data = z.read(name)
                    upload = requests.post(
                        f"{XANO_BASE_URL}/file",
                        files={"file": (name, data, "text/plain")},
                        headers={"Authorization": f"Bearer {XANO_API_KEY}"}
                    )
                    if upload.status_code == 200:
                        url = upload.json().get("url")
                        requests.post(
                            f"{XANO_BASE_URL}/gtfs_files",
                            json={
                                "company_id": company_id,
                                "gtfs_version_id": version_id,
                                "file_type": name.replace(".txt", ""),
                                "file_url": url,
                                "original_name": name,
                                "status": "not_started"
                            },
                            headers={"Authorization": f"Bearer {XANO_API_KEY}", "Content-Type": "application/json"}
                        )
                        count += 1

        return {"message": "OK", "files_uploaded": count, "version_id": version_id}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
