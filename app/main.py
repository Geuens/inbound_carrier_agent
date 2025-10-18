# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
import logging
import pandas as pd
from pathlib import Path


app = FastAPI(title="Inbound Carrier Agent")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent / "data" / "Company_Census_File_20251018_small.csv"

try:
    carriers_df = pd.read_csv(DATA_PATH, dtype=str)  # Load as strings to avoid numeric mismatches
except FileNotFoundError:
    raise HTTPException(status_code=500, detail="Carrier data file not found")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error loading carrier data: {e}")

@app.post("/webhook/verify")
async def verify_carrier(request: Request):
    """
    Verify if the given MC number exists in the local CSV dataset.
    Returns received=True if found, otherwise received=False.
    """
    body = await request.json()
    mc_number = str(body.get("mc_number", "")).strip()
    logger.info(f"Verifying MC number: {mc_number}")

    if not mc_number:
        logger.warning("No MC number provided in request.")
        return JSONResponse({"received": False, "mc_number": None, "mc_correct": False})

    if "DOCKET1" not in carriers_df.columns:
        logger.error("CSV missing 'DOCKET1' column.")
        raise HTTPException(status_code=500, detail="CSV missing 'DOCKET1' column")

    exists = carriers_df["DOCKET1"].astype(str).str.strip().eq(mc_number).any()
    logger.info(f"MC number {mc_number} {'found' if exists else 'not found'} in dataset.")

    return JSONResponse({
        "received": exists,
        "mc_number": mc_number,
        "mc_correct": exists
    })

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path}
    )

