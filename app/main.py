# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
import logging
import pandas as pd
from pathlib import Path


app = FastAPI(title="Inbound Carrier Agent")

DATA_PATH = Path(__file__).parent / "data" / "Company_Census_File_20251018_small.csv"

try:
    carriers_df = pd.read_csv(DATA_PATH, dtype=str)  # Load as strings to avoid numeric mismatches
except FileNotFoundError:
    raise HTTPException(status_code=500, detail="Carrier data file not found")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error loading carrier data: {e}")

@app.get("/")
def root():
    return {"status": "ok", "service": "Inbound Carrier Agent"}

def verify_carrier(mc_number: str):
    """
    Verify if the given MC number exists in the local CSV dataset.
    Returns mc_correct = True if found, else False.
    """
    mc_number = str(mc_number).strip()
    logger.info(f"Verifying MC number: {mc_number}")

    if "DOCKET1" not in carriers_df.columns:
        logger.error("CSV missing 'DOCKET1' column.")
        raise HTTPException(status_code=500, detail="CSV missing 'DOCKET1' column")

    exists = carriers_df["DOCKET1"].astype(str).str.strip().eq(mc_number).any()

    if exists:
        logger.info(f"MC number {mc_number} found in dataset.")
    else:
        logger.warning(f"MC number {mc_number} not found in dataset.")

    return {"mc_number": mc_number, "mc_correct": bool(exists)}

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

