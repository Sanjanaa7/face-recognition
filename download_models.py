"""
Script to download all required DeepFace models.
Run this script once to ensure all models are downloaded and cached.
"""
import os
from deepface import DeepFace
import time
import numpy as np

def download_models():
    print("🚀 Starting model download check...")
    print("This will download the required AI models if they are not already present.")
    print("This is a ONE-TIME process. Please be patient.\n")

    # 1. Recognition Model (VGG-Face)
    print(f"⏳ Checking/Downloading VGG-Face model...")
    start = time.time()
    try:
        DeepFace.build_model("VGG-Face")
        elapsed = time.time() - start
        print(f"✅ VGG-Face model is ready! (Took {elapsed:.2f}s)")
    except Exception as e:
        print(f"❌ Failed to load VGG-Face: {e}")

    # 2. Analysis Models (Emotion, Age, Gender)
    # We trigger their download by running a dummy analysis
    print(f"⏳ Checking/Downloading Analysis models (Emotion, Age, Gender)...")
    try:
        # Create a dummy black image
        dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
        
        start = time.time()
        # This will download/load all attribute models
        DeepFace.analyze(
            img_path=dummy_img, 
            actions=['emotion', 'age', 'gender'],
            enforce_detection=False,
            silent=True
        )
        elapsed = time.time() - start
        print(f"✅ Analysis models are ready! (Took {elapsed:.2f}s)")
    except Exception as e:
        print(f"❌ Failed to load analysis models: {e}")
        print("   Please check your internet connection.")

    print("\n✨ All models are checked and ready!")
    print("You can now start the application with 'run.bat'.")

if __name__ == "__main__":
    download_models()
