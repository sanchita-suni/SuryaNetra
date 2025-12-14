import streamlit as st
import pandas as pd
import json
import os
import sys
import time
import numpy as np
from streamlit_image_comparison import image_comparison
from datetime import date
import pydeck as pdk

# --- 1. SETUP & IMPORTS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(CURRENT_DIR)

try:
    from report import generate_pdf
    import fetch_pipeline
    import detect
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# Define Paths
DATA_PATHS = os.path.join(PARENT_DIR, "Prediction_files")
INPUT_EXCEL_PATH = os.path.join(PARENT_DIR, "input", "coordinates.xlsx")
OUTPUT_IMG_DIR = os.path.join(PARENT_DIR, "output", "images")
REQUESTS_DIR = os.path.join(PARENT_DIR, "output", "requests")
CITIZEN_UPLOADS_DIR = os.path.join(PARENT_DIR, "output", "citizen_uploads")
REPORT_DIR = os.path.join(PARENT_DIR, "output", "reports")

for d in [REQUESTS_DIR, CITIZEN_UPLOADS_DIR, OUTPUT_IMG_DIR, REPORT_DIR, os.path.dirname(INPUT_EXCEL_PATH)]: 
    os.makedirs(d, exist_ok=True)

st.set_page_config(page_title="SuryaNetra", page_icon="🛰️", layout="wide")

# --- 2. MULTILINGUAL DICTIONARY ---
LANG_MAP = {
    "English": "English",
    "हिन्दी": "Hindi",
    "ಕನ್ನಡ": "Kannada",
    "മലയാളം": "Malayalam",
    "తెలుగు": "Telugu",
    "தமிழ்": "Tamil"
}

LANG_DICT = {
    "English": {
        "lang_label": "Language",
        "app_name": "SuryaNetra",
        "subtitle": "Governance Portal",
        "mode_audit": "Official Audit Portal",
        "mode_citizen": "Citizen Corner",
        "status_verifiable": "VERIFIED SOLAR",
        "status_empty": "VERIFIED EMPTY",
        "status_fail": "NOT VERIFIABLE",
        "action_flag": "🚩 Flag for Citizen Review",
        "upload_label": "Upload Rooftop Proof",
        "met_sites": "Total Sites Audited",
        "met_cap": "Total Verified Capacity",
        "met_area": "Verified Solar Area",
        "met_carbon": "Carbon Offset"
    },
    "Hindi": {
        "lang_label": "भाषा",
        "app_name": "सूर्यनेत्र",
        "subtitle": "शासन पोर्टल",
        "mode_audit": "अधिकारी ऑडिट पोर्टल",
        "mode_citizen": "नागरिक सेवा",
        "status_verifiable": "सत्यापित (सौर ऊर्जा)",
        "status_empty": "सत्यापित (खाली छत)",
        "status_fail": "सत्यापन असफल",
        "action_flag": "🚩 नागरिक समीक्षा के लिए भेजें",
        "upload_label": "छत का फोटो अपलोड करें",
        "met_sites": "कुल साइटें",
        "met_cap": "कुल सत्यापित क्षमता",
        "met_area": "सत्यापित सौर क्षेत्र",
        "met_carbon": "कार्बन ऑफसेट"
    },
    "Kannada": {"lang_label": "ಭಾಷೆ", "app_name": "ಸೂರ್ಯನೇತ್ರ", "subtitle": "ಆಡಳಿತ ಪೋರ್ಟಲ್", "mode_audit": "ಅಧಿಕೃತ ಆಡಿಟ್ ಪೋರ್ಟಲ್", "mode_citizen": "ನಾಗರಿಕ ಸೇವೆ", "status_verifiable": "ಪರಿಶೀಲಿಸಲಾಗಿದೆ (ಸೌರ)", "status_empty": "ಪರಿಶೀಲಿಸಲಾಗಿದೆ (ಖಾಲಿ)", "status_fail": "ಪರಿಶೀಲಿಸಲಾಗಿಲ್ಲ", "action_flag": "🚩 ನಾಗರಿಕ ವಿಮರ್ಶೆಗೆ ಫ್ಲ್ಯಾಗ್ ಮಾಡಿ", "upload_label": "ರೂಫ್‌ಟಾಪ್ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "met_sites": "ಒಟ್ಟು ತಾಣಗಳು", "met_cap": "ಒಟ್ಟು ಪರಿಶೀಲಿಸಿದ ಸಾಮರ್ಥ್ಯ", "met_area": "ಪರಿಶೀಲಿಸಿದ ಸೌರ ಪ್ರದೇಶ", "met_carbon": "ಕಾರ್ಬನ್ ಆಫ್‌ಸೆಟ್"},
    "Malayalam": {"lang_label": "ഭാഷ", "app_name": "സൂര്യനേത്ര", "subtitle": "ഗവേണൻസ് പോർട്ടൽ", "mode_audit": "ഒഫീഷ്യൽ ഓഡിറ്റ് പോർട്ടൽ", "mode_citizen": "സിറ്റിസൺ കോർണർ", "status_verifiable": "വെരിഫൈ ചെയ്തു (സോളാർ)", "status_empty": "വെരിഫൈ ചെയ്തു (ശൂന്യം)", "status_fail": "വെരിഫൈ ചെയ്യാൻ സാധിക്കില്ല", "action_flag": "🚩 സിറ്റിസൺ റിവ്യൂവിനായി ഫ്ലാഗ് ചെയ്യുക", "upload_label": "റൂഫ്‌ടോപ്പ് ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക", "met_sites": "ആകെ സൈറ്റുകൾ", "met_cap": "ആകെ ശേഷി", "met_area": "സോളാർ ഏരിയ", "met_carbon": "കാർബൺ ഓഫ്‌സെറ്റ്"},
    "Telugu": {"lang_label": "భాష", "app_name": "సూర్యనేత్ర", "subtitle": "గవర్నెన్స్ పోర్టల్", "mode_audit": "అధికారిక ఆడిట్ పోర్టల్", "mode_citizen": "పౌర సేవలు", "status_verifiable": "ధృవీకరించబడింది (సోలార్)", "status_empty": "ధృవీకరించబడింది (ఖాళీ)", "status_fail": "ధృవీకరించబడలేదు", "action_flag": "🚩 పౌర సమీక్ష కోసం ఫ్లాగ్ చేయండి", "upload_label": "రూఫ్‌టాప్ ఫోటో అప్‌లోడ్ చేయండి", "met_sites": "మొత్తం సైట్లు", "met_cap": "మొత్తం సామర్థ్యం", "met_area": "సౌర విస్తీర్ణం", "met_carbon": "కార్బన్ ఆఫ్సెట్"},
    "Tamil": {"lang_label": "மொழி", "app_name": "சூர்யநேத்ரா", "subtitle": "நிர்வாக போர்டல்", "mode_audit": "அதிகாரப்பூர்வ தணிக்கை போர்டல்", "mode_citizen": "குடிமக்கள் சேவை", "status_verifiable": "சரிபார்க்கப்பட்டது (சோலார்)", "status_empty": "சரிபார்க்கப்பட்டது (காலியானது)", "status_fail": "சரிபார்க்க முடியவில்லை", "action_flag": "🚩 குடிமக்கள் மதிப்பாய்வுக்காகக் கொடியிடவும்", "upload_label": "மேற்கூரை புகைப்படத்தைப் பதிவேற்றவும்", "met_sites": "மொத்த தளங்கள்", "met_cap": "மொத்த திறன்", "met_area": "சோலார் பகுதி", "met_carbon": "கார்பன் ஆஃப்செட்"}
}

# --- 3. CSS ---
st.markdown("""
    <style>
    div[data-testid="stIframe"] { width: 100% !important; }
    iframe { width: 100% !important; min-width: 100% !important; }
    div.stButton > button:first-child { width: 100%; border-radius: 5px; border: 1px solid #ddd; }
    .metric-box { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #2ecc71; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a !important; margin-bottom: 10px; }
    .metric-value { font-size: 28px; font-weight: 800; color: #2e7d32 !important; margin: 0; }
    .metric-label { font-size: 14px; color: #333 !important; text-transform: uppercase; font-weight: 700; }
    .big-band-pass { padding: 15px; background-color: #d1e7dd; color: #0f5132; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #0f5132; }
    .big-band-fail { padding: 15px; background-color: #f8d7da; color: #842029; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #842029; }
    .big-band-warn { padding: 15px; background-color: #fff3cd; color: #664d03; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #664d03; }
    .big-band-appeal { padding: 15px; background-color: #cff4fc; color: #055160; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #b6effb; }
    .report-paper { background-color: white; color: black !important; padding: 30px; border: 1px solid #ddd; border-radius: 4px; font-family: 'Times New Roman', serif; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPERS ---
@st.cache_data
def load_data():
    data = []
    if os.path.exists(DATA_PATHS):
        for f in os.listdir(DATA_PATHS):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(DATA_PATHS, f)) as file: data.append(json.load(file))
                except: pass
    df = pd.DataFrame(data)
    if not df.empty and 'sample_id' in df.columns:
        df['sample_id'] = df['sample_id'].astype(str)
        df = df.drop_duplicates(subset=['sample_id'], keep='last')
    return df

def sanitize_json(data):
    if isinstance(data, dict): return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list): return [sanitize_json(i) for i in data]
    elif isinstance(data, (np.int64, np.int32)): return int(data)
    elif isinstance(data, (np.float64, np.float32)): return float(data)
    elif isinstance(data, (np.bool_)): return bool(data)
    return data

def save_record(data):
    sid = data['sample_id']
    file_path = os.path.join(DATA_PATHS, f"{sid}.json")
    with open(file_path, 'w') as f: json.dump(sanitize_json(data), f, indent=4)
    load_data.clear()

def update_status(sid, new_status, has_solar_bool, note=None):
    file_path = os.path.join(DATA_PATHS, f"{sid}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f: data = json.load(f)
        data['qc_status'] = new_status
        data['has_solar'] = has_solar_bool
        if note:
            if 'qc_notes' not in data: data['qc_notes'] = []
            data['qc_notes'].append(note)
        save_record(data)

# --- 5. SESSION STATE INIT ---
if 'target_id' not in st.session_state: st.session_state['target_id'] = None
if 'current_view' not in st.session_state: st.session_state['current_view'] = "Audits"
if 'lang_idx' not in st.session_state: st.session_state['lang_idx'] = 0

# --- 6. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/solar-panel.png", width=80)
    current_lang_key = list(LANG_MAP.values())[st.session_state['lang_idx']]
    st.markdown(f"**{LANG_DICT[current_lang_key]['lang_label']}**")
    native_lang = st.selectbox("Language", list(LANG_MAP.keys()), index=st.session_state['lang_idx'], label_visibility="collapsed")
    new_idx = list(LANG_MAP.keys()).index(native_lang)
    if new_idx != st.session_state['lang_idx']:
        st.session_state['lang_idx'] = new_idx
        st.rerun()
    lang_key = LANG_MAP[native_lang]
    L = LANG_DICT[lang_key]
    st.title(L["app_name"])
    st.caption(L["subtitle"])
    mode = st.radio("System Mode", ["Official Audit Portal", "Citizen Corner"])
    st.divider()

# ==========================================
# MODE 1: OFFICIAL AUDITOR DASHBOARD
# ==========================================
if mode == "Official Audit Portal":
    st.title(f"🛰️ {L['app_name']} Dashboard")
    df = load_data()
    
    if df.empty:
        st.info("System Initialized. Run an audit to begin.")
    else:
        # METRICS
        verified_df = df[(df['qc_status'] == 'VERIFIABLE') & (df['has_solar'] == True)]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'''<div class="metric-box"><p class="metric-value">{len(df)}</p><p class="metric-label">{L["met_sites"]}</p></div>''', unsafe_allow_html=True)
        c2.markdown(f'''<div class="metric-box"><p class="metric-value">{(verified_df['pv_area_sqm_est'].sum() * 0.15):.1f} kW</p><p class="metric-label">{L["met_cap"]}</p></div>''', unsafe_allow_html=True)
        c3.markdown(f'''<div class="metric-box"><p class="metric-value">{verified_df['pv_area_sqm_est'].sum():.1f} m²</p><p class="metric-label">{L["met_area"]}</p></div>''', unsafe_allow_html=True)
        c4.markdown(f'''<div class="metric-box"><p class="metric-value">{(verified_df['pv_area_sqm_est'].sum() * 0.15 * 1.2):.1f}</p><p class="metric-label">{L["met_carbon"]} (Tons)</p></div>''', unsafe_allow_html=True)
        st.write("") 

    nav_c1, nav_c2, nav_c3 = st.columns(3)
    if nav_c1.button("📋 Audits", type="primary" if st.session_state['current_view']=="Audits" else "secondary"): 
        st.session_state['current_view'] = "Audits"; st.rerun()
    if nav_c2.button("🔍 Inspection", type="primary" if st.session_state['current_view']=="Inspection" else "secondary"): 
        st.session_state['current_view'] = "Inspection"; st.rerun()
    if nav_c3.button("🚀 New", type="primary" if st.session_state['current_view']=="New" else "secondary"): 
        st.session_state['current_view'] = "New"; st.rerun()
    st.markdown("---")

    # VIEW 1: AUDITS
    if st.session_state['current_view'] == "Audits":
        if not df.empty:
            view_df = df.copy()
            view_df['sort_key'] = view_df['qc_status'].apply(lambda x: 0 if 'PENDING' in x else 1)
            view_df = view_df.sort_values('sort_key')
            st.dataframe(view_df[['sample_id', 'qc_status', 'has_solar', 'pv_area_sqm_est', 'confidence']], use_container_width=True)
        else: st.write("No data in queue.")

    # VIEW 2: INSPECTION
    elif st.session_state['current_view'] == "Inspection":
        if df.empty: st.warning("No data.")
        else:
            col_sel, _ = st.columns([3, 1])
            with col_sel:
                ids = list(df['sample_id'])
                default_idx = ids.index(st.session_state['target_id']) if st.session_state['target_id'] in ids else 0
                selected_id = st.selectbox("Select ID to Inspect:", ids, index=default_idx)
            
            if selected_id != st.session_state['target_id']: st.session_state['target_id'] = selected_id

            if selected_id:
                rec = df[df['sample_id'] == selected_id].iloc[0]
                status = rec['qc_status']
                
                # STATUS BANDS
                if status == "VERIFIABLE":
                    color = "big-band-pass" if rec['has_solar'] else "big-band-warn"
                    txt = L["status_verifiable"] if rec['has_solar'] else L["status_empty"]
                    st.markdown(f'<div class="{color}">{txt}</div>', unsafe_allow_html=True)
                elif status == "PENDING_CITIZEN_APPEAL":
                     st.markdown(f'<div class="big-band-appeal">📢 CITIZEN APPEAL PENDING</div>', unsafe_allow_html=True)
                elif status == "PENDING_AUDITOR_FLAG":
                     st.markdown(f'<div class="big-band-warn">⏳ AWAITING CITIZEN PROOF</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="big-band-fail">❌ {L["status_fail"]}</div>', unsafe_allow_html=True)
                st.write("")
                
                # CONTENT
                c_img, c_map = st.columns([2, 1])
                with c_img:
                    st.subheader("👁️ AI Analysis")
                    img_raw = os.path.join(OUTPUT_IMG_DIR, f"{selected_id}.png")
                    img_audit = os.path.join(PARENT_DIR, "output", "audits", f"{selected_id}_audit.jpg")
                    if os.path.exists(img_raw) and os.path.exists(img_audit):
                        image_comparison(img1=img_raw, img2=img_audit, label1="Raw", label2="AI Overlay", width=800)
                    else: st.warning("Images missing.")
                
                with c_map:
                    st.subheader("📍 Location")
                    view_state = pdk.ViewState(latitude=rec['lat'], longitude=rec['lon'], zoom=19)
                    layer = pdk.Layer("ScatterplotLayer", data=pd.DataFrame([rec]), get_position=["lon", "lat"], get_fill_color=[0, 0, 255], get_radius=5)
                    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
                    
                    # --- ACTION BLOCK (STRICT SEPARATION) ---
                    proof_path = os.path.join(CITIZEN_UPLOADS_DIR, f"{selected_id}_proof.jpg")
                    
                    # 1. AI FAILED -> Auditor sees "Flag"
                    if status == "NOT_VERIFIABLE":
                        st.info("📢 Verification Actions")
                        if st.button(L["action_flag"]):
                            update_status(selected_id, "PENDING_AUDITOR_FLAG", False, "Flagged by Auditor")
                            st.rerun()

                    # 2. FLAGGED -> Auditor waits
                    elif status == "PENDING_AUDITOR_FLAG":
                        st.info("⏳ Notification sent. Waiting for Citizen Proof...")

                    # 3. APPEAL SUBMITTED -> Auditor sees "Accept/Reject"
                    elif status == "PENDING_CITIZEN_APPEAL":
                        st.info("📢 Review Citizen Evidence")
                        if os.path.exists(proof_path): st.image(proof_path, caption="Citizen Uploaded Proof", width=300)
                        
                        b1, b2, b3 = st.columns(3)
                        if b1.button("✅ Accept Solar"):
                            update_status(selected_id, "VERIFIABLE", True, "Solar Verified by Auditor")
                            st.session_state['target_id'] = selected_id 
                            st.session_state['current_view'] = "Inspection" 
                            st.rerun() 
                        if b2.button("⚠️ Verify Empty"):
                            update_status(selected_id, "VERIFIABLE", False, "Confirmed Empty by Auditor")
                            st.session_state['target_id'] = selected_id
                            st.session_state['current_view'] = "Inspection"
                            st.rerun() 
                        if b3.button("❌ Reject Evidence"):
                            update_status(selected_id, "NOT_VERIFIABLE", False, "Evidence Rejected - Re-upload Requested")
                            st.session_state['target_id'] = selected_id
                            st.session_state['current_view'] = "Inspection"
                            st.rerun() 
                            
                    elif status == "VERIFIABLE":
                        st.success("Record Verified.")
                        if st.button("Unlock for Re-Review"):
                            update_status(selected_id, "NOT_VERIFIABLE", False, "Re-opened by Auditor")
                            st.session_state['target_id'] = selected_id
                            st.session_state['current_view'] = "Inspection"
                            st.rerun()

                # REPORT EDITOR
                st.markdown("---")
                st.subheader("📝 Official Report Editor")
                
                curr_area = float(rec['pv_area_sqm_est']) if pd.notnull(rec['pv_area_sqm_est']) else 0.0
                curr_conf = float(rec['confidence']) if pd.notnull(rec['confidence']) else 0.0
                raw_notes = rec.get('qc_notes', [])
                notes_str = ", ".join([str(x) for x in raw_notes]) if isinstance(raw_notes, list) else str(raw_notes).replace('[','').replace(']','').replace("'", "")

                c_edit, c_prev = st.columns(2)
                with c_edit:
                    st.markdown("**1. Edit Parameters**")
                    new_status = st.selectbox("Verification", ["PASSED", "FAILED"], index=0 if rec['has_solar'] else 1)
                    new_area = st.number_input("Confirmed Area (m²)", value=curr_area, step=0.1)
                    new_conf = st.slider("Confidence", 0.0, 1.0, curr_conf)
                    new_notes = st.text_area("Remarks", value=notes_str, height=150)
                    if st.button("💾 SAVE & GENERATE PDF", type="primary"):
                        updated_rec = rec.to_dict()
                        updated_rec['has_solar'] = (new_status == "PASSED")
                        updated_rec['qc_status'] = "VERIFIABLE" if new_status == "PASSED" else "NOT_VERIFIABLE"
                        updated_rec['pv_area_sqm_est'] = new_area
                        updated_rec['confidence'] = new_conf
                        updated_rec['qc_notes'] = [n.strip() for n in new_notes.split(',')]
                        save_record(updated_rec)
                        pdf_path = os.path.join(REPORT_DIR, f"{selected_id}_audit.pdf")
                        generate_pdf(updated_rec, pdf_path)
                        st.session_state['target_id'] = selected_id
                        st.session_state['current_view'] = "Inspection"
                        st.toast("✅ Saved!")
                        st.rerun()

                with c_prev:
                    st.markdown("**2. Live Document Preview**")
                    with st.container():
                        st.markdown(f"""<div class="report-paper">
                            <h2 style="text-align: center; border-bottom: 2px solid black;">SOLAR AUDIT REPORT</h2>
                            <p style="text-align: center;">SuryaNetra | ID: {selected_id} | {date.today()}</p>
                            <br><h4>1. DETERMINATION</h4>
                            <p><b>STATUS:</b> <span style="color: {'green' if new_status == 'PASSED' else 'red'}; font-weight: bold;">{new_status}</span></p>
                            <br><h4>2. TECHNICAL METRICS</h4>
                            <ul style="list-style-type: none; padding-left: 0;">
                                <li><b>Area:</b> {new_area} m²</li>
                                <li><b>Capacity:</b> {new_area * 0.15:.2f} kW</li>
                                <li><b>Confidence:</b> {new_conf*100:.1f}%</li>
                            </ul>
                            <br><h4>3. NOTES</h4><p>{new_notes}</p></div>""", unsafe_allow_html=True)
                    
                    pdf_path = os.path.join(REPORT_DIR, f"{selected_id}_audit.pdf")
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f: st.download_button("⬇️ Download PDF", f, file_name=f"{selected_id}_audit.pdf")
                with st.expander("View System JSON"): st.json(sanitize_json(rec.to_dict()))

    elif st.session_state['current_view'] == "New":
        c_single, c_batch = st.columns(2)
        with c_single:
            st.subheader("Single Run")
            slat = st.number_input("Lat", value=28.6139, format="%.5f")
            slon = st.number_input("Lon", value=77.2090, format="%.5f")
            if 'session_id' not in st.session_state: st.session_state['session_id'] = f"test_{int(time.time())}"
            sid = st.text_input("ID", value=st.session_state['session_id'])
            if st.button("Audit"):
                with st.spinner("Analyzing..."):
                    fetch_pipeline.fetch_satellite_image(slat, slon, sid, OUTPUT_IMG_DIR)
                    if os.path.exists(INPUT_EXCEL_PATH): df_c = pd.read_excel(INPUT_EXCEL_PATH)
                    else: df_c = pd.DataFrame(columns=['sample_id','latitude','longitude'])
                    new_row = {'sample_id': sid, 'latitude': slat, 'longitude': slon}
                    df_c = pd.concat([df_c[df_c['sample_id'].astype(str) != sid], pd.DataFrame([new_row])], ignore_index=True)
                    df_c.to_excel(INPUT_EXCEL_PATH, index=False)
                    detect.run_pipeline()
                st.session_state['target_id'] = sid
                st.session_state['current_view'] = "Inspection"
                load_data.clear()
                st.success("Run Complete!")
                st.rerun()

        with c_batch:
            st.subheader("Batch")
            up = st.file_uploader("Upload Excel", type=['xlsx'])
            if up and st.button("Start"):
                with open(INPUT_EXCEL_PATH, "wb") as f: f.write(up.getbuffer())
                df_up = pd.read_excel(INPUT_EXCEL_PATH)
                bar = st.progress(0)
                for i, row in df_up.iterrows():
                    fetch_pipeline.fetch_satellite_image(row['latitude'], row['longitude'], str(row['sample_id']), OUTPUT_IMG_DIR)
                    bar.progress((i+1)/len(df_up)*0.5)
                detect.run_pipeline()
                bar.progress(1.0)
                load_data.clear()
                if not df_up.empty: st.session_state['target_id'] = str(df_up.iloc[0]['sample_id'])
                st.session_state['current_view'] = "Inspection"
                st.success("Batch Complete!")
                st.rerun()

# ==========================================
# MODE 2: CITIZEN
# ==========================================
elif mode == "Citizen Corner":
    st.title(f"🏡 Citizen Corner")
    cid = st.text_input("Consumer ID")
    
    if cid:
        df = load_data()
        if not df.empty and cid in df['sample_id'].values:
            rec = df[df['sample_id'] == cid].iloc[0]
            status = rec.get('qc_status', 'NOT_VERIFIABLE')
            
            if status == "VERIFIABLE" and rec['has_solar']:
                st.balloons()
                st.success(f"✅ VERIFIED SOLAR")
                pdf_path = os.path.join(REPORT_DIR, f"{cid}_audit.pdf")
                if not os.path.exists(pdf_path): generate_pdf(rec.to_dict(), pdf_path)
                st.markdown("### 📄 Official Documents")
                with open(pdf_path, "rb") as f: st.download_button("⬇️ Download Certificate", f, file_name=f"{cid}_certificate.pdf", type="primary")

            elif status == "PENDING_AUDITOR_FLAG":
                st.warning("⚠️ Action Required: Please upload rooftop proof.")
                up_proof = st.file_uploader(L["upload_label"], type=['jpg', 'png'])
                if up_proof:

                    with open(os.path.join(CITIZEN_UPLOADS_DIR, f"{cid}_proof.jpg"), "wb") as f: f.write(up_proof.getbuffer())

                    if st.button("Submit Appeal"):
                        update_status(cid, "PENDING_CITIZEN_APPEAL", False, "Citizen Initiated Appeal")
                        st.success("Filed! Appeal is now under review.")
                        st.rerun()
            
            elif status == "PENDING_CITIZEN_APPEAL":
                st.info("ℹ️ Your appeal has been submitted and is under review.")
                
            else:
                st.error(f"❌ NOT VERIFIABLE")
                st.write(f"Reason: {rec.get('qc_notes', ['Unknown'])[0]}")
                pdf_path = os.path.join(REPORT_DIR, f"{cid}_audit.pdf")
                if not os.path.exists(pdf_path): generate_pdf(rec.to_dict(), pdf_path)
                with open(pdf_path, "rb") as f: st.download_button("⬇️ Download Report", f, file_name=f"{cid}_report.pdf")
                
                with st.expander("File Appeal"):
                    appeal_proof = st.file_uploader("Upload Proof", type=['jpg', 'png'], key="appeal")
                    if appeal_proof:
                        with open(os.path.join(CITIZEN_UPLOADS_DIR, f"{cid}_proof.jpg"), "wb") as f: f.write(appeal_proof.getbuffer())

                        if st.button("Submit Appeal"):
                            update_status(cid, "PENDING_CITIZEN_APPEAL", False, "Citizen Initiated Appeal")
                            st.success("Filed!")
                            st.rerun()
        else:
            st.warning("ID Not Found.")