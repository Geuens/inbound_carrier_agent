# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os

app = FastAPI(title="Inbound Carrier Agent")

@app.get("/")
def root():
    return {"status": "ok", "service": "Inbound Carrier Agent"}

@app.get("/verify-carrier/{mc_number}")
def verify_carrier(mc_number: str):
    """
    Verify carrier status using the FMCSA API.
    """
    FMCSA_API_KEY = os.getenv("FMCSA_API_KEY", "")
    if not FMCSA_API_KEY:
        raise HTTPException(status_code=500, detail="FMCSA_API_KEY is not configured")

    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{mc_number}?webKey={FMCSA_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="FMCSA lookup failed")

    data = response.json()
    return {
        "mc_number": mc_number,
        "status": data.get("content", {}).get("carrier", {}).get("operatingStatus"),
        "details": data.get("content", {}).get("carrier", {})
    }

@app.post("/webhook/happyrobot")
async def happyrobot_webhook(request: Request):
    """
    Receives POST requests from HappyRobot automation system.
    Expects JSON payload with an 'event' and 'data'.
    """
    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data")

    print(f"Received HappyRobot event: {event}")
    print(f"Payload: {data}")

    if event == "carrier_verified":
        print(f"Carrier verified: {data}")
    elif event == "carrier_failed":
        print(f"Carrier verification failed: {data}")

    return JSONResponse({"received": True, "event": event})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )

