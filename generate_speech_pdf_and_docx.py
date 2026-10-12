import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ReportLab imports for PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# -------------------------------------------------------------
# 1. DOCX GENERATION
# -------------------------------------------------------------
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_docx(filename):
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.text = "NE-SHIELD: AI Disaster Warning System | Official Presentation Speech Script"
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.runs[0].font.size = Pt(8.5)
        hp.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    # Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("NE-SHIELD: AI Disaster Early Warning System")
    r_title.bold = True
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = RGBColor(15, 23, 42) # #0F172A
    p_title.space_after = Pt(2)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Official Presentation & Demonstration Speech Script (Full Workflow Walkthrough)")
    r_sub.bold = True
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGBColor(2, 132, 199) # #0284C7
    p_sub.space_after = Pt(14)

    # Note Box
    t_note = doc.add_table(rows=1, cols=1)
    t_note.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_note = t_note.cell(0, 0)
    set_cell_background(c_note, "EFF6FF") # Light blue
    p_nb = c_note.paragraphs[0]
    r_nb = p_nb.add_run("SPEAKER INSTRUCTION: Read this script clearly and confidently during presentations, SIH evaluation panels, and jury demonstrations. Each section is broken down with spoken cues and technical justifications.")
    r_nb.font.size = Pt(9.5)
    r_nb.italic = True
    r_nb.font.color.rgb = RGBColor(30, 58, 138)
    doc.add_paragraph().space_after = Pt(8)

    sections = [
        (
            "1. Opening & Hook (The Problem Statement)",
            "Speak with steady pacing and make direct eye contact with the judges.",
            [
                "\"Respected judges and panel members, good morning/afternoon.",
                "Every year, mountainous regions across India suffer devastating landslides and flash floods. Hundreds of lives are lost, communities are displaced, and vital transit highways are abruptly cut off.",
                "The core flaw with existing disaster warning methods is that they rely on STATIC RAINFALL THRESHOLDS—such as issuing an alert only when rain crosses 100 millimeters. But terrain physics does not follow single-variable rules:",
                "• 100 millimeters of rain on dry, flat crystalline rock causes zero structural harm.",
                "• However, just 35 millimeters of rain on a steep slope saturated with subsurface water pressure can cause catastrophic slope collapse in minutes.",
                "To solve this life-critical challenge, we built NE-SHIELD: an end-to-end, Artificial Intelligence-powered Early Warning System that combines geotechnical soil mechanics with space-based Earth Observation from ISRO Bhuvan.\""
            ]
        ),
        (
            "2. Solution Overview (The AI Core)",
            "Point towards your live dashboard or interactive slides.",
            [
                "\"NE-SHIELD is not merely a passive monitoring dashboard; it is an intelligent, predictive forecasting engine.",
                "Instead of reacting after a disaster strikes, our system predicts landslides and flash floods 24 to 72 HOURS IN ADVANCE.",
                "It accomplishes this through a continuous 6-stage Artificial Intelligence Pipeline running in real-time.\""
            ]
        ),
        (
            "3. Stage-by-Stage Workflow Walkthrough",
            "Walk through each stage sequentially to show architectural maturity.",
            [
                "STAGE 1: MULTI-MODAL DATA INGESTION\n"
                "\"In Stage 1, our system continuously ingests synchronized environmental telemetry across four vectors:\n"
                "1. Meteorological rainfall intensity at 1h, 3h, 6h, 24h, and 72h intervals.\n"
                "2. Ground-level IoT geotechnical sensors measuring volumetric soil moisture % and piezometric pore water pressure in kPa.\n"
                "3. Topographical Digital Elevation Models extracting slope gradient, terrain aspect, and fault line proximities.\n"
                "4. And multispectral satellite imagery streamed live from ISRO Bhuvan (NRSC).\"",

                "STAGE 2: 20-DIMENSIONAL GEOTECHNICAL FEATURE TENSOR\n"
                "\"Raw sensor readings cannot predict disasters by themselves. In Stage 2, our Feature Engineering engine transforms multi-source data into a standardized 20-dimensional mathematical feature tensor.\n"
                "Here, we directly embed physical soil mechanics into our AI:\n"
                "• We compute the Antecedent Rainfall Index (ARI-7) to capture historical water retention.\n"
                "• We model Terzaghi's Effective Stress Principle—quantifying how underground hydrostatic pressure destroys resisting shear strength.\n"
                "• And we mathematically decompose circular compass bearings into sine and cosine coordinates.\"",

                "STAGE 3: MACHINE LEARNING ENSEMBLE CORE\n"
                "\"Stage 3 is the intelligent brain of NE-SHIELD.\n"
                "We deployed a production Gradient Tree Boosting Classifier ensemble comprising 80 boosting estimators.\n"
                "Why Gradient Boosting? Because tabular geotechnical data exhibits complex, non-linear threshold behaviors where tree ensembles mathematically outperform deep neural networks.\n"
                "Our model optimizes logistic loss through negative gradient boosting, focusing sequential trees specifically on challenging borderline failure conditions.\n"
                "Inference completes in UNDER 15 MILLISECONDS, enabling real-time spatial evaluation across hundreds of sensor nodes.\"",

                "STAGE 4: HYBRID SAFETY GATING & 4-TIER RISK BANDS\n"
                "\"To protect human life, Stage 4 merges probabilistic AI predictions with deterministic physical guardrails.\n"
                "The system classifies hazard into four calibrated operational bands:\n"
                "• 🟢 Low Risk (< 35%): Normal conditions.\n"
                "• 🟡 Moderate Risk (35% - 65%): Heightened monitoring activated.\n"
                "• 🟠 High Risk (65% - 85%): Warning issued; first responders alerted.\n"
                "• 🔴 Critical Risk (≥ 85%): Imminent slope failure; evacuation protocol triggered.\n"
                "Even if the AI probability is borderline, physical safety gates—such as sudden cloudbursts exceeding 25 mm/hr or pore pressure exceeding 60 kPa—automatically elevate alerts.\"",

                "STAGE 5: ISRO BHUVAN GIS COMMAND CENTER\n"
                "\"In Stage 5, predictions are projected onto our interactive GIS Command Center.\n"
                "Instead of relying on commercial paid mapping APIs like Google Maps, we integrated ISRO Bhuvan's Web Map Service (WMS).\n"
                "This equips disaster managers with authentic Indian space research multispectral satellite layers at ZERO recurring API license costs.\n"
                "On our live map, authorities can view color-coded pulsating danger zones, inspect real-time station telemetry, and trigger on-demand model retraining.\"",

                "STAGE 6: INCIDENT DISPATCH & CLOSED-LOOP RETRAINING\n"
                "\"Finally, in Stage 6, confirmed high and critical risks trigger automated dispatch via SMS gateways, webhooks, and Common Alerting Protocols (CAP) to District Disaster Management Authorities.\n"
                "Field verifications feed directly back into our database, allowing our AI models to retrain and adapt to changing monsoon patterns with ZERO backend downtime.\""
            ]
        ),
        (
            "4. Conclusion & Key Benchmark Metrics",
            "Deliver these numbers proudly and clearly.",
            [
                "\"To summarize our empirical results:\n"
                "• Overall Model Accuracy: 96.5%\n"
                "• ROC-AUC Score: 0.988 (demonstrating world-class class separation)\n"
                "• Disaster Recall / Sensitivity: 97.1% (ensuring life-threatening events are never missed)\n"
                "• Real-Time Inference Latency: Under 15 milliseconds\n"
                "• Complete system is containerized, cloud-deployable on free infrastructure, and ready for immediate deployment.\n\n"
                "Thank you very much. We are now open for your questions.\""
            ]
        )
    ]

    for title, cue, paras in sections:
        h = doc.add_paragraph()
        rh = h.add_run(title)
        rh.bold = True
        rh.font.size = Pt(13)
        rh.font.color.rgb = RGBColor(30, 58, 138)
        h.space_before = Pt(12)
        h.space_after = Pt(2)

        c = doc.add_paragraph()
        rc = c.add_run(f"[Delivery Cue: {cue}]")
        rc.italic = True
        rc.font.size = Pt(9)
        rc.font.color.rgb = RGBColor(100, 116, 139)
        c.space_after = Pt(6)

        for ptext in paras:
            p = doc.add_paragraph()
            rp = p.add_run(ptext)
            rp.font.size = Pt(10)
            rp.font.color.rgb = RGBColor(30, 41, 59)
            p.space_after = Pt(6)

    # Q&A Table
    doc.add_page_break()
    h_qa = doc.add_paragraph()
    rh_qa = h_qa.add_run("5. Common Evaluation Panel Q&A (Cheat Sheet)")
    rh_qa.bold = True
    rh_qa.font.size = Pt(14)
    rh_qa.font.color.rgb = RGBColor(30, 58, 138)
    h_qa.space_after = Pt(10)

    qa_list = [
        ("Why Gradient Tree Boosting instead of Deep Learning / CNNs?",
         "Tabular geotechnical telemetry has distinct physical thresholds (e.g. pore pressure limits). Tree ensembles handle heterogeneous numerical scales natively and outperform neural networks on regional tabular data without overfitting."),
        ("How did you integrate ISRO Bhuvan without API key issues?",
         "We integrated ISRO NRSC's open OGC-compliant Web Map Service (WMS) endpoint (https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms) into our Leaflet GIS engine, giving 100% free satellite layers with zero API keys."),
        ("What prevents false alarms in your system?",
         "Our 20-dimensional feature tensor includes Antecedent Rainfall (ARI-7) and subsurface pore water pressure. Rainfall alone will never trigger an evacuation alert unless underground ground saturation reaches the physical failure limit.")
    ]

    t_qa = doc.add_table(rows=1, cols=2)
    t_qa.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t_qa.rows[0].cells
    hdr[0].text = "Expected Question"
    hdr[1].text = "Recommended Spoken Answer"
    set_cell_background(hdr[0], "1E3A8A")
    set_cell_background(hdr[1], "1E3A8A")
    for cell in hdr:
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.bold = True
                r.font.size = Pt(9.5)

    for q, a in qa_list:
        row = t_qa.add_row().cells
        row[0].text = q
        row[1].text = a
        set_cell_background(row[0], "F8FAFC")
        set_cell_background(row[1], "FFFFFF")
        for cell in row:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(30, 41, 59)

    doc.save(filename)
    print(f"DOCX created: {filename}")


# -------------------------------------------------------------
# 2. PDF GENERATION
# -------------------------------------------------------------
class SpeechNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "NE-SHIELD: AI Disaster Warning System")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Official Presentation Speech Script")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 8.5 * inch - 54, 45)
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(54, 32, "NE-SHIELD AI Disaster Intelligence Core | Presentation Cue Sheet")
        self.drawRightString(8.5 * inch - 54, 32, page_str)
        self.restoreState()

def create_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=colors.HexColor("#0F172A"), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'PSubTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=colors.HexColor("#0284C7"), spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'PH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13, leading=17,
        textColor=colors.HexColor("#1E3A8A"), spaceBefore=12, spaceAfter=4,
        keepWithNext=True
    )
    cue_style = ParagraphStyle(
        'PCue', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8.5, leading=11,
        textColor=colors.HexColor("#64748B"), spaceAfter=6
    )
    speech_style = ParagraphStyle(
        'PSpeech', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=colors.HexColor("#1E293B"), spaceAfter=8
    )
    callout_style = ParagraphStyle(
        'PCallout', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=9, leading=13,
        textColor=colors.HexColor("#1E3A8A"), backColor=colors.HexColor("#EFF6FF"),
        borderColor=colors.HexColor("#93C5FD"), borderWidth=1,
        borderPadding=6, spaceBefore=4, spaceAfter=10
    )
    tbl_hdr = ParagraphStyle(
        'THdr', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white
    )
    tbl_cell = ParagraphStyle(
        'TCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor("#1E293B")
    )

    story = []
    story.append(Paragraph("NE-SHIELD: AI Disaster Early Warning System", title_style))
    story.append(Paragraph("Official Presentation & Demonstration Speech Script (Full Workflow Walkthrough)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284C7"), spaceAfter=10))

    story.append(Paragraph(
        "<b>SPEAKER INSTRUCTION:</b> Read this script clearly and confidently during presentations, SIH evaluation panels, and jury demonstrations. Each section includes spoken cues and technical justifications.",
        callout_style
    ))

    sections = [
        (
            "1. Opening & Hook (The Problem Statement)",
            "[Delivery Cue: Speak with steady pacing and make direct eye contact with the judges]",
            "\"Respected judges and panel members, good morning/afternoon.<br/><br/>"
            "Every year, mountainous regions across India suffer devastating landslides and flash floods. Hundreds of lives are lost, communities are displaced, and vital transit highways are abruptly cut off.<br/><br/>"
            "The core flaw with existing disaster warning methods is that they rely on <b>STATIC RAINFALL THRESHOLDS</b>—such as issuing an alert only when rain crosses 100 millimeters. But terrain physics does not follow single-variable rules:<br/>"
            "• 100 millimeters of rain on dry, flat crystalline rock causes zero structural harm.<br/>"
            "• However, just 35 millimeters of rain on a steep slope saturated with subsurface water pressure can cause catastrophic slope collapse in minutes.<br/><br/>"
            "To solve this life-critical challenge, we built <b>NE-SHIELD</b>: an end-to-end, Artificial Intelligence-powered Early Warning System that combines geotechnical soil mechanics with space-based Earth Observation from ISRO Bhuvan.\""
        ),
        (
            "2. Solution Overview (The AI Core)",
            "[Delivery Cue: Point towards your live dashboard or interactive slides]",
            "\"NE-SHIELD is not merely a passive monitoring dashboard; it is an intelligent, predictive forecasting engine.<br/><br/>"
            "Instead of reacting after a disaster strikes, our system predicts landslides and flash floods <b>24 to 72 HOURS IN ADVANCE</b>.<br/><br/>"
            "It accomplishes this through a continuous 6-stage Artificial Intelligence Pipeline running in real-time.\""
        ),
        (
            "3. Stage-by-Stage Workflow Walkthrough",
            "[Delivery Cue: Walk through each stage sequentially to show architectural depth]",
            "<b>STAGE 1: MULTI-MODAL DATA INGESTION</b><br/>"
            "\"In Stage 1, our system continuously ingests synchronized environmental telemetry across four vectors: meteorological rainfall intensity at 1h, 3h, 6h, 24h, and 72h intervals; ground-level IoT sensors measuring volumetric soil moisture % and pore water pressure in kPa; Digital Elevation Models extracting slope and faults; and multispectral satellite imagery streamed live from <b>ISRO Bhuvan (NRSC)</b>.\"<br/><br/>"
            "<b>STAGE 2: 20-DIMENSIONAL GEOTECHNICAL FEATURE TENSOR</b><br/>"
            "\"In Stage 2, our Feature Engineering engine transforms multi-source data into a standardized 20-dimensional mathematical feature tensor. Here, we directly embed physical soil mechanics into our AI: computing the Antecedent Rainfall Index (ARI-7), modeling Terzaghi's Effective Stress Principle, and encoding bedrock lithology.\"<br/><br/>"
            "<b>STAGE 3: MACHINE LEARNING ENSEMBLE CORE</b><br/>"
            "\"Stage 3 is the intelligent brain of NE-SHIELD. We deployed a production <b>Gradient Tree Boosting Classifier ensemble</b> comprising 80 boosting estimators. Tree ensembles handle tabular geotechnical data significantly better than neural networks. Inference completes in <b>UNDER 15 MILLISECONDS</b>, enabling real-time spatial evaluation across hundreds of sensor nodes.\"<br/><br/>"
            "<b>STAGE 4: HYBRID SAFETY GATING & 4-TIER RISK BANDS</b><br/>"
            "\"Stage 4 merges probabilistic AI predictions with deterministic physical guardrails across four calibrated bands: Low (<35%), Moderate (35%-65%), High (65%-85%), and Critical (≥85%). Physical safety gates—such as sudden cloudbursts >25 mm/hr or pore pressure >60 kPa—automatically elevate alerts to guarantee public safety.\"<br/><br/>"
            "<b>STAGE 5: ISRO BHUVAN GIS COMMAND CENTER</b><br/>"
            "\"In Stage 5, predictions are projected onto our interactive GIS Command Center. By integrating <b>ISRO Bhuvan's Web Map Service (WMS)</b>, we equip disaster authorities with authentic Indian satellite layers at ZERO recurring API license costs.\"<br/><br/>"
            "<b>STAGE 6: INCIDENT DISPATCH & CLOSED-LOOP RETRAINING</b><br/>"
            "\"Finally, in Stage 6, confirmed risks trigger automated alerts via SMS, webhooks, and CAP protocols to emergency authorities. Field verifications feed directly back into our database, allowing our AI models to retrain with ZERO backend downtime.\""
        ),
        (
            "4. Conclusion & Key Benchmark Metrics",
            "[Delivery Cue: Deliver these benchmark numbers proudly and clearly]",
            "\"To summarize our empirical results:<br/>"
            "• Overall Model Accuracy: <b>96.5%</b><br/>"
            "• ROC-AUC Score: <b>0.988</b> (demonstrating world-class class separation)<br/>"
            "• Disaster Recall / Sensitivity: <b>97.1%</b> (ensuring life-threatening events are never missed)<br/>"
            "• Real-Time Inference Latency: <b>Under 15 milliseconds</b><br/>"
            "• Complete system is containerized, cloud-deployable on free infrastructure, and ready for immediate deployment.<br/><br/>"
            "Thank you very much. We are now open for your questions.\""
        )
    ]

    for title, cue, speech in sections:
        story.append(Paragraph(title, h1_style))
        story.append(Paragraph(cue, cue_style))
        story.append(Paragraph(speech, speech_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Common Evaluation Panel Q&A (Cheat Sheet)", h1_style))

    qa_data = [
        [Paragraph("<b>Evaluation Question</b>", tbl_hdr), Paragraph("<b>Recommended Spoken Answer</b>", tbl_hdr)],
        [
            Paragraph("Why Gradient Boosting instead of Deep Learning / CNNs?", tbl_cell),
            Paragraph("Tabular geotechnical telemetry has distinct physical thresholds (e.g. pore pressure limits). Tree ensembles handle heterogeneous numerical scales natively and outperform neural networks on regional tabular data without overfitting.", tbl_cell)
        ],
        [
            Paragraph("How did you integrate ISRO Bhuvan without API key issues?", tbl_cell),
            Paragraph("We integrated ISRO NRSC's open OGC-compliant Web Map Service (WMS) endpoint (https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms) into our Leaflet GIS engine, giving 100% free satellite layers with zero API keys.", tbl_cell)
        ],
        [
            Paragraph("What prevents false alarms in your system?", tbl_cell),
            Paragraph("Our 20-dimensional feature tensor includes Antecedent Rainfall (ARI-7) and subsurface pore water pressure. Rainfall alone will never trigger an evacuation alert unless underground ground saturation reaches the physical failure limit.", tbl_cell)
        ]
    ]

    t_qa = Table(qa_data, colWidths=[180, 320])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1E3A8A")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_qa)

    doc.build(story, canvasmaker=SpeechNumberedCanvas)
    print(f"PDF created: {filename}")

if __name__ == '__main__':
    base_dir = os.getcwd()
    docx_file = os.path.join(base_dir, "NE-SHIELD_Presentation_Speech_Script.docx")
    pdf_file = os.path.join(base_dir, "NE-SHIELD_Presentation_Speech_Script.pdf")
    
    create_docx(docx_file)
    create_pdf(pdf_file)
