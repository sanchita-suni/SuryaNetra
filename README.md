# 🛰️ SūryaNetra
### 🏆 EcoInnovators Ideathon 2026 Submission

[![Watch the Demo](Artefacts/auditor_dashboard.png)](https://drive.google.com/file/d/1WTkHUNNKU_nXKkVvq3th43Rs0rbY_zj8/view?usp=sharing)
> *Click the image above to watch the demo in action.*

---

## 🎯 The Challenge
**Objective:** Verify rooftop solar installations for the *PM Surya Ghar: Muft Bijli Yojana*.
**The Problem:** Field inspections are slow, and standard AI fails due to **GPS Drift** (satellite coordinates often miss the roof center).

## 💡 Our Solution: SūryaNetra
We built a governance-ready pipeline that combines **Computer Vision** with a **Citizen-Democratic Workflow**.

### Key Innovations
| Feature | Technical Implementation | Impact |
| :--- | :--- | :--- |
| **Swarm-Overlap Detection** | YOLOv8 + Geometric Intersection Logic | Solves GPS Drift by validating *overlap* rather than center-point containment. |
| **Dynamic Quantification** | Pixel-to-Meter conversion based on Latitude | Calculates accurate $m^2$ area for subsidy estimation. |
| **Citizen Appeal Loop** | Streamlit "Citizen Corner" Mode | Handles edge cases (tree cover, shadows) by letting citizens upload geotagged proof. |

---

## 📚 Data Sources & Citations
In compliance with the challenge guidelines, the following datasets were utilized for model training and validation:
* **Source 1:** Alfred Weber Institute of Economics (Roboflow).
* **Source 2:** LSG1547 Project (Roboflow).
* **Source 3:** Piscinas Y Tenistable (Roboflow).
* **Satellite Imagery:** Google Static Maps API and ESRI World Imagery.

---

## 📸 System Screenshots
| Auditor Dashboard | Citizen Appeal Interface |
| :---: | :---: |
| ![Auditor View](Artefacts/auditor_dashboard.png) | ![Citizen View](Artefacts/citizen_corner.png) |
| *Real-time detection with Red/Green buffer zones* | *Mobile-friendly proof upload for failed audits* |

---

## 📂 Repository Roadmap
This repository follows the submission guidelines:

* `Pipeline_code/` - The core Streamlit dashboard and inference logic.
* `Trained_model_file/` - Custom fine-tuned YOLOv8 model (`best.pt`).
* `Model_card/` - Detailed PDF explaining architecture and limitations.
* `Model_Training Logs/` - F1 Score and Loss metrics.
* `input/` - Uploaded .xlsx file is stored here
* `output/` - Output images, audits, citizen uploads and downloaded reports are saved here.
* `Prediction_files/` - JSON output files of the detections.
* `Artefacts/` - Sample detections and output proofs.

---

## 📄 Compliance: Mandatory JSON Output
Each verification site generates a JSON record in the `Prediction_files/` directory following the required schema:

```json
{
    "sample_id": "site_solar_2",
    "lat": 28.6295,
    "lon": 77.2137,
    "has_solar": true,
    "confidence": 0.64,
    "pv_area_sqm_est": 1109.02,
    "buffer_radius_sqft": 2400,
    "qc_status": "VERIFIABLE",
    "qc_notes": [
        "Solar Confirmed (Zone: 2400)"
    ],
    "bbox_or_mask": "[[253.45411682128906, 143.7777862548828, 365.323486328125, 223.3053436279297], [400.8895568847656, 34.69709014892578, 481.2196960449219, 103.09870147705078], [309.21197509765625, 78.72380065917969, 446.60357666015625, 173.71133422851562], [394.6480712890625, 26.056808471679688, 488.1163330078125, 113.26091003417969], [246.47344970703125, 128.05157470703125, 369.23175048828125, 236.1302490234375], [171.26089477539062, 158.91824340820312, 313.12237548828125, 269.7717590332031]]",
    "image_metadata": {
        "source": "Google Static Maps",
        "capture_date": "2025-12-14"
    },
    "integrity_hash": "06af5d67fe5672e52a8c97b2edba79bd305254377e529fb7f1911a0dab5c71d0"
}
```

---

## 🚀 Quick Start
**Local Installation**
1. Clone the repo:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/SuryaNetra.git](https://github.com/YOUR_USERNAME/SuryaNetra.git)
2. Install dependencies:
    ```bash
    pip install -r "Environment_details/requirements.txt"
3. Add Google Maps API Key:
   go to Pipeline_code/fetch_pipeline.py and replace "api-key-goes-here" with your API as directed
4. Run the pipeline:
    ```bash
    streamlit run "Pipeline_code/app.py" 
5. or use:
    ```bash
    python -m streamlit run "Pipeline_code/app.py"
