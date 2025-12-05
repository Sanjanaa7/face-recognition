"""
Services package initialization
"""
from app.services.face_detection_service import face_detection_service, FaceDetectionService
from app.services.face_recognition_service import face_recognition_service, FaceRecognitionService

__all__ = [
    "face_detection_service",
    "FaceDetectionService",
    "face_recognition_service",
    "FaceRecognitionService"
]
