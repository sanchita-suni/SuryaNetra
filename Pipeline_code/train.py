from ultralytics import YOLO
import os

# CONFIG
DATA_YAML_PATH = "C:/dev/SuryaNetra/solar-panels-1/data.yaml"  
# Point to the LAST saved weight to resume
RESUME_WEIGHTS = "SuryaNetra_Runs/solar_detection_v1/weights/last.pt"

def train_model():
    print(f"🔄 Resuming Training from: {RESUME_WEIGHTS}")
    
    # Load the paused model
    model = YOLO(RESUME_WEIGHTS)  

    results = model.train(
        data=DATA_YAML_PATH,
        epochs=30,
        imgsz=640,
        batch=16,
        project='SuryaNetra_Runs',
        name='solar_detection_v1',
        resume=True,        # <--- CRITICAL: Tells YOLO to pick up where it left off
        
        # Keep augmentations consistent
        degrees=25.0,
        hsv_v=0.4,
        hsv_s=0.7,
        fliplr=0.5,
        mosaic=1.0,
    )
    
    print("✅ Training Complete!")

if __name__ == '__main__':
    train_model()