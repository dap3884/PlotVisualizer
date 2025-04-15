from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.docker_runner import run_script_in_docker, sanitize_code
import uuid
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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
    if req.language not in ("python", "r"):
        raise HTTPException(status_code=400, detail="Unsupported language")

    try:
        sanitize_code(req.code, req.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        filename = run_script_in_docker(code=req.code, language=req.language, output_path=None)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Syntax Error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {e}")

    return {"status": "success", "chart_url": f"/output/{filename}"}

