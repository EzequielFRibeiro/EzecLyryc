from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, upload, websocket, transcriptions, subscriptions

app = FastAPI(
    title="CifraPartit API",
    description="AI-powered music transcription platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(websocket.router)
app.include_router(transcriptions.router)
app.include_router(subscriptions.router)

@app.get("/")
async def root():
    return {"message": "CifraPartit API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
