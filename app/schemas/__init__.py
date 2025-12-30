"""
Schemas package initialization
"""
from app.schemas.face_schemas import (
    BoundingBox,
    FaceLandmark,
    FaceDetectionResponse,
    FaceDetectionResult,
    MultiFaceDetectionResponse,
    FaceDetectionLandmarksResponse,
    FaceDetectionDeepResponse,
    SaveFaceRequest,
    SaveFaceResponse,
    MultiSaveFaceResponse,
    RecognizeFaceResponse,
    DeleteFaceRequest,
    DeleteFaceResponse,
    FaceInfo,
    ListFacesResponse,
    ErrorResponse,
    RecognizedFace,
    MultiRecognizeFaceResponse
)

__all__ = [
    "BoundingBox",
    "FaceLandmark",
    "FaceDetectionResponse",
    "FaceDetectionResult",
    "MultiFaceDetectionResponse",
    "FaceDetectionLandmarksResponse",
    "FaceDetectionDeepResponse",
    "SaveFaceRequest",
    "SaveFaceResponse",
    "MultiSaveFaceResponse",
    "RecognizeFaceResponse",
    "DeleteFaceRequest",
    "DeleteFaceResponse",
    "FaceInfo",
    "ListFacesResponse",
    "ErrorResponse",
    "RecognizedFace",
    "MultiRecognizeFaceResponse"
]
