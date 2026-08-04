"""
OSMOS Contextual Page Guide — Data Content Module.

Contains the PAGE_HELP dictionary mapping each OSMOS page to its purpose,
user actions, key outputs, workflow position, mini workflow, demo tips, and DB requirements.
"""

PAGE_HELP = {
    "Dashboard Overview": {
        "title": "Executive Dashboard Overview",
        "purpose": "This page gives a global operational summary of the OSMOS platform. It helps the admin quickly understand the current state of customers, prospects, risks, value opportunities, alerts, and campaign activity.",
        "actions": [
            "View global KPIs.",
            "Monitor customer/prospect distribution.",
            "Detect high-value or high-risk entities.",
            "View critical action alerts.",
            "Check recent activity.",
            "Access LLM guidance only when explicitly requested.",
            "See campaign and journey indicators if available."
        ],
        "outputs": [
            "Total entities.",
            "Number of clients and prospects.",
            "CLV overview.",
            "Risk indicators.",
            "Critical alerts.",
            "Recent events.",
            "Campaign counters.",
            "System summary charts."
        ],
        "workflow_position": "Workflow position: Global monitoring layer",
        "mini_workflow": "Raw Data / DB → Digital Twin Engine → Predictions & Risk Alerts → Executive KPI Dashboard",
        "demo_tip": "Use this page first in the presentation to introduce the global purpose of OSMOS.",
        "requires_postgres": False
    },
    "Entity Profile": {
        "title": "Individual Entity Profile",
        "purpose": "This page allows the admin to inspect one specific customer or prospect. It shows the entity's latest information, behavioral features, predictions, scores, and history.",
        "actions": [
            "Select one entity by entity_id.",
            "View customer/prospect profile details.",
            "Inspect current behavioral variables.",
            "View latest RFM-ES, CLV, classification, and segment/persona.",
            "Check event history for the selected entity.",
            "Understand how the entity evolved over time."
        ],
        "outputs": [
            "Entity identity.",
            "Entity type: Prospect or Client.",
            "Behavioral state.",
            "Latest CLV prediction.",
            "Latest dynamic class.",
            "Latest segment and persona.",
            "Historical events."
        ],
        "workflow_position": "Workflow position: Individual entity inspection layer",
        "mini_workflow": "Select Entity → Fetch Digital Twin State → Calculate RFM / CLV / Segment → Display Timeline History",
        "demo_tip": "Select a known entity such as P_DEMO_001 after running the Journey Simulator to show how events are stored normally in PostgreSQL.",
        "requires_postgres": False
    },
    "Customer Segments & Personas": {
        "title": "Customer Segments & Personas",
        "purpose": "This page explains how customers and prospects are grouped into meaningful business cohorts and mapped to marketing persona blueprints.",
        "actions": [
            "Explore customer segments.",
            "View persona assignments.",
            "Compare groups of customers.",
            "Understand dominant customer behaviors.",
            "Identify strategic marketing groups.",
            "See recommended actions by segment/persona."
        ],
        "outputs": [
            "Segment distribution.",
            "Persona distribution.",
            "Segment descriptions.",
            "Persona descriptions.",
            "Recommended actions.",
            "Preferred channels."
        ],
        "workflow_position": "Workflow position: Cohort-level interpretation layer",
        "mini_workflow": "Entity → Digital Twin → Scores → Segment → Persona → Action",
        "demo_tip": "Use this page to explain why Digital Twin and Persona are not the same thing. Enforce resolution chain: entity_id → Digital Twin → segment → persona.",
        "requires_postgres": False
    },
    "Simulate Event": {
        "title": "Event Simulation",
        "purpose": "This page allows the admin to simulate customer/prospect interactions and observe how one event changes the Digital Twin state.",
        "actions": [
            "Select an entity.",
            "Apply a simulated event.",
            "Simulate purchases, complaints, email actions, engagement actions, or inactivity.",
            "Convert a prospect to a client through a purchase.",
            "Recalculate the affected entity.",
            "Save the event in PostgreSQL.",
            "Observe before/after changes."
        ],
        "outputs": [
            "Simulated event record.",
            "Updated entity state.",
            "Updated RFM-ES score.",
            "Updated CLV prediction.",
            "Updated dynamic classification.",
            "Updated segment/persona.",
            "Event history record."
        ],
        "workflow_position": "Workflow position: Event-driven update layer",
        "mini_workflow": "Select Entity → Select Event → Execute Event → Single-Entity Recalculation → Persist Event & Snapshot",
        "demo_tip": "Use a purchase event on a prospect to show the conversion from Prospect to Client.",
        "requires_postgres": False
    },
    "Create New Entity": {
        "title": "Create New Customer or Prospect",
        "purpose": "This page allows the admin to add a new customer or prospect into OSMOS and initialize its Digital Twin.",
        "actions": [
            "Create a new Prospect.",
            "Create a new Client.",
            "Enter initial profile and behavioral fields.",
            "Initialize default scoring values.",
            "Save the entity in PostgreSQL.",
            "Prepare the entity for future event simulation and prediction."
        ],
        "outputs": [
            "New entity_id.",
            "Initial entity profile.",
            "Initial Digital Twin state.",
            "Initial segment/persona if available."
        ],
        "workflow_position": "Workflow position: Data ingestion and entity initialization layer",
        "mini_workflow": "Input Form → Validate Identity → Initialize Scores → Persist Entity → Ready for Simulations",
        "demo_tip": "Create a simple prospect, then simulate events to show how OSMOS evolves its state.",
        "requires_postgres": False
    },
    "Database Intelligence": {
        "title": "Database Intelligence & Historical Monitoring",
        "purpose": "This page provides an administrative view of the PostgreSQL persistence layer, historical intelligence, table status, model outputs, and system auditability.",
        "actions": [
            "Check PostgreSQL health.",
            "View table row counts.",
            "Inspect latest events.",
            "Monitor CLV trend alerts.",
            "View segment transition matrix.",
            "Monitor prediction drift.",
            "Explore historical records.",
            "Check campaign, journey, LLM, and event tables."
        ],
        "outputs": [
            "Database health metrics.",
            "Table inventory.",
            "Latest event records.",
            "CLV trend alerts.",
            "Segment transition matrix.",
            "Prediction drift indicators.",
            "Historical prediction records.",
            "Audit logs."
        ],
        "workflow_position": "Workflow position: Historical audit and monitoring layer",
        "mini_workflow": "PostgreSQL Connection → Health Metrics → Table Row Inventory → Prediction Drift & Transition Audit",
        "demo_tip": "After running the Journey Simulator, open this page and show that journey-generated events appear inside normal history tables.",
        "requires_postgres": True
    },
    "Digital Twin & Persona": {
        "title": "Digital Twin & Persona Explorer",
        "purpose": "This page is the core scientific view of OSMOS. It shows the difference between an individual Digital Twin and a segment-level Persona.",
        "actions": [
            "Select an entity.",
            "View its Digital Twin state.",
            "Inspect behavioral vectors.",
            "View predictive scores.",
            "View segment/persona resolution.",
            "Explore persona library.",
            "Generate optional LLM Digital Twin summary.",
            "Review entity history and campaign history."
        ],
        "outputs": [
            "Individual Digital Twin profile.",
            "Behavioral state vector.",
            "RFM-ES, CLV, churn risk, decision priority.",
            "Segment assignment.",
            "Persona blueprint.",
            "Recommended action and channel.",
            "Optional LLM explanation."
        ],
        "workflow_position": "Workflow position: Individual intelligence + persona resolution layer",
        "mini_workflow": "Entity → Digital Twin → Scores → Segment → Persona → Action",
        "demo_tip": "Use P_DEMO_001 here after running the journey to show how its persona changes from New Explorer to Premium Loyalist to Silent VIP at Risk.",
        "requires_postgres": False
    },
    "Campaign Simulation": {
        "title": "Closed-Loop Campaign Simulation",
        "purpose": "This page allows admins to transform recommendations into simulated marketing actions and observe possible customer responses.",
        "actions": [
            "Create campaign drafts from LLM recommendations.",
            "Create campaigns from Digital Twin suggested actions.",
            "Approve campaign drafts.",
            "Simulate dispatch.",
            "Simulate customer response.",
            "Store dispatches and responses in PostgreSQL.",
            "Track campaign impact on the Digital Twin."
        ],
        "outputs": [
            "Campaign drafts.",
            "Approved campaigns.",
            "Simulated dispatch records.",
            "Simulated customer responses.",
            "Campaign response distribution.",
            "Impact on CLV, segment, or persona.",
            "Campaign history by entity."
        ],
        "workflow_position": "Workflow position: Closed-loop action-feedback layer",
        "mini_workflow": "Recommendation → Campaign Draft → Simulated Dispatch → Response → Event History → Updated Digital Twin",
        "demo_tip": "Use this page to explain that the current prototype does not send real emails or SMS. It simulates marketing actions safely.",
        "requires_postgres": True
    },
    "Journey Simulator": {
        "title": "Digital Twin Journey Tree Simulator",
        "purpose": "This page provides a guided presentation scenario where one demo entity evolves from a new prospect to a VIP client, then becomes at risk of churn.",
        "actions": [
            "Create/reset the demo entity P_DEMO_001.",
            "Run the journey step by step.",
            "Run the full journey.",
            "Generate real events and store them in event_history.",
            "Update the Digital Twin after each stage.",
            "Display the journey as a tree.",
            "View before/after class, segment, persona, CLV, and risk.",
            "Generate optional LLM explanations.",
            "Enable Presentation Mode for video recording."
        ],
        "outputs": [
            "Journey tree.",
            "Step-by-step lifecycle timeline.",
            "Generated event history.",
            "Before/after Digital Twin snapshots.",
            "Persona transitions.",
            "LLM explanations and recommendations.",
            "Presentation-ready visual cards."
        ],
        "workflow_position": "Workflow position: End-to-end demo scenario layer",
        "mini_workflow": "P_DEMO_001 → Generated Events → Digital Twin Update → Class/Segment/Persona Change → LLM Explanation → Presentation Tree",
        "demo_tip": "Use this page in the presentation video because it explains the whole platform clearly and visually.",
        "requires_postgres": True
    },
    "Agent Supervision Center": {
        "title": "Multi-Agent Intelligent Supervision Layer",
        "purpose": "Coordinates specialized analytical agents (Digital Twin, CLV, Churn Risk, Persona) to inspect entity state in read-only mode and synthesize global Next Best Actions.",
        "actions": [
            "Select entity to inspect.",
            "Select active specialized agents.",
            "Run read-only multi-agent analysis.",
            "Inspect evidence traceability matrix.",
            "Generate button-triggered LLM executive summary.",
            "Toggle Presentation Mode for executive view."
        ],
        "outputs": [
            "Global supervision status (OK, Warning, Critical).",
            "Consolidated risks, opportunities, and recommendations.",
            "Deterministic Next Best Action recommendation.",
            "Individual agent cards & confidence scores.",
            "Evidence traceability matrix.",
            "Optional bilingual (FR/EN) LLM executive summary."
        ],
        "workflow_position": "Workflow position: Multi-Agent Intelligent Supervision Layer",
        "mini_workflow": "Admin Request → Context Builder → Specialized Agents → Result Aggregator → Next Best Action → Optional LLM Summary",
        "demo_tip": "Demonstrate read-only multi-agent supervision for P_DEMO_001 or C00001 to show deterministic NBA recommendation followed by optional LLM summary generation.",
        "requires_postgres": False
    }
}

def get_page_help_content(page_name):
    """
    Retrieves the help content dictionary for a given page_name.
    Returns a safe default fallback dictionary for unknown pages.
    """
    if page_name in PAGE_HELP:
        return PAGE_HELP[page_name]
        
    return {
        "title": str(page_name),
        "purpose": "This page is part of the OSMOS platform. It contributes to the customer intelligence workflow.",
        "actions": [
            "Explore data and configurations.",
            "Execute page actions."
        ],
        "outputs": [
            "Interactive UI tables and metric indicators."
        ],
        "workflow_position": f"Workflow position: {page_name} module",
        "mini_workflow": f"Input Data → {page_name} Processing → Result Summary",
        "demo_tip": "Explore this module to inspect detailed metrics and system status.",
        "requires_postgres": False
    }
