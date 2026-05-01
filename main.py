from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

app = FastAPI()

# ================= HOME =================
@app.get("/")
def home():
    return {"status": "SAAS ONLINE 🚀"}

# ================= DB (MEMÓRIA - DEMO) =================
licenses = {}

# ================= MODELOS =================
class CreateKey(BaseModel):
    days: int = 0

class ValidateKey(BaseModel):
    key: str
    hwid: str

# ================= CREATE KEY =================
@app.post("/create")
def create(data: CreateKey):
    key = str(uuid.uuid4())

    expires = None
    if data.days > 0:
        expires = (datetime.utcnow() + timedelta(days=data.days)).isoformat()

    licenses[key] = {
        "hwid": "",
        "expires": expires,
        "active": True
    }

    return {"key": key}

# ================= VALIDATE =================
@app.post("/validate")
def validate(data: ValidateKey):
    lic = licenses.get(data.key)

    if not lic:
        return {"status": "invalid"}

    if not lic["active"]:
        return {"status": "blocked"}

    if lic["expires"]:
        if datetime.utcnow() > datetime.fromisoformat(lic["expires"]):
            return {"status": "expired"}

    if lic["hwid"] == "" or lic["hwid"] == data.hwid:
        lic["hwid"] = data.hwid
        return {"status": "ok"}

    return {"status": "wrong_device"}

# ================= BLOCK =================
@app.post("/block")
def block(data: ValidateKey):
    lic = licenses.get(data.key)

    if not lic:
        return {"status": "not_found"}

    lic["active"] = False
    return {"status": "blocked"}