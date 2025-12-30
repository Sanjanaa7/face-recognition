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
    FaceInfo,
    RecognizedFace,
    MultiRecognizeFaceResponse,
    MultiSaveFaceResponse
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
        
        # Get face thumbnail
        thumbnail = face_detection_service.get_face_thumbnail_base64(img_array, detection_result['bounding_box'])
        
        # Save to database
        face_record = face_recognition_service.save_face(
            db=db,
            name=name,
            embedding=embedding,
            email=email,
            phone=phone,
            thumbnail=thumbnail
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
    "/save-multiple-faces",
    response_model=MultiSaveFaceResponse,
    summary="Save multiple faces to the database",
    description="Detects multiple faces in the image and saves them with the provided comma-separated names."
)
async def save_multiple_faces(
    names: str = Form(..., description="Comma-separated names for detected faces"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Save multiple faces:
    1. Detect all faces in image
    2. Split the 'names' string into a list
    3. Match names to detected faces sequentially
    4. Extract embeddings and save each to database
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect multiple faces
        detections, iw, ih = face_detection_service.detect_multiple_faces(img_array)
        
        if not detections:
            return MultiSaveFaceResponse(
                success=False,
                message="No faces detected in the image",
                saved_faces=[]
            )
        
        # Parse names
        name_list = [n.strip() for n in names.split(',')]
        
        saved_results = []
        for i, det in enumerate(detections):
            # Use name from list if available, else generic name
            name = name_list[i] if i < len(name_list) else f"Person_{i+1}"
            
            # Get face embedding
            embedding = face_detection_service.get_face_embedding(img_array, bbox=det['bounding_box'])
            
            if not embedding:
                saved_results.append(SaveFaceResponse(
                    success=False,
                    message=f"Failed to extract embedding for {name}"
                ))
                continue
            
            # Get face thumbnail
            thumbnail = face_detection_service.get_face_thumbnail_base64(img_array, det['bounding_box'])
            
            # Save to database
            face_record = face_recognition_service.save_face(
                db=db,
                name=name,
                embedding=embedding,
                thumbnail=thumbnail
            )
            
            saved_results.append(SaveFaceResponse(
                success=True,
                message=f"Face saved for {name}",
                face_id=face_record.id,
                name=face_record.name
            )
        )
        
        return MultiSaveFaceResponse(
            success=True,
            message=f"Attempted to save {len(detections)} face(s)",
            saved_faces=saved_results
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


@router.post(
    "/recognize-multiple-faces",
    response_model=MultiRecognizeFaceResponse,
    summary="Recognize multiple faces in an image",
    description="Detects all faces in the group photo and matches each against stored faces in the database."
)
async def recognize_multiple_faces(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Recognize multiple faces:
    1. Detect all faces in image
    2. For each face, extract embedding
    3. Compare with stored faces
    4. Return list of matched identities with confidence and bounding boxes
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Decode image
        img_array = face_detection_service.decode_image(image_data)
        
        # Detect multiple faces
        detections, iw, ih = face_detection_service.detect_multiple_faces(img_array)
        
        if not detections:
            return MultiRecognizeFaceResponse(
                success=True,
                message="No faces detected in the image",
                faces_detected=0,
                recognized_faces=[],
                image_meta={"width": iw, "height": ih}
            )
        
        recognized_faces = []
        
        for detection in detections:
            bbox = detection['bounding_box']
            
            # Get face embedding for this specific face
            embedding = face_detection_service.get_face_embedding(img_array, bbox=bbox)
            
            if not embedding:
                recognized_faces.append(RecognizedFace(
                    recognized=False,
                    name="Unknown",
                    confidence=0.0,
                    bounding_box=bbox
                ))
                continue
            
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
                
                recognized_faces.append(RecognizedFace(
                    recognized=True,
                    name=matched_record.name,
                    confidence=confidence,
                    face_id=matched_record.id,
                    email=matched_record.email,
                    phone=matched_record.phone,
                    bounding_box=bbox
                ))
            else:
                # Log unknown face
                face_recognition_service.log_recognition(
                    db=db,
                    recognized_name=None,
                    confidence=confidence,
                    status="unknown"
                )
                
                recognized_faces.append(RecognizedFace(
                    recognized=False,
                    name="Unknown",
                    confidence=confidence,
                    bounding_box=bbox
                ))
        
        return MultiRecognizeFaceResponse(
            success=True,
            message=f"Detected {len(detections)} face(s), recognized {len([f for f in recognized_faces if f.recognized])} face(s)",
            faces_detected=len(detections),
            recognized_faces=recognized_faces,
            image_meta={"width": iw, "height": ih}
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
