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
    output_type: str = "png"  # "png" or "html"
    visualization_type: str = "static"  # "static", "interactive", or "3d"

@app.post("/generate-visualization")
async def generate_chart(req: ScriptRequest):
    if req.language not in ("python", "r"):
        raise HTTPException(status_code=400, detail="Unsupported language")

    if req.output_type not in ("png", "html"):
        raise HTTPException(status_code=400, detail="Unsupported output type")

    try:
        sanitize_code(req.code, req.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ext = "html" if req.output_type == "html" else "png"
    output_filename = f"{uuid.uuid4()}.{ext}"
    output_path = os.path.join(os.path.abspath("output"), output_filename)


    try:
        run_script_in_docker(code=req.code, language=req.language, output_path=output_path, output_type=req.output_type, visualization_type=req.visualization_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {e}")

    return {"status": "success", "chart_url": f"/output/{output_filename}"}

