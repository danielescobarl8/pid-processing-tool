from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import pandas as pd
import uuid
import os

app = FastAPI()

OUTPUT_DIR = "output_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/process/")
async def process_file(
    file: UploadFile = File(...),
    pids: str = Form(...)
):
    df = pd.read_csv(file.file, delimiter=";", low_memory=False)
    df_filtered = df[['PID', 'MPL_PRODUCT_ID', 'COLOR_ID']]

    user_pids = [pid.strip() for pid in pids.split(",")]
    df_selected = df_filtered[df_filtered['PID'].isin(user_pids)]
    color_ids = df_selected['COLOR_ID'].dropna().unique()
    df_final = df_filtered[df_filtered['COLOR_ID'].isin(color_ids)].copy()

    df_final['CATALOG_VERSION'] = "SBCColombiaProductCatalog"
    df_final['APPROVAL_STATUS'] = "approved"
    df_final.rename(columns={'PID': 'SKU', 'MPL_PRODUCT_ID': 'Base Product ID'}, inplace=True)
    df_final = df_final[['SKU', 'Base Product ID', 'CATALOG_VERSION', 'APPROVAL_STATUS']]

    file_name = f"{uuid.uuid4()}.txt"
    file_path = os.path.join(OUTPUT_DIR, file_name)
    df_final.to_csv(file_path, index=False, sep="|")

    return {"download_url": f"/download/{file_name}"}

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = os.path.join(OUTPUT_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/plain', filename="processed_output.txt")
    return {"error": "File not found"}
