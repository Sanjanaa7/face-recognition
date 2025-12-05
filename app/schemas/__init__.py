"""
Schemas package initialization
"""
from app.schemas.face_schemas import (
    BoundingBox,
    FaceLandmark,
    FaceDetectionResponse,
    FaceDetectionLandmarksResponse,
    FaceDetectionDeepResponse,
    SaveFaceRequest,
    SaveFaceResponse,
    RecognizeFaceResponse,
    DeleteFaceRequest,
    DeleteFaceResponse,
    FaceInfo,
    ListFacesResponse,
    ErrorResponse
)

__all__ = [
    "BoundingBox",
    "FaceLandmark",
    "FaceDetectionResponse",
    "FaceDetectionLandmarksResponse",
    "FaceDetectionDeepResponse",
    "SaveFaceRequest",
    "SaveFaceResponse",
    "RecognizeFaceResponse",
    "DeleteFaceRequest",
    "DeleteFaceResponse",
    "FaceInfo",
    "ListFacesResponse",
    "ErrorResponse"
]
