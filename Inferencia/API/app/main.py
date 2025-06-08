import os
import logging
import shutil
import glob
import json
from io import BytesIO
from zipfile import ZipFile
from datetime import datetime
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
import cv2
from PIL import Image

# ─── Configurações via ENV / .env ──────────────────────────────────────────────
class Settings(BaseSettings):
    AZ_CONN_STR: str
    INPUT_CONTAINER: str       = "input-container"
    OUTPUT_CONTAINER: str      = "predict-source"
    PROCESSED_PREFIX: str      = "ProcessadoComSucesso/"
    LOCAL_TMP: str             = "/tmp"

    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DATABASE: str        = "GreeningDetection"
    COSMOS_CONTAINER: str       = "Predicoes"

    STORAGE_ACCOUNT_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()

# ─── Cria clientes únicos ──────────────────────────────────────────────────────
blob_service   = BlobServiceClient.from_connection_string(settings.AZ_CONN_STR)
input_client   = blob_service.get_container_client(settings.INPUT_CONTAINER)
output_client  = blob_service.get_container_client(settings.OUTPUT_CONTAINER)

cosmos_client      = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
db_client          = cosmos_client.get_database_client(settings.COSMOS_DATABASE)
cosmos_container   = db_client.get_container_client(settings.COSMOS_CONTAINER)

# ─── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI()
model = None  # será carregado no startup

@app.on_event("startup")
def load_model():
    global model
    logging.info("Baixando modelo YOLO…")
    model_path = hf_hub_download(
        repo_id="cuidacitrus/yolov8n-greening-detector",
        filename="v3_best.pt"
    )
    model = YOLO(model_path)
    logging.info("Modelo YOLO carregado")

def process_blob(blob_name: str):
    logging.info(f"Processando blob: {blob_name}")
    os.makedirs(settings.LOCAL_TMP, exist_ok=True)
    local_zip = os.path.join(settings.LOCAL_TMP, os.path.basename(blob_name))

    # 1) baixa o ZIP
    data = input_client.download_blob(blob_name).readall()
    with open(local_zip, "wb") as f:
        f.write(data)

    # 2) extrai
    extract_dir = os.path.join(settings.LOCAL_TMP, "extracted")
    if os.path.isdir(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    with ZipFile(local_zip, "r") as z:
        z.extractall(extract_dir)

    # 3) metadata (se existir)
    metadata_map = {}
    meta_file = os.path.join(extract_dir, "metadata.json")
    if os.path.isfile(meta_file):
        raw = json.load(open(meta_file)).get("locations", [])
        items = raw[0] if raw and isinstance(raw[0], list) else raw
        for item in items:
            if isinstance(item, dict) and "filename" in item:
                metadata_map[item["filename"]] = item

    # 4) inferência em cada imagem
    for img_path in glob.glob(os.path.join(extract_dir, "*")):
        if not img_path.lower().endswith((".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")):
            continue

        res = model.predict(source=img_path, conf=0.75, verbose=False)[0]
        annotated = cv2.cvtColor(res.plot(), cv2.COLOR_BGR2RGB)
        buf = BytesIO()
        Image.fromarray(annotated).save(buf, format="JPEG")
        buf.seek(0)

        fname = os.path.basename(img_path)
        output_client.upload_blob(name=fname, data=buf, overwrite=True)
        url_image = f"{settings.STORAGE_ACCOUNT_URL}/{settings.OUTPUT_CONTAINER}/{fname}"

        # coleta detecções “greening”
        detections = []
        for box in res.boxes:
            label = res.names[int(box.cls)]
            if label.lower() == "greening":
                detections.append({
                    "label":      label,
                    "confidence": float(box.conf),
                    "bbox":       [*map(float, box.xyxy[0].tolist())]
                })

        if detections:
            meta = metadata_map.get(fname, {})
            item = {
                "id":           fname,
                "detections":   detections,
                "latitude":     meta.get("latitude"),
                "longitude":    meta.get("longitude"),
                "url_image":    url_image,
                "processed_at": datetime.utcnow().isoformat()
            }
            cosmos_container.upsert_item(item)

    # 5) move o ZIP original para o prefixo de processado
    dest = settings.PROCESSED_PREFIX + os.path.basename(blob_name)
    src_blob = input_client.get_blob_client(blob_name)
    dst_blob = input_client.get_blob_client(dest)
    data = src_blob.download_blob().readall()
    dst_blob.upload_blob(data, overwrite=True)
    src_blob.delete_blob()
    logging.info(f"📦 ZIP movido para {dest}")

    # limpeza
    os.remove(local_zip)
    shutil.rmtree(extract_dir)
    logging.info(f"✅ Processamento completo: {blob_name}")

@app.api_route("/process", methods=["GET", "POST"])
async def process_all(request: Request):
    if request.method == "GET":
        return Response(status_code=200)
    

    payload = await request.json()
    events  = payload if isinstance(payload, list) else [payload]

    try:
        for ev in events:
            et = ev.get("eventType")

            if et == "Microsoft.EventGrid.SubscriptionValidationEvent":
                code = ev["data"]["validationCode"]
                return JSONResponse({"validationResponse": code})

            if et != "Microsoft.Storage.BlobCreated":
                continue

            url = ev["data"].get("url")
            if not url:
                continue 

            parsed = urlparse(url)
            container_prefix = f"/{settings.INPUT_CONTAINER}/"
            if not parsed.path.startswith(container_prefix):
                continue

            blob_name = parsed.path[len(container_prefix):]

            if blob_name.startswith(settings.PROCESSED_PREFIX):
                logging.info(f"Pulando blob já processado: {blob_name}")
                continue

            logging.info(f"Processando: {blob_name}")
            process_blob(blob_name)
        logging.info(f"Processo concluido com sucesso!")
    except Exception as e:
        logging.exception("Erro no processamento")
        raise HTTPException(status_code=500, detail="Erro interno")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
