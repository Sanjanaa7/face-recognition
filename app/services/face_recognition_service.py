"""
Face Recognition Service for database operations
"""
import numpy as np
import pickle
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.face_model import FaceRecord, RecognitionLog
from sklearn.metrics.pairwise import cosine_similarity


class FaceRecognitionService:
    """
    Service for face recognition and database operations
    """
    
    def __init__(self):
        self.similarity_threshold = 0.6  # Cosine similarity threshold
    
    def serialize_embedding(self, embedding: List[float]) -> bytes:
        """
        Serialize face embedding to bytes for database storage
        """
        embedding_array = np.array(embedding, dtype=np.float32)
        return pickle.dumps(embedding_array)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """
        Deserialize face embedding from bytes
        """
        return pickle.loads(embedding_bytes)
    
    def save_face(
        self,
        db: Session,
        name: str,
        embedding: List[float],
        email: Optional[str] = None,
        phone: Optional[str] = None,
        model_name: str = "VGG-Face"
    ) -> FaceRecord:
        """
        Save face embedding to database
        """
        # Serialize embedding
        embedding_bytes = self.serialize_embedding(embedding)
        
        # Create new face record
        face_record = FaceRecord(
            name=name,
            email=email,
            phone=phone,
            face_embedding=embedding_bytes,
            embedding_model=model_name
        )
        
        db.add(face_record)
        db.commit()
        db.refresh(face_record)
        
        return face_record
    
    def recognize_face(
        self,
        db: Session,
        embedding: List[float]
    ) -> Tuple[Optional[FaceRecord], float]:
        """
        Recognize face by comparing with stored embeddings
        Returns: (matched_record, confidence_score)
        """
        # Get all face records
        all_faces = db.query(FaceRecord).all()
        
        if not all_faces:
            return None, 0.0
        
        # Convert input embedding to numpy array
        input_embedding = np.array(embedding).reshape(1, -1)
        
        best_match = None
        best_similarity = -1.0
        
        # Compare with each stored face
        for face_record in all_faces:
            stored_embedding = self.deserialize_embedding(face_record.face_embedding)
            stored_embedding = stored_embedding.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(input_embedding, stored_embedding)[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = face_record
        
        # Check if similarity exceeds threshold
        if best_similarity >= self.similarity_threshold:
            return best_match, float(best_similarity)
        
        return None, float(best_similarity)
    
    def delete_face(self, db: Session, face_id: Optional[int] = None, name: Optional[str] = None) -> int:
        """
        Delete face record(s) from database
        Returns: number of deleted records
        """
        query = db.query(FaceRecord)
        
        if face_id is not None:
            query = query.filter(FaceRecord.id == face_id)
        elif name is not None:
            query = query.filter(FaceRecord.name == name)
        else:
            raise ValueError("Either face_id or name must be provided")
        
        deleted_count = query.delete()
        db.commit()
        
        return deleted_count
    
    def list_all_faces(self, db: Session) -> List[FaceRecord]:
        """
        List all face records in database
        """
        return db.query(FaceRecord).all()
    
    def log_recognition(
        self,
        db: Session,
        recognized_name: Optional[str],
        confidence: Optional[float],
        status: str
    ):
        """
        Log recognition attempt
        """
        log_entry = RecognitionLog(
            recognized_name=recognized_name,
            confidence_score=confidence,
            status=status
        )
        
        db.add(log_entry)
        db.commit()


# Singleton instance
face_recognition_service = FaceRecognitionService()
