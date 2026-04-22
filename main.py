from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import zipfile
import io
import requests
import os
from datetime import datetime

app = FastAPI()

XANO_API_KEY = os.getenv("eyJhbGciOiJBMjU2S1ciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiemlwIjoiREVGIn0.xslKVuIGFJ6cq_lJyoubyqIWFwsF2igIJRyAcnDRfBX5HsoHVElyeEiR7QaYSITtHGCi5Au-BPBlaR2ehMglgkvW7nCcG9uG.4UV1jL4IlGwf0AFCEmeNMg.Wf5cQ5d-tYYkn1NxvHxkYE0AZyq8zGbEH6Hoa9JKYmgvRfQoStIKe2oXXaQDhgdMYYt9SNkhm7BiVWxBHBtetduCJnZQ-Rvq_SOYL2jRaCzpqKuVCbjo6yQhrKLNLnrgIrr-pKpIDHwWNu3FXEHVlypZl9eLZsaC-O9tQZHEGPY.acmsTw0SlrPtcfL8A6GDd2Bnvfoui-04CD0-eGzILt0")
XANO_BASE_URL = "https://xfnq-h4pb-gxqm.p7.xano.io/api:N1ylqXnK/uppload/GTFS_import"  # à remplacer

@app.post("/import-gtfs")
async def import_gtfs(
    file: UploadFile = File(...),
    company_id: int = Form(...),
    version_name: str = Form(...)
):
    # 1. Créer la version GTFS
    version_data = {
        "name": version_name,
        "import_date": datetime.now().isoformat(),
        "status": "active",
        "company_id": company_id
    }
    # TODO: Appeler l'API Xano pour créer gtfs_versions

    # 2. Dézipper et filtrer les fichiers utiles
    content = await file.read()
    with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
        file_list = zip_ref.namelist()
        gtfs_files = [f for f in file_list if f.endswith('.txt') and f in 
                      ["shapes.txt", "stop_times.txt", "routes.txt", "trips.txt", 
                       "calendar.txt", "calendar_dates.txt", "agency.txt", "stops.txt"]]
        
        for filename in gtfs_files:
            file_content = zip_ref.read(filename)
            # TODO: Upload vers Xano + créer gtfs_files + créer job

    return {"message": "Import lancé", "files": gtfs_files}
