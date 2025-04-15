from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.docker_runner import run_script_in_docker, sanitize_code
import uuid
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory="output"), name="output")

class ScriptRequest(BaseModel):
    code: str
    language: str

@app.post("/generate-visualization")
async def generate_chart(req: ScriptRequest):
    logger.info(f"Received request for language: {req.language}")

    if req.language not in ("python", "r"):
        logger.warning(f"Unsupported language: {req.language}")
        raise HTTPException(status_code=400, detail="Unsupported language")

    try:
        sanitize_code(req.code, req.language)
    except ValueError as e:
        logger.warning(f"Sanitization failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    try:
        filename = run_script_in_docker(code=req.code, language=req.language, output_path=None)
        logger.info(f"Visualization generated successfully: {filename}")
    except RuntimeError as e:
        logger.error(f"Script runtime error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script runtime error: {str(e)}")
    except Exception as e:
        logger.exception("Unhandled execution error")
        raise HTTPException(status_code=500, detail=f"Execution error: {e}")

    return {"status": "success", "chart_url": f"/output/{filename}"}
