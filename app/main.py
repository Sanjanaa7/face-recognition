"""
Main FastAPI Application for Face Recognition System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routers import face_detection_router, face_recognition_router
from app.models import init_db
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Face Recognition System API",
    description="""
    A complete Face Recognition System with the following features:
    
    ## Face Detection Endpoints (No Database Operations)
    * **Face Detection** - Detect faces and extract embeddings
    * **Face Detection with Landmarks** - Detect faces with facial landmarks
    * **Deep Face Analysis** - Detect faces with emotion, age, and gender prediction
    
    ## Face Recognition Endpoints (Database Operations)
    * **Save Face** - Save a face to the database
    * **Recognize Face** - Recognize a face from the database
    * **Delete Face** - Delete a face from the database
    * **List Faces** - List all saved faces
    
    ## Technologies Used
    * MediaPipe - Face detection & facial landmarks
    * DeepFace - Face embeddings, emotion, age, and gender prediction
    * FastAPI - REST API framework
    * SQLite - Database for storing face embeddings
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(face_detection_router.router)
app.include_router(face_recognition_router.router)


from app.services.face_detection_service import face_detection_service

@app.on_event("startup")
async def startup_event():
    """
    Initialize database and load models on startup
    """
    print("🚀 Starting Face Recognition System...")
    
    # Initialize Database
    init_db()
    print("✅ Database initialized!")
    
    # Pre-load AI Models
    face_detection_service.load_models()
    
    print("📡 API Server running at http://127.0.0.1:8000")
    print("📚 API Documentation available at http://127.0.0.1:8000/docs")
    print("📖 ReDoc available at http://127.0.0.1:8000/redoc")


@app.get("/api/info", tags=["Root"])
async def root():
    """
    API Information endpoint
    """
    return JSONResponse(content={
        "message": "Welcome to Face Recognition System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "detection": [
                "/api/face-detection",
                "/api/face-detection-landmarks",
                "/api/face-detection-deep"
            ],
            "recognition": [
                "/api/save-face",
                "/api/recognize-face",
                "/api/delete-face",
                "/api/list-faces"
            ]
        }
    })


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "Face Recognition System",
        "version": "1.0.0"
    })

# Mount frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
