from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import date
import os

def generate_pdf(data, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFillColor(colors.HexColor("#0E1117"))
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 60, "SOLAR AUDIT REPORT")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 85, f"SuryaNetra | ID: {data.get('sample_id')} | Date: {date.today()}")
    
    c.setFillColor(colors.black)
    y = height - 150

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "1. AUDIT DETERMINATION")
    y -= 25
    c.setFont("Helvetica", 12)
    
    if data.get('has_solar'):
        status = "PASSED (Solar Detected)"
        color = colors.green
    else:
        status = "FAILED / REVIEW NEEDED"
        color = colors.red
        
    c.setFillColor(color)
    c.drawString(70, y, f"STATUS: {status}")
    y -= 40

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "2. TECHNICAL METRICS")
    y -= 25
    c.setFont("Helvetica", 12)
    
    area = data.get('pv_area_sqm_est', 0.0)
    conf = data.get('confidence', 0.0)
    zone = data.get('buffer_radius_sqft', 0)
    capacity = area * 0.15
    
    c.drawString(70, y, f"Confirmed Area: {area} m²")
    y -= 20
    c.drawString(70, y, f"System Capacity: {capacity:.2f} kW")
    y -= 20
    c.drawString(70, y, f"AI Confidence: {float(conf)*100:.1f}%")
    y -= 20
    c.drawString(70, y, f"Zone Compliance: {zone} sq.ft")
    y -= 40
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "3. AUDITOR NOTES")
    y -= 25
    c.setFont("Helvetica", 10)
    
    notes = data.get('qc_notes', [])
    note_text = ", ".join(notes) if isinstance(notes, list) else str(notes)
    
    text_object = c.beginText(70, y)
    text_object.setFont("Helvetica", 10)
    words = note_text.split()
    line = ""
    for word in words:
        if len(line) + len(word) > 80:
            text_object.textLine(line)
            line = word + " "
        else:
            line += word + " "
    text_object.textLine(line)
    c.drawText(text_object)
    
    # FOOTER
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.gray)
    c.drawString(50, 50, f"Integrity Hash: {data.get('integrity_hash', 'N/A')}")
    
    c.save()