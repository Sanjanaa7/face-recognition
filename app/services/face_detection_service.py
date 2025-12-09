"""
Face Detection Service using MediaPipe
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Dict, List, Tuple
from deepface import DeepFace
import base64
from io import BytesIO
from PIL import Image


class FaceDetectionService:
    """
    Service for face detection using MediaPipe and DeepFace
    """
    
    def __init__(self):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for short range (faster), 1 for full range
            min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            min_detection_confidence=0.5
        )
        
    def decode_image(self, image_data: bytes, max_size: int = 800) -> np.ndarray:
        """
        Decode image from bytes to numpy array and resize if too large
        """
        try:
            # Try to decode as base64 first
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data)
            
            # Convert to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Resize if too large (maintains aspect ratio)
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB numpy array
            image_np = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            return image_np
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    def detect_face(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect face in image and return bounding box
        """
        # Convert BGR to RGB for MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = self.face_detection.process(image_rgb)
        
        if not results.detections:
            return None
        
        # Get first detection
        detection = results.detections[0]
        
        # Get bounding box
        bboxC = detection.location_data.relative_bounding_box
        ih, iw, _ = image.shape
        
        bbox = {
            'x': int(bboxC.xmin * iw),
            'y': int(bboxC.ymin * ih),
            'width': int(bboxC.width * iw),
            'height': int(bboxC.height * ih)
        }
        
        # Ensure bbox is within image bounds
        bbox['x'] = max(0, bbox['x'])
        bbox['y'] = max(0, bbox['y'])
        bbox['width'] = min(iw - bbox['x'], bbox['width'])
        bbox['height'] = min(ih - bbox['y'], bbox['height'])
        
        # Get confidence score
        confidence = detection.score[0]
        
        return {
            'bounding_box': bbox,
            'confidence': float(confidence)
        }
    
    def _crop_face(self, image: np.ndarray, bbox: Dict) -> np.ndarray:
        """Helper to crop face from image using bbox"""
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        # Add a small margin (10%)
        margin_x = int(w * 0.1)
        margin_y = int(h * 0.1)
        
        start_y = max(0, y - margin_y)
        end_y = min(image.shape[0], y + h + margin_y)
        start_x = max(0, x - margin_x)
        end_x = min(image.shape[1], x + w + margin_x)
        
        return image[start_y:end_y, start_x:end_x]

    def get_face_embedding(self, image: np.ndarray, model_name: str = "VGG-Face", bbox: Optional[Dict] = None) -> Optional[List[float]]:
        """
        Extract face embedding using DeepFace.
        If bbox is provided, crops face first and skips DeepFace detection for speed.
        """
        try:
            # Determine input image
            if bbox:
                # Crop face and skip detection
                face_img = self._crop_face(image, bbox)
                detector_backend = 'skip'
            else:
                # Use full image and let DeepFace detect (slower)
                face_img = image
                detector_backend = 'opencv' # Faster than default

            # DeepFace expects RGB
            if len(face_img.shape) == 3:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            
            # Get embedding
            embedding_objs = DeepFace.represent(
                img_path=face_img,
                model_name=model_name,
                enforce_detection=False,
                detector_backend=detector_backend
            )
            
            if embedding_objs and len(embedding_objs) > 0:
                return embedding_objs[0]["embedding"]
            
            return None
        except Exception as e:
            print(f"Error getting face embedding: {str(e)}")
            return None
    
    def detect_landmarks(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect facial landmarks using MediaPipe Face Mesh
        Returns ALL 468 face mesh landmarks plus categorized groups
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        results = self.face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            return None
        
        # Get first face landmarks
        face_landmarks = results.multi_face_landmarks[0]
        
        ih, iw = image.shape[:2]
        
        # Extract ALL 468 landmarks with their coordinates
        all_landmarks = []
        for idx, lm in enumerate(face_landmarks.landmark):
            all_landmarks.append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        # MediaPipe Face Mesh landmark indices for categorized groups
        LEFT_EYE_INDICES = [33, 133, 160, 159, 158, 157, 173, 144, 145, 153, 154, 155]
        RIGHT_EYE_INDICES = [362, 263, 387, 386, 385, 384, 398, 373, 374, 380, 381, 382]
        NOSE_INDICES = [1, 2, 98, 327, 4, 5, 6, 19, 94, 141, 168, 195, 197]
        MOUTH_INDICES = [61, 291, 0, 17, 269, 405, 39, 40, 185, 314, 317, 402, 78, 308, 191, 80, 81, 82]
        FACE_OVAL_INDICES = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 
                             397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 
                             172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        LEFT_EYEBROW_INDICES = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
        RIGHT_EYEBROW_INDICES = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
        LIPS_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
        
        # Extract categorized landmarks
        categorized_landmarks = {
            'left_eye': [],
            'right_eye': [],
            'left_eyebrow': [],
            'right_eyebrow': [],
            'nose': [],
            'mouth': [],
            'lips': [],
            'face_oval': []
        }
        
        for idx in LEFT_EYE_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['left_eye'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in RIGHT_EYE_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['right_eye'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in LEFT_EYEBROW_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['left_eyebrow'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in RIGHT_EYEBROW_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['right_eyebrow'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in NOSE_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['nose'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in MOUTH_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['mouth'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in LIPS_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['lips'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        for idx in FACE_OVAL_INDICES:
            lm = face_landmarks.landmark[idx]
            categorized_landmarks['face_oval'].append({
                'index': idx,
                'x': float(lm.x * iw),
                'y': float(lm.y * ih),
                'z': float(lm.z)
            })
        
        return {
            'all_landmarks': all_landmarks,  # All 468 points
            'total_landmarks': len(all_landmarks),
            'categorized': categorized_landmarks  # Grouped by facial features
        }
    
    def analyze_face_deep(self, image: np.ndarray, bbox: Optional[Dict] = None) -> Optional[Dict]:
        """
        Deep face analysis: emotion, age, gender using DeepFace.
        If bbox is provided, crops face first and skips DeepFace detection for speed.
        """
        try:
            # Determine input image
            if bbox:
                face_img = self._crop_face(image, bbox)
                detector_backend = 'skip'
            else:
                face_img = image
                detector_backend = 'opencv'

            # Convert BGR to RGB
            if len(face_img.shape) == 3:
                image_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = face_img
            
            # Analyze face
            analysis = DeepFace.analyze(
                img_path=image_rgb,
                actions=['emotion', 'age', 'gender'],
                enforce_detection=False,
                detector_backend=detector_backend
            )
            
            if analysis and len(analysis) > 0:
                result = analysis[0]
                
                return {
                    'emotion': result['dominant_emotion'],
                    'emotion_scores': result['emotion'],
                    'age': int(result['age']),
                    'gender': result['dominant_gender'],
                    'gender_confidence': float(result['gender'][result['dominant_gender']])
                }
            
            return None
        except Exception as e:
            print(f"Error in deep face analysis: {str(e)}")
            return None
    
    def load_models(self):
        """
        Pre-load DeepFace models to avoid delay on first request
        """
        print("⏳ Pre-loading DeepFace models... This may take a moment.")
        try:
            # Pre-load VGG-Face (default for recognition)
            DeepFace.build_model("VGG-Face")
            print("✅ VGG-Face model loaded")
            
            # Pre-load analysis models (Emotion, Age, Gender)
            # We must use analyze() with a dummy image to trigger loading
            dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
            DeepFace.analyze(
                img_path=dummy_img,
                actions=['emotion', 'age', 'gender'],
                enforce_detection=False,
                silent=True
            )
            print("✅ Analysis models (Emotion, Age, Gender) loaded")
            
            print("✨ All DeepFace models pre-loaded successfully!")
        except Exception as e:
            print(f"⚠️ Warning: Could not pre-load models: {str(e)}")
            print("Models will be loaded on demand (first request will be slow).")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


# Singleton instance
face_detection_service = FaceDetectionService()
