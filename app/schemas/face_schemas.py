"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# Face Detection Schemas
# ============================================

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: int
    y: int
    width: int
    height: int
class ImageMeta(BaseModel):
    """Metadata about the processed image"""
    width: int
    height: int

class FaceLandmark(BaseModel):
    """Facial landmark point"""
    index: Optional[int] = None  # Landmark index (0-467 for MediaPipe Face Mesh)
    x: float
    y: float
    z: Optional[float] = None


class FaceDetectionResponse(BaseModel):
    """Response for /face-detection endpoint"""
    success: bool
    message: str
    face_detected: bool
    bounding_box: Optional[BoundingBox] = None
    face_embedding: Optional[List[float]] = None
    confidence: Optional[float] = None


class FaceDetectionResult(BaseModel):
    """Individual face detection result"""
    bounding_box: BoundingBox
    face_embedding: Optional[List[float]] = None
    confidence: float


class MultiFaceDetectionResponse(BaseModel):
    """Response for multi-face detection"""
    success: bool
    message: str
    faces_detected: int
    detections: List[FaceDetectionResult]
    image_meta: Optional[ImageMeta] = None


class FaceDetectionLandmarksResponse(BaseModel):
    """Response for /face-detection-landmarks endpoint"""
    success: bool
    message: str
    face_detected: bool
    bounding_box: Optional[BoundingBox] = None
    face_embedding: Optional[List[float]] = None
    all_landmarks: Optional[List[FaceLandmark]] = None  # All 468 face mesh points
    total_landmarks: Optional[int] = None  # Total number of landmarks
    categorized: Optional[Dict[str, List[FaceLandmark]]] = None  # Grouped by feature
    confidence: Optional[float] = None


class FaceDetectionDeepResponse(BaseModel):
    """Response for /face-detection-deep endpoint"""
    success: bool
    message: str
    face_detected: bool
    bounding_box: Optional[BoundingBox] = None
    face_embedding: Optional[List[float]] = None
    emotion: Optional[str] = None
    emotion_scores: Optional[Dict[str, float]] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    gender_confidence: Optional[float] = None
    confidence: Optional[float] = None


# ============================================
# Database Operation Schemas
# ============================================

class SaveFaceRequest(BaseModel):
    """Request to save a face"""
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class SaveFaceResponse(BaseModel):
    """Response for saving a face"""
    success: bool
    message: str
    face_id: Optional[int] = None
    name: Optional[str] = None


class MultiSaveFaceResponse(BaseModel):
    """Response for bulk saving faces"""
    success: bool
    message: str
    saved_faces: List[SaveFaceResponse]


class RecognizeFaceResponse(BaseModel):
    """Response for face recognition"""
    success: bool
    message: str
    recognized: bool
    name: Optional[str] = None
    confidence: Optional[float] = None
    face_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class RecognizedFace(BaseModel):
    """Detailed information for a recognized face"""
    recognized: bool
    name: Optional[str] = "Unknown"
    confidence: Optional[float] = None
    face_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bounding_box: BoundingBox


class MultiRecognizeFaceResponse(BaseModel):
    """Response for multi-face recognition"""
    success: bool
    message: str
    faces_detected: int
    recognized_faces: List[RecognizedFace]
    image_meta: Optional[ImageMeta] = None


class DeleteFaceRequest(BaseModel):
    """Request to delete a face"""
    face_id: Optional[int] = None
    name: Optional[str] = None


class DeleteFaceResponse(BaseModel):
    """Response for deleting a face"""
    success: bool
    message: str
    deleted_count: int


class FaceInfo(BaseModel):
    """Face information"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    thumbnail: Optional[str] = None
    created_at: datetime
    embedding_model: str

    class Config:
        from_attributes = True


class ListFacesResponse(BaseModel):
    """Response for listing all faces"""
    success: bool
    message: str
    total_faces: int
    faces: List[FaceInfo]


# ============================================
# Error Response Schema
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
