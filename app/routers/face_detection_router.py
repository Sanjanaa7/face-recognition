"""
Face Detection Router - Detection endpoints WITHOUT database operations
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas import (
    FaceDetectionResponse,
    FaceDetectionLandmarksResponse,
    FaceDetectionDeepResponse,
    ErrorResponse
)
from app.services import face_detection_service
import time

router = APIRouter(prefix="/api", tags=["Face Detection"])


@router.post(
    "/face-detection",
    response_model=FaceDetectionResponse,
    summary="Detect face and extract embeddings",
    description="Detects a face in the uploaded image and returns bounding box and face embeddings. NO database operations."
)
async def detect_face(image: UploadFile = File(...)):
    """
    Detect face in image and return:
    - Face bounding box
    - Face embeddings
    
    This endpoint ONLY performs detection, no database operations.
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect face
        detection_result = face_detection_service.detect_face(img_array)
        
        if not detection_result:
            return FaceDetectionResponse(
                success=True,
                message="No face detected in the image",
                face_detected=False
            )
        
        # Get face embedding
        embedding = face_detection_service.get_face_embedding(img_array, bbox=detection_result['bounding_box'])
        
        return FaceDetectionResponse(
            success=True,
            message="Face detected successfully",
            face_detected=True,
            bounding_box=detection_result['bounding_box'],
            face_embedding=embedding,
            confidence=detection_result['confidence']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/face-detection-landmarks",
    response_model=FaceDetectionLandmarksResponse,
    summary="Detect face with facial landmarks",
    description="Detects a face and extracts facial landmarks (eyes, nose, mouth, etc.). NO database operations."
)
async def detect_face_landmarks(image: UploadFile = File(...)):
    """
    Detect face with landmarks and return:
    - Face bounding box
    - Face embeddings
    - Facial landmark points (eyes, nose, lips, etc.)
    
    This endpoint ONLY performs detection, no database operations.
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect face
        detection_result = face_detection_service.detect_face(img_array)
        
        if not detection_result:
            return FaceDetectionLandmarksResponse(
                success=True,
                message="No face detected in the image",
                face_detected=False
            )
        
        # Get face embedding
        embedding = face_detection_service.get_face_embedding(img_array, bbox=detection_result['bounding_box'])
        
        # Detect landmarks
        landmarks = face_detection_service.detect_landmarks(img_array)
        
        return FaceDetectionLandmarksResponse(
            success=True,
            message="Face and landmarks detected successfully",
            face_detected=True,
            bounding_box=detection_result['bounding_box'],
            face_embedding=embedding,
            landmarks=landmarks,
            confidence=detection_result['confidence']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/face-detection-deep",
    response_model=FaceDetectionDeepResponse,
    summary="Deep face analysis with emotion, age, and gender",
    description="Detects face and performs deep analysis including emotion, age, and gender prediction. NO database operations."
)
async def detect_face_deep(image: UploadFile = File(...)):
    """
    Detect face with deep analysis and return:
    - Face bounding box
    - Face embeddings
    - Emotion (with confidence scores)
    - Age
    - Gender (with confidence)
    
    This endpoint ONLY performs detection and analysis, no database operations.
    """
    try:
        start_time = time.time()
        
        # Read image data
        image_data = await image.read()
        t1 = time.time()
        print(f"⏱️ Read image: {t1 - start_time:.3f}s")
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        t2 = time.time()
        print(f"⏱️ Decode image: {t2 - t1:.3f}s")
        
        # Detect face
        detection_result = face_detection_service.detect_face(img_array)
        t3 = time.time()
        print(f"⏱️ Detect face (MediaPipe): {t3 - t2:.3f}s")
        
        if not detection_result:
            return FaceDetectionDeepResponse(
                success=True,
                message="No face detected in the image",
                face_detected=False
            )
        
        # Get face embedding
        embedding = face_detection_service.get_face_embedding(img_array, bbox=detection_result['bounding_box'])
        t4 = time.time()
        print(f"⏱️ Get embedding (DeepFace): {t4 - t3:.3f}s")
        
        # Deep analysis
        deep_analysis = face_detection_service.analyze_face_deep(img_array, bbox=detection_result['bounding_box'])
        t5 = time.time()
        print(f"⏱️ Deep analysis: {t5 - t4:.3f}s")
        
        response_data = {
            'success': True,
            'message': 'Face detected and analyzed successfully',
            'face_detected': True,
            'bounding_box': detection_result['bounding_box'],
            'face_embedding': embedding,
            'confidence': detection_result['confidence']
        }
        
        if deep_analysis:
            response_data.update({
                'emotion': deep_analysis['emotion'],
                'emotion_scores': deep_analysis['emotion_scores'],
                'age': deep_analysis['age'],
                'gender': deep_analysis['gender'],
                'gender_confidence': deep_analysis['gender_confidence']
            })
        
        total_time = time.time() - start_time
        print(f"✅ Total request time: {total_time:.3f}s")
        
        return FaceDetectionDeepResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
