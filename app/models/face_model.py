"""
Database models for Face Recognition System
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class FaceRecord(Base):
    """
    Model to store face embeddings and identity information
    """
    __tablename__ = "face_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Face embedding stored as binary (numpy array serialized)
    face_embedding = Column(LargeBinary, nullable=False)
    
    # Additional metadata
    embedding_model = Column(String, default="VGG-Face")
    image_path = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FaceRecord(id={self.id}, name='{self.name}')>"


class RecognitionLog(Base):
    """
    Model to log face recognition attempts
    """
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recognized_name = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "success", "no_face", "unknown"
    
    def __repr__(self):
        return f"<RecognitionLog(id={self.id}, name='{self.recognized_name}', confidence={self.confidence_score})>"
