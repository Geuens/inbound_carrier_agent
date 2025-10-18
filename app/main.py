from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import re
import os

# ------------- Security Setup -------------
API_KEY = os.getenv("API_KEY", "dev-secret-key")

def check_api_key(x_api_key: Optional[str] = Header(None)):
    """Reject requests without the correct x-api-key header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ------------- Data Model -------------
class CarrierIn(BaseModel):
    mc_number: str

class CarrierOut(BaseModel):
    mc_number: str
    eligible: bool
    reason: str

# ------------- App Definition -------------
app = FastAPI(title="Inbound Carrier Sales API")

@app.get("/healthz")
def health():
    return {"ok": True}

# ------------- FMCSA Verification Endpoint -------------
@app.post("/verify_carrier", response_model=CarrierOut)
def verify_carrier(payload: CarrierIn, x_api_key: str = Header(None)):
    """Check carrier eligibility based on mock FMCSA rules."""
    check_api_key(x_api_key)

    mc_number = payload.mc_number.strip().upper()
    digits = re.sub(r"\D", "", mc_number)  # keep only numbers

    # --- Mock validation logic ---
    if not digits:
        return CarrierOut(mc_number=mc_number, eligible=False, reason="Missing MC digits")
    if not (5 <= len(digits) <= 7):
        return CarrierOut(mc_number=mc_number, eligible=False, reason="MC number must be 5–7 digits")
    if digits.startswith("9"):
        return CarrierOut(mc_number=mc_number, eligible=False, reason="FMCSA disqualified (starts with 9)")

    # If it passes all checks, assume it's eligible
    return CarrierOut(mc_number=mc_number, eligible=True, reason="")
