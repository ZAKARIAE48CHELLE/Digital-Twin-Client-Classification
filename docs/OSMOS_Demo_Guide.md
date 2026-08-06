# OSMOS - Live Demonstration Guide & Speaker Notes

This guide provides a step-by-step script and speaker notes for presenting the OSMOS platform to stakeholders, executives, and technical committees.

Each page includes a floating right-side Page Guide widget (`Page Guide`). During demonstrations, the presenter can open it to explain the purpose, actions, outputs, and workflow position of the current page without leaving the interface or crowding navigation.

The interface includes a custom OSMOS visual design system with Light/Dark mode switching and professional iconography. The goal is to provide a distinctive enterprise-grade UI rather than a generic Streamlit dashboard.

---

## 1. Demonstration Script (15-Minute Flow)

### Step 1: Launch Application & Overview
* **Action**: Run `streamlit run app.py`.
* **Screen**: Main Executive Dashboard.
* **Speaker Script**:
  > *"Welcome to OSMOS - Optimal Smart Marketing Operation System. OSMOS is an enterprise AI platform that unifies customer behavioral scoring, CLV estimation, historical audit tracking, and local LLM action recommendations."*

### Step 2: Critical Action Alerts & LLM Guidance
* **Action**: Scroll to **Critical Action Alerts**. Click `Generate LLM Guidance` on an active alert.
* **Speaker Script**:
  > *"Notice how the system surfaces real-time deterministic alerts, such as Prediction Drift or CLV drops. When we click 'Generate LLM Guidance', our local, private LLM analyzes the feature context and generates a bilingual executive recommendation without any external API calls."*

### Step 3: Digital Twin & Persona Intelligence
* **Action**: Navigate to **Digital Twin Explorer** in the sidebar. Select entity `P01501`.
* **Speaker Script**:
  > *"Here is the core scientific distinction of OSMOS. On the left, we see the individual Digital Twin of entity P01501 - showing its exact recency, spend, churn risk, and predicted CLV of 17,507 MAD. Through our strict resolution chain, P01501 is assigned to the 'High-Value Loyalists' segment, which automatically maps to the 'Premium Loyalist' Persona Blueprint."*

### Step 4: One-Click Demo Preparation & LLM Journey Planner (Phase 8.7)
* **Action**: Navigate to **Digital Twin Journey Tree Simulator**. Click `Prepare Full Demo Entity`.
* **Speaker Script**:
  > *"The Journey Simulator is the controlled lifecycle generator for OSMOS. By clicking 'Prepare Full Demo Entity', OSMOS resets demo entity P_DEMO_001 to a clean Prospect state and deterministically executes a 5-stage customer lifecycle scenario with real PostgreSQL event_history records, journey_steps, snapshots, and persona resolution. Additionally, our Phase 8.7 LLM-assisted journey planner allows proposing custom scenarios: the LLM proposes a structured plan, OSMOS validates it deterministically, the admin approves it, and only then the Journey Runner applies valid events into PostgreSQL history."*

### Step 5: Multi-Agent Supervision & Debate Mode
* **Action**: Navigate to **Agent Supervision Center**. Select `P_DEMO_001` and click `Run Multi-Agent Audit`.
* **Speaker Script**:
  > *"With P_DEMO_001 fully prepared, our 8 supervision agents evaluate customer health and operational readiness in parallel. Notice how debate mode identifies gaps and synthesizes a clear Next Best Action using official OSMOS terminology."*

---

## 2. Key Talking Points & FAQ Answers

- **Q: Does the LLM calculate customer lifetime value or write directly to the database?**
  * **Answer**: *"No. All calculations (CLV, RFM-ES, Churn Risk) are 100% deterministic. The LLM acts purely as an advisory synthesis layer. In journey planning, the LLM proposes a scenario, OSMOS validates it deterministically against 14 safety rules, the admin approves it, and only then the Journey Runner writes real events to PostgreSQL."*
- **Q: Why separate Digital Twin from Persona?**
  * **Answer**: *"A Digital Twin belongs to an individual customer and changes constantly with real-time data. A Persona belongs to a segment and defines standard marketing strategy. Conflating the two leads to inaccurate marketing."*
