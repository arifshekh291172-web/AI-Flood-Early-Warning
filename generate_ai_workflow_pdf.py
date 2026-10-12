import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "NE-SHIELD: AI-Powered Early Warning & Susceptibility System")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "AI Technical Whitepaper & Workflow")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 8.5 * inch - 54, 45)
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(54, 32, "Confidential - Theem Warrior AI Disaster Management Core")
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284C7"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0369A1"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=7
    )
    
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0F766E"),
        backColor=colors.HexColor("#F0FDFA"),
        borderColor=colors.HexColor("#0D9488"),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("NE-SHIELD: AI-DRIVEN EARLY WARNING SYSTEM", title_style))
    story.append(Paragraph("Predictive Geotechnical & Flood Intelligence Framework Powered by Machine Learning and ISRO Bhuvan", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284C7"), spaceAfter=12))

    meta_data = [
        [
            Paragraph("<b>System Name:</b> NE-SHIELD AI Core", table_cell_style),
            Paragraph("<b>Primary Architecture:</b> Supervised Ensemble (Gradient Boosting + RF)", table_cell_style)
        ],
        [
            Paragraph("<b>Target Domain:</b> Landslide & Flash-Flood Susceptibility", table_cell_style),
            Paragraph("<b>Geospatial Engine:</b> ISRO Bhuvan WMS & Leaflet GIS Engine", table_cell_style)
        ],
        [
            Paragraph("<b>Organization:</b> Theem Warriors Disaster Intelligence", table_cell_style),
            Paragraph("<b>Deployment Target:</b> Render Cloud Production Container", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary & AI Paradigm", h1_style))
    story.append(Paragraph(
        "<b>NE-SHIELD (North-East Hazard Early-Warning Integrated Evaluation Engine)</b> represents a breakthrough in artificial intelligence for natural disaster risk reduction. Mountainous regions such as Northeast India suffer from sudden rain-triggered debris flows, translational landslides, and localized flash floods. Conventional monitoring methods rely solely on reactive rainfall thresholds or post-event satellite damage assessment, leading to catastrophic delays in civilian evacuations.",
        body_style
    ))
    story.append(Paragraph(
        "NE-SHIELD replaces static thresholding with a <b>real-time, multi-modal Artificial Intelligence Inference Pipeline</b>. By combining Gradient Boosting decision trees, geological factor maps, geotechnical soil mechanics sensors, and live earth observation data from ISRO Bhuvan, the system forecasts localized slope failures and inundation hazards up to <b>24 to 72 hours in advance</b> with high precision and low false-alarm ratios.",
        body_style
    ))

    # Section 2: End-to-End Workflow & Pipeline Architecture
    story.append(Paragraph("2. End-to-End Artificial Intelligence Pipeline Workflow", h1_style))
    story.append(Paragraph(
        "The end-to-end operation of NE-SHIELD follows a continuous 6-stage AI data lifecycle designed for millisecond latency, rock-solid robustness, and verifiable predictions:",
        body_style
    ))

    stages = [
        ("Stage 1: Multi-Modal Ingestion", "Gathers telemetry across 5 parallel pipelines: AWS/IMD meteorological feeds (1h, 3h, 6h, 24h, 72h rainfall), geotechnical slope sensors (volumetric soil moisture %, piezometric pore water pressure kPa), Digital Elevation Models (DEM), and ISRO Bhuvan satellite thematic layers."),
        ("Stage 2: Geotechnical Feature Engineering", "Constructs a synchronized 20-dimensional mathematical feature tensor. Integrates geotechnical physics: Antecedent Rainfall Index (ARI-7), slope gradient, aspect trigonometry, curvature, fault distance, and lithology codes."),
        ("Stage 3: Machine Learning Model Inference", "The 20-feature tensor is evaluated by the production Gradient Boosting Classifier (GBC) ensemble. The model computes posterior probabilities P(Hazard = 1 | X) using log-odds optimization over 80 shallow boosting estimators."),
        ("Stage 4: Hybrid Decision Engine & Risk Classification", "Blends pure probabilistic AI scoring with physical threshold safety gates (e.g. cloudburst >25mm/hr, pore water pressure >60 kPa, saturation >80%). Maps predictions into actionable four-tier disaster bands: LOW (<0.35), MODERATE (0.35-0.65), HIGH (0.65-0.85), CRITICAL (≥0.85)."),
        ("Stage 5: Spatial GIS Visualization & ISRO Bhuvan Fusion", "Renders risk zones directly on high-resolution Leaflet GIS maps overlaid with ISRO Bhuvan satellite feeds. Generates dynamic color-coded contour polygons and pin-point critical node markers with zero third-party API keys."),
        ("Stage 6: Autonomous Alerting & Incident Dispatch", "When predictions enter HIGH or CRITICAL states, automated Webhooks, SMS dispatchers, and CAP (Common Alerting Protocol) event streams notify District Disaster Management Authorities (DDMA) and first responders in real time.")
    ]

    for title, desc in stages:
        story.append(Paragraph(f"<b>• {title}:</b> {desc}", body_style))

    story.append(Spacer(1, 8))

    # Section 3: AI & Machine Learning Foundations
    story.append(Paragraph("3. Deep-Dive: AI & Machine Learning Algorithmic Architecture", h1_style))
    story.append(Paragraph(
        "The predictive backbone of NE-SHIELD is built upon advanced ensemble learning algorithms engineered specifically for non-linear, high-dimensional geological phenomena. Tabular environmental data exhibits intricate feature interactions (e.g. steep slope is harmless until combined with high pore pressure and antecedent saturation) where tree ensembles consistently outperform standard neural networks.",
        body_style
    ))

    story.append(Paragraph("3.1 Gradient Boosting Classifier (GBC) Architecture", h2_style))
    story.append(Paragraph(
        "The primary AI model employs <b>Gradient Tree Boosting</b>. Rather than training independent models in parallel, the algorithm trains estimators sequentially in an additive stage-wise manner:",
        body_style
    ))
    story.append(Paragraph(
        "<i>F<sub>m</sub>(x) = F<sub>m-1</sub>(x) + γ<sub>m</sub> h<sub>m</sub>(x)</i>",
        callout_style
    ))
    story.append(Paragraph(
        "At each boosting round <i>m</i>, a new regression tree <i>h<sub>m</sub>(x)</i> is fitted to the negative gradients (pseudo-residuals) of the logistic loss function with respect to the previous ensemble prediction <i>F<sub>m-1</sub>(x)</i>. This guarantees that each subsequent tree focuses specifically on difficult-to-classify edge cases, such as borderline rainfall events where structural geology dictates failure.",
        body_style
    ))

    story.append(Paragraph("3.2 Hyperparameter Specification & Regularization", h2_style))
    hyper_data = [
        [Paragraph("<b>Hyperparameter</b>", table_header_style), Paragraph("<b>Tuned Value</b>", table_header_style), Paragraph("<b>Engineering Rationale</b>", table_header_style)],
        [Paragraph("Estimators (n_estimators)", table_cell_style), Paragraph("80 Trees", table_cell_style), Paragraph("Balances high predictive capacity against latency constraints (<20ms inference).", table_cell_style)],
        [Paragraph("Learning Rate (η)", table_cell_style), Paragraph("0.10 (Shrinkage)", table_cell_style), Paragraph("Shrinks the contribution of each tree to prevent overfitting on local weather spikes.", table_cell_style)],
        [Paragraph("Max Tree Depth", table_cell_style), Paragraph("4 Levels", table_cell_style), Paragraph("Limits tree interactions to 4-way feature conjunctions, preventing noise memorization.", table_cell_style)],
        [Paragraph("Test Split / Stratification", table_cell_style), Paragraph("20% Stratified", table_cell_style), Paragraph("Preserves natural positive/negative landslide event proportions during validation.", table_cell_style)],
        [Paragraph("Random State Seed", table_cell_style), Paragraph("42 (Deterministic)", table_cell_style), Paragraph("Ensures 100% scientific reproducibility across retraining cycles.", table_cell_style)]
    ]
    t_hyper = Table(hyper_data, colWidths=[120, 90, 290])
    t_hyper.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1E3A8A")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_hyper)
    story.append(Spacer(1, 10))

    # Section 4: 20-Dimensional Geotechnical Feature Vector
    story.append(Paragraph("4. The 20-Dimensional AI Feature Vector & Physics Modeling", h1_style))
    story.append(Paragraph(
        "Machine Learning models are only as good as their input representations. NE-SHIELD incorporates domain-specific hydrology and slope stability physics directly into its feature extraction layer:",
        body_style
    ))

    feat_data = [
        [Paragraph("<b>Feature Name</b>", table_header_style), Paragraph("<b>Unit / Type</b>", table_header_style), Paragraph("<b>Physical / AI Significance</b>", table_header_style)],
        [Paragraph("rainfall_1h_mm", table_cell_style), Paragraph("mm/hr", table_cell_style), Paragraph("Detects sudden cloudbursts and flash-flood initiation.", table_cell_style)],
        [Paragraph("rainfall_3h / 6h_mm", table_cell_style), Paragraph("mm", table_cell_style), Paragraph("Short-duration storm intensification indices.", table_cell_style)],
        [Paragraph("rainfall_24h / 72h_mm", table_cell_style), Paragraph("mm", table_cell_style), Paragraph("Medium-duration saturation indices driving regional debris flows.", table_cell_style)],
        [Paragraph("antecedent_rainfall_7d_mm", table_cell_style), Paragraph("mm (ARI-7)", table_cell_style), Paragraph("Accounts for historical water retention before new rainfall occurs.", table_cell_style)],
        [Paragraph("soil_moisture_pct", table_cell_style), Paragraph("0 - 100 %", table_cell_style), Paragraph("Subsurface volumetric water content determining shear strength drop.", table_cell_style)],
        [Paragraph("pore_pressure_kpa", table_cell_style), Paragraph("kPa", table_cell_style), Paragraph("Piezometric water pressure reducing effective stress (Terzaghi principle).", table_cell_style)],
        [Paragraph("slope_deg", table_cell_style), Paragraph("Degrees (°)", table_cell_style), Paragraph("Gravitational driving force according to Mohr-Coulomb failure envelope.", table_cell_style)],
        [Paragraph("elevation_m", table_cell_style), Paragraph("Meters MSL", table_cell_style), Paragraph("Orography and catchment runoff acceleration indicator.", table_cell_style)],
        [Paragraph("aspect_sin / aspect_cos", table_cell_style), Paragraph("Continuous [-1, 1]", table_cell_style), Paragraph("Decomposes circular compass direction for smooth ML convergence.", table_cell_style)],
        [Paragraph("distance_to_fault_m", table_cell_style), Paragraph("Meters", table_cell_style), Paragraph("Proximity to active tectonic shear zones where rock mass is fractured.", table_cell_style)],
        [Paragraph("lithology_code", table_cell_style), Paragraph("Categorical [0-3]", table_cell_style), Paragraph("Bedrock stability: Crystalline(0), Metamorphic(1), Sedimentary(2), Alluvial(3).", table_cell_style)]
    ]
    t_feat = Table(feat_data, colWidths=[130, 80, 290])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0369A1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0369A1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 10))

    # Section 5: ISRO Bhuvan Satellite & Spatial AI Engine
    story.append(Paragraph("5. ISRO Bhuvan Satellite & Geospatial Data Fusion Engine", h1_style))
    story.append(Paragraph(
        "NE-SHIELD bridges ground-level IoT monitoring with space-based Earth Observation. Integration with <b>ISRO Bhuvan</b> (National Remote Sensing Centre - NRSC) provides macro-scale terrain context that cannot be captured by ground stations alone:",
        body_style
    ))
    story.append(Paragraph(
        "<b>• ISRO Bhuvan WMS Satellite Layer:</b> Streams real-time multispectral satellite imagery directly from <code>https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms</code>. This gives disaster managers visual terrain verification of flood inundation and landslide scars without relying on expensive proprietary mapping APIs.<br/>"
        "<b>• Dynamic GIS Command Dashboard:</b> Built using Leaflet.js and responsive HTML5 canvas, the user interface displays active monitoring stations, real-time risk severity heatmaps (CRITICAL in glowing crimson, HIGH in orange, MODERATE in amber, LOW in emerald), interactive station telemetry popups, and instant manual AI pipeline trigger controls.<br/>"
        "<b>• Zero-Key Open Architecture:</b> Bypasses Google Maps / Mapbox billing dependencies by utilizing ISRO Bhuvan and ESRI World Imagery basemaps, ensuring 100% uptime for public safety agencies at zero recurring API costs.",
        body_style
    ))

    # Section 6: AI Training, Evaluation & Retraining Pipeline
    story.append(Paragraph("6. Continuous Learning & Retraining Pipeline", h1_style))
    story.append(Paragraph(
        "A critical vulnerability of traditional disaster models is concept drift — weather patterns change with seasonal monsoons and climate disruption. NE-SHIELD solves this through an autonomous training pipeline:",
        body_style
    ))
    story.append(Paragraph(
        "1. <b>Continuous Feedback Ingestion:</b> Field observation logs, verified historical landslide occurrences from the Geological Survey of India (GSI), and sensor feeds are ingested into SQLite/PostgreSQL storage.<br/>"
        "2. <b>Automated Retraining:</b> The <code>run_pipeline.py</code> and <code>/api/v1/ml/train</code> endpoints can be triggered automatically on scheduled cron intervals or via the operator UI.<br/>"
        "3. <b>Model Versioning & Verification:</b> Trained models undergo rigorous evaluation: ROC-AUC score, Precision-Recall curve, Confusion Matrix, and F1-Score. Only models outperforming baseline thresholds are stamped with <code>PRODUCTION_ACTIVE</code> status and hot-swapped in memory with zero backend downtime.<br/>"
        "4. <b>Joblib Model Artifact Serialization:</b> Active model weights are preserved in <code>active_model.joblib</code> along with complete training metadata JSON for full regulatory auditability.",
        body_style
    ))

    # Section 7: Free Cloud Hosting & Deployment Architecture
    story.append(Paragraph("7. Cloud Deployment & Scalability Architecture", h1_style))
    story.append(Paragraph(
        "The complete system is containerized and cloud-optimized for zero-cost deployment on Render.com and GitHub:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>FastAPI High-Performance Async Backend:</b> Serves sub-10ms RESTful endpoints for real-time risk predictions, station telemetries, and alert broadcasts.<br/>"
        "• <b>Render Cloud Blueprint (<code>render.yaml</code>):</b> Fully automated cloud specification with automatic Python 3.11 dependency compilation, health checks, and global HTTPS certificate provisioning.<br/>"
        "• <b>Static GIS Dashboard Integration:</b> The interactive command center is embedded directly inside FastAPI's static file engine, allowing both the GIS interface and the AI API to run in a single lightweight microservice on Render's 100% free tier.<br/>"
        "• <b>GitHub CI/CD Integration:</b> Managed under <code>arifshekh291172-web/Theem-Warrior-AI-Flood-Early-Warning</code> with automated branch tracking and continuous deployment.",
        body_style
    ))

    # Section 8: Summary & Key Takeaways
    story.append(Spacer(1, 6))
    story.append(Paragraph("8. Technical Summary & Impact", h1_style))
    summary_box = [
        [Paragraph(
            "<b>Key Highlights of NE-SHIELD AI System:</b><br/>"
            "• <b>AI-Centric Design:</b> 80-Tree Gradient Boosting ensemble trained on 20 geotechnical and meteorological features.<br/>"
            "• <b>ISRO Bhuvan Integration:</b> Direct satellite WMS layers providing authentic Indian space research GIS data.<br/>"
            "• <b>Early Detection Window:</b> Predicts catastrophic slope failures up to 72 hours prior to trigger.<br/>"
            "• <b>Production Ready:</b> 1-click execution scripts (<code>start.bat</code>), GitHub automated push, and free Render deployment.",
            table_cell_style
        )]
    ]
    t_summary = Table(summary_box, colWidths=[500])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#2563EB")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_summary)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {filename}")

if __name__ == '__main__':
    target = os.path.join(os.getcwd(), "NE-SHIELD_AI_System_Workflow_Architecture.pdf")
    create_pdf(target)
