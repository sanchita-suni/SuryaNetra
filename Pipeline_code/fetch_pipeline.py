import os
import requests
from PIL import Image
from io import BytesIO

# ---  ENTER YOUR GOOGLE MAPS API KEY HERE  ---
API_KEY = "api-key-goes-here" 

ZOOM_LEVEL = 20
IMAGE_SIZE = "640x640"
MAP_TYPE = "satellite"

def fetch_satellite_image(lat, lon, sample_id, output_dir):
    """
    Fetches image from Google Static Maps and saves to output_dir.
    """
    if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
        print("   ❌ ERROR: API Key not set in fetch_pipeline.py")
        return None

    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": f"{lat},{lon}",
        "zoom": ZOOM_LEVEL,
        "size": IMAGE_SIZE,
        "maptype": MAP_TYPE,
        "key": API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        if b"error_message" in response.content:
            print(f"   ❌ Google API Error: {response.content}")
            return None

        img = Image.open(BytesIO(response.content))
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{sample_id}.png"
        save_path = os.path.join(output_dir, filename)
        img.save(save_path)
        
        return save_path
        
    except Exception as e:
        print(f"   ❌ Fetch Failed for {sample_id}: {e}")
        return None