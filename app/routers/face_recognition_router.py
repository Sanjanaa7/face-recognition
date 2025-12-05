"""
Face Recognition Router - Database operations for saving and recognizing faces
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas import (
    SaveFaceResponse,
    RecognizeFaceResponse,
    DeleteFaceResponse,
    ListFacesResponse,
    FaceInfo
)
from app.services import face_detection_service, face_recognition_service
from app.models import get_db

router = APIRouter(prefix="/api", tags=["Face Recognition"])


@router.post(
    "/save-face",
    response_model=SaveFaceResponse,
    summary="Save a face to the database",
    description="Detects a face in the image, extracts embeddings, and saves it to the database with the provided name."
)
async def save_face(
    name: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Save a face to the database:
    1. Detect face in image
    2. Extract face embedding
    3. Save to database with name and optional contact info
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect face
        detection_result = face_detection_service.detect_face(img_array)
        
        if not detection_result:
            return SaveFaceResponse(
                success=False,
                message="No face detected in the image. Please upload a clear image with a visible face."
            )
        
        # Get face embedding
        embedding = face_detection_service.get_face_embedding(img_array)
        
        if not embedding:
            return SaveFaceResponse(
                success=False,
                message="Failed to extract face embedding. Please try with a different image."
            )
        
        # Save to database
        face_record = face_recognition_service.save_face(
            db=db,
            name=name,
            embedding=embedding,
            email=email,
            phone=phone
        )
        
        return SaveFaceResponse(
            success=True,
            message=f"Face saved successfully for {name}",
            face_id=face_record.id,
            name=face_record.name
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/recognize-face",
    response_model=RecognizeFaceResponse,
    summary="Recognize a face from the database",
    description="Detects a face in the image and matches it against stored faces in the database."
)
async def recognize_face(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recognize a face:
    1. Detect face in image
    2. Extract face embedding
    3. Compare with stored faces
    4. Return matched identity with confidence
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect face
        detection_result = face_detection_service.detect_face(img_array)
        
        if not detection_result:
            # Log recognition attempt
            face_recognition_service.log_recognition(
                db=db,
                recognized_name=None,
                confidence=None,
                status="no_face"
            )
            
            return RecognizeFaceResponse(
                success=True,
                message="No face detected in the image",
                recognized=False
            )
        
        # Get face embedding
        embedding = face_detection_service.get_face_embedding(img_array)
        
        if not embedding:
            return RecognizeFaceResponse(
                success=False,
                message="Failed to extract face embedding",
                recognized=False
            )
        
        # Recognize face
        matched_record, confidence = face_recognition_service.recognize_face(
            db=db,
            embedding=embedding
        )
        
        if matched_record:
            # Log successful recognition
            face_recognition_service.log_recognition(
                db=db,
                recognized_name=matched_record.name,
                confidence=confidence,
                status="success"
            )
            
            return RecognizeFaceResponse(
                success=True,
                message=f"Face recognized as {matched_record.name}",
                recognized=True,
                name=matched_record.name,
                confidence=confidence,
                face_id=matched_record.id,
                email=matched_record.email,
                phone=matched_record.phone
            )
        else:
            # Log unknown face
            face_recognition_service.log_recognition(
                db=db,
                recognized_name=None,
                confidence=confidence,
                status="unknown"
            )
            
            return RecognizeFaceResponse(
                success=True,
                message="Face not recognized. Unknown person.",
                recognized=False,
                confidence=confidence
            )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/delete-face",
    response_model=DeleteFaceResponse,
    summary="Delete a face from the database",
    description="Deletes a face record from the database by ID or name."
)
async def delete_face(
    face_id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Delete a face from the database by ID or name
    """
    try:
        if not face_id and not name:
            raise HTTPException(
                status_code=400,
                detail="Either face_id or name must be provided"
            )
        
        deleted_count = face_recognition_service.delete_face(
            db=db,
            face_id=face_id,
            name=name
        )
        
        if deleted_count == 0:
            return DeleteFaceResponse(
                success=False,
                message="No face found with the provided criteria",
                deleted_count=0
            )
        
        return DeleteFaceResponse(
            success=True,
            message=f"Successfully deleted {deleted_count} face record(s)",
            deleted_count=deleted_count
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/list-faces",
    response_model=ListFacesResponse,
    summary="List all saved faces",
    description="Returns a list of all faces stored in the database."
)
async def list_faces(db: Session = Depends(get_db)):
    """
    List all faces in the database
    """
    try:
        all_faces = face_recognition_service.list_all_faces(db)
        
        face_infos = [
            FaceInfo(
                id=face.id,
                name=face.name,
                email=face.email,
                phone=face.phone,
                created_at=face.created_at,
                embedding_model=face.embedding_model
            )
            for face in all_faces
        ]
        
        return ListFacesResponse(
            success=True,
            message=f"Found {len(face_infos)} face(s) in the database",
            total_faces=len(face_infos),
            faces=face_infos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
