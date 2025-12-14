import os
import cv2
import json
import numpy as np
import hashlib
import pandas as pd
import math
from ultralytics import YOLO
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "Trained_model_file", "best.pt")
IMG_DIR = os.path.join(BASE_DIR, "output", "images")
JSON_OUT_DIR = os.path.join(BASE_DIR, "Prediction_files")
ARTIFACT_OUT_DIR = os.path.join(BASE_DIR, "output", "audits")
COORD_FILE = os.path.join(BASE_DIR, "input", "coordinates.xlsx")

FOOTER_HEIGHT_PX = 50   
EDGE_MARGIN_PX = 5      
ZOOM_LEVEL = 20         
DETECT_CONF = 0.10      
VERIFY_CONF = 0.40      
MIN_VALID_AREA = 1.0    
SHADOW_THRESH = 50      

def get_meters_per_pixel(latitude, zoom=ZOOM_LEVEL):
    return 156543.03392 * math.cos(math.radians(latitude)) / (2 ** zoom)

def calculate_area_sqm(box, scale):
    x1, y1, x2, y2 = box
    pixel_area = (x2 - x1) * (y2 - y1)
    return round(pixel_area * (scale ** 2), 2)

def generate_trust_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def check_image_quality(img):
    h, w = img.shape[:2]
    center = img[int(h*0.3):int(h*0.7), int(w*0.3):int(w*0.7)]
    gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) < SHADOW_THRESH:
        return False, f"Severe Shadow (Level: {np.mean(gray):.1f})"
    return True, "Clear"

def get_buffer_status_overlap(candidates, img_w, img_h, scale):
    """
    Checks if ANY part of the box overlaps with the buffer zones.
    This is more permissible than checking the center point.
    """
    if not candidates: return 0
    scale = float(scale)
    
    # Radius in Pixels
    r_1200_px = 5.96 / scale  
    r_2400_px = 8.42 / scale  
    
    cx, cy = img_w // 2, img_h // 2
    in_1200, in_2400 = False, False
    
    for item in candidates:
        x1, y1, x2, y2 = item['box']
        
        # Check if box intersects circle
        # Simple proximity check: closest point on box to circle center
        closest_x = max(x1, min(cx, x2))
        closest_y = max(y1, min(cy, y2))
        
        dist_x = cx - closest_x
        dist_y = cy - closest_y
        distance = np.sqrt(dist_x**2 + dist_y**2)
        
        if distance <= r_1200_px: in_1200 = True
        if distance <= r_2400_px: in_2400 = True
            
    if in_1200: return 1200
    if in_2400: return 2400
    return 0

def run_pipeline():
    print("🚀 Running SūryaNetra 'Overlap' Logic...")
    if not os.path.exists(MODEL_PATH): print("❌ No Model"); return
    model = YOLO(MODEL_PATH)
    
    coord_map = {}
    if os.path.exists(COORD_FILE):
        try:
            df = pd.read_excel(COORD_FILE)
            for _, row in df.iterrows():
                coord_map[str(row['sample_id'])] = {'lat': row['latitude'], 'lon': row['longitude']}
        except: pass
            
    os.makedirs(JSON_OUT_DIR, exist_ok=True)
    os.makedirs(ARTIFACT_OUT_DIR, exist_ok=True)
    
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.png', '.jpg'))]
    
    for f in files:
        sid = os.path.splitext(f)[0]
        img_path = os.path.join(IMG_DIR, f)
        img = cv2.imread(img_path)
        if img is None: continue
        h, w = img.shape[:2]
        
        site_data = coord_map.get(sid, {'lat': 20.5937, 'lon': 78.9629}) 
        scale = get_meters_per_pixel(site_data['lat'])
        
        # 1. Quality Check
        is_usable, quality_note = check_image_quality(img)
        
        # 2. Inference
        results = model(img_path, verbose=False, conf=DETECT_CONF)
        candidates = []
        max_conf = 0.0
        
        if results[0].boxes:
            for i, box in enumerate(results[0].boxes.xyxy):
                conf = float(results[0].boxes.conf[i])
                b = box.tolist()
                
                if b[3] > (h - FOOTER_HEIGHT_PX): continue
                if (b[0] < EDGE_MARGIN_PX) or (b[1] < EDGE_MARGIN_PX) or (b[2] > w - EDGE_MARGIN_PX): continue
                
                bw, bh = b[2]-b[0], b[3]-b[1]
                if min(bw, bh) == 0: continue
                if max(bw, bh) / min(bw, bh) > 4.5: continue 

                area = calculate_area_sqm(b, scale)
                candidates.append({'box': b, 'conf': conf, 'area': area})
                if conf > max_conf: max_conf = conf

        total_area = sum(c['area'] for c in candidates)
        buffer_val = get_buffer_status_overlap(candidates, w, h, scale)
        
        # 3. Decision Tree
        qc_status = "VERIFIABLE"
        has_solar = False
        qc_notes = []

        if not is_usable:
            qc_status = "NOT_VERIFIABLE"
            qc_notes.append(quality_note)
        elif not candidates:
            qc_status = "VERIFIABLE"
            has_solar = False
            qc_notes.append("Clear View: Empty Roof")
        else:
            is_valid_signal = (max_conf >= VERIFY_CONF) and (total_area >= MIN_VALID_AREA)
            
            if not is_valid_signal:
                qc_status = "VERIFIABLE"
                has_solar = False
                qc_notes.append("Ignored Noise (Weak Signal)")
            elif buffer_val > 0:
                qc_status = "VERIFIABLE"
                has_solar = True
                qc_notes.append(f"Solar Confirmed (Zone: {buffer_val})")
            else:
                qc_status = "VERIFIABLE"
                has_solar = False # Detected, but outside valid zone
                qc_notes.append("Solar Detected OUTSIDE 2400 sqft Limit")

        # 4. JSON Output
        rec = {
            "sample_id": sid, "lat": site_data['lat'], "lon": site_data['lon'],
            "has_solar": has_solar, "confidence": round(max_conf, 2),
            "pv_area_sqm_est": round(total_area, 2),
            "buffer_radius_sqft": buffer_val,
            "qc_status": qc_status, "qc_notes": qc_notes,
            "bbox_or_mask": str([c['box'] for c in candidates]) if candidates else "[]",
            "image_metadata": {"source": "Google Static Maps", "capture_date": str(date.today())}
        }
        rec['integrity_hash'] = generate_trust_hash(rec)
        
        with open(os.path.join(JSON_OUT_DIR, f"{sid}.json"), 'w') as jf: json.dump(rec, jf, indent=4)
    
        plot = img.copy()
        
        # Draw 1200 Ring (Yellow)
        cv2.circle(plot, (w//2, h//2), int(5.96/scale), (0, 255, 255), 1)
        # Draw 2400 Ring (Cyan)
        cv2.circle(plot, (w//2, h//2), int(8.42/scale), (255, 255, 0), 1)
        
        if candidates:
            for c in candidates:
                x1, y1, x2, y2 = map(int, c['box'])
                
                b_color = (0, 0, 255) 
                
                if (c['conf'] >= VERIFY_CONF):
                    # Check Overlap for individual box coloring
                    cx, cy = w//2, h//2
                    closest_x = max(x1, min(cx, x2))
                    closest_y = max(y1, min(cy, y2))
                    dist = np.sqrt((cx-closest_x)**2 + (cy-closest_y)**2)
                    
                    if dist <= (5.96/scale): b_color = (0, 255, 0)      # Green (1200)
                    elif dist <= (8.42/scale): b_color = (255, 165, 0)  # Orange/Cyan (2400)
                
                cv2.rectangle(plot, (x1, y1), (x2, y2), b_color, 2)
                cv2.putText(plot, f"{c['conf']:.2f}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, b_color, 1)

        status_text = f"SOLAR: {buffer_val}" if has_solar else "NO SOLAR"
        cv2.putText(plot, status_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if has_solar else (0, 0, 255), 2)
        cv2.imwrite(os.path.join(ARTIFACT_OUT_DIR, f"{sid}_audit.jpg"), plot)
        print(f"   👉 {sid}: {status_text} | Zone: {buffer_val}")

if __name__ == "__main__":
    run_pipeline()