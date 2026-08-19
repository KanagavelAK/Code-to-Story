from dotenv import load_dotenv

# Load .env before any other imports that need env vars
load_dotenv()

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from story import generate_story


# Create the FastAPI app instance
app = FastAPI(title="Code to Story", version="1.0.0")

# Allow all origins so the frontend can reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the frontend HTML file
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class ConvertRequest(BaseModel):
    """Request body for the /convert endpoint."""
    code: str
    language: str


@app.get("/")
def serve_frontend():
    """Serve the HTML frontend at the root URL."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
def health_check():
    """Return a simple status check to confirm the server is running."""
    return {"status": "ok"}


@app.post("/convert")
def convert_code_to_story(request: ConvertRequest):
    """Accept a code block and language, return an AI-generated story."""
    try:
        result = generate_story(request.code, request.language)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Story generation failed")

