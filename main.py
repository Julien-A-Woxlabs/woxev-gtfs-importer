from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
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
    company_id: str = Form(...),
    version_name: str = Form(...)
):
    try:
        payload = {
            "name": version_name,
            "status": "active",
            "company_id": company_id
        }

        res = requests.post(
            f"{XANO_BASE_URL}/gtfs_versions",
            json=payload,
            headers={
                "Authorization": f"Bearer {XANO_API_KEY}",
                "Content-Type": "application/json"
            }
        )

        print(f"Status: {res.status_code} | Response: {res.text}")

        if res.status_code != 200:
            return JSONResponse(status_code=400, content={"error": res.text})

        return {"message": "Version créée avec succès", "version_id": res.json().get("id")}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
