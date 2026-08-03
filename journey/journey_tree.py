import pandas as pd
import textwrap
from html import escape
from ui.icons import icon_html
from journey.journey_repository import get_journey_steps, get_journey_scenario_by_id


STAGE_ICONS = {
    "1. New Prospect": "Search",
    "2. Warm Prospect": "Engagement",
    "3. New Client": "Client",
    "4. VIP Client / Premium Loyalist": "Value",
    "5. At-Risk Premium Client / Churn Risk": "Warning",
}

def get_stage_icon(stage_name):
    """Return the professional icon key for a given stage name."""
    for key, icon in STAGE_ICONS.items():
        if key.lower() in str(stage_name).lower() or stage_name.lower() in key.lower():
            return icon
    return "Journey"

def build_journey_tree_data(scenario_id):
    """Fetches steps and constructs structured tree dataset."""
    steps = get_journey_steps(scenario_id)
    scenario = get_journey_scenario_by_id(scenario_id)
    return {
        "scenario": scenario,
        "steps": steps,
        "df": pd.DataFrame(steps) if steps else pd.DataFrame()
    }

def render_journey_tree_mermaid(steps):
    """
    Generates GitHub Flavored Mermaid flowchart string representing the 5-stage lifecycle tree.
    """
    if not steps:
        return """flowchart TD
    A["1. New Prospect (Draft)"] --> B["2. Warm Prospect"]
    B --> C["3. New Client"]
    C --> D["4. VIP Client"]
    D --> E["5. Churn Risk VIP"]
"""
    
    nodes = []
    connections = []
    
    for i, s in enumerate(steps):
        node_id = f"N{s.get('step_order', i+1)}"
        title = s.get('stage_name', f'Stage {i+1}')
        after_cls = s.get('after_dynamic_class', 'N/A')
        after_seg = s.get('after_segment', 'N/A')
        after_per = s.get('after_persona', 'N/A')
        
        # Clean label text for Mermaid
        node_label = f'<b>{title}</b><br/>Class: {after_cls}<br/>Segment: {after_seg}<br/>Persona: {after_per}'
        nodes.append(f'    {node_id}["{node_label}"]')
        
        if i > 0:
            prev_id = f"N{steps[i-1].get('step_order', i)}"
            connections.append(f'    {prev_id} --> {node_id}')
            
    mermaid_str = "flowchart TD\n" + "\n".join(nodes) + "\n" + "\n".join(connections)
    return mermaid_str


def render_journey_tree_html(steps):
    """Return a themed HTML lifecycle flow for Streamlit rendering."""
    if not steps:
        steps = [
            {
                "step_order": 1,
                "stage_name": "1. New Prospect",
                "after_dynamic_class": "Cold Prospect",
                "after_segment": "Prospect",
                "after_persona": "New Explorer",
            },
            {
                "step_order": 2,
                "stage_name": "2. Warm Prospect",
                "after_dynamic_class": "Warm Prospect",
                "after_segment": "Prospect",
                "after_persona": "New Explorer",
            },
            {
                "step_order": 3,
                "stage_name": "3. New Client",
                "after_dynamic_class": "Active Client",
                "after_segment": "New Customers",
                "after_persona": "New Explorer",
            },
            {
                "step_order": 4,
                "stage_name": "4. VIP Client / Premium Loyalist",
                "after_dynamic_class": "VIP Client",
                "after_segment": "High-Value Loyalists",
                "after_persona": "Premium Loyalist",
            },
            {
                "step_order": 5,
                "stage_name": "5. At-Risk Premium Client / Churn Risk",
                "after_dynamic_class": "Churn Risk Client",
                "after_segment": "Complaint-Driven Risk Clients",
                "after_persona": "Frustrated Client",
            },
        ]

    cards = []
    total = len(steps)
    for index, step in enumerate(steps):
        stage_name = escape(str(step.get("stage_name", f"Stage {index + 1}")))
        dynamic_class = escape(str(step.get("after_dynamic_class", "N/A")))
        segment = escape(str(step.get("after_segment", "N/A")))
        persona = escape(str(step.get("after_persona", "N/A")))
        order = escape(str(step.get("step_order", index + 1)))
        icon = icon_html(get_stage_icon(stage_name))
        connector = "" if index == total - 1 else "<div class='osmos-journey-connector' aria-hidden='true'>&rarr;</div>"
        cards.append(
            "<div class='osmos-journey-node-wrap'>"
            "<div class='osmos-journey-node'>"
            f"<div class='osmos-journey-node-top'><span class='osmos-journey-icon'>{icon}</span><span class='osmos-journey-step'>Step {order}</span></div>"
            f"<div class='osmos-journey-stage'>{stage_name}</div>"
            "<div class='osmos-journey-meta'>"
            f"<div><span>Class</span><b>{dynamic_class}</b></div>"
            f"<div><span>Segment</span><b>{segment}</b></div>"
            f"<div><span>Persona</span><b>{persona}</b></div>"
            "</div>"
            "</div>"
            f"{connector}"
            "</div>"
        )

    return "<div class='osmos-journey-tree-flow'>" + "".join(cards) + "</div>"

def build_step_card(step):
    """
    Renders styled HTML card for a single journey step.
    """
    icon = get_stage_icon(step.get("stage_name", ""))
    stage_title = step.get("stage_name", "")
    step_order = step.get("step_order", 1)
    
    events = step.get("trigger_event_type", "N/A")
    
    b_class = step.get("before_dynamic_class", "N/A")
    a_class = step.get("after_dynamic_class", "N/A")
    b_seg = step.get("before_segment", "N/A")
    a_seg = step.get("after_segment", "N/A")
    b_per = step.get("before_persona", "N/A")
    a_per = step.get("after_persona", "N/A")
    
    def safe_num(val, default=0.0):
        if val is None or pd.isna(val):
            return default
        try:
            f = float(val)
            return default if pd.isna(f) else f
        except Exception:
            return default

    b_clv = safe_num(step.get("before_clv_amount"), 0.0)
    a_clv = safe_num(step.get("after_clv_amount"), 0.0)
    clv_diff = a_clv - b_clv
    
    b_rfm = safe_num(step.get("before_rfm_score"), 0.0)
    a_rfm = safe_num(step.get("after_rfm_score"), 0.0)
    
    b_churn = safe_num(step.get("before_churn_risk"), 0.0)
    a_churn = safe_num(step.get("after_churn_risk"), 0.0)

    
    exp_fr = step.get("llm_explanation_fr", "")
    rec_fr = step.get("llm_recommendation_fr", "")
    
    clv_color = "#34d399" if clv_diff >= 0 else "#f87171"
    churn_color = "#f87171" if a_churn > 0.35 else "#34d399"

    card_html = textwrap.dedent(f"""\
    <div style='background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)); border: 1.5px solid rgba(56, 189, 248, 0.3); border-left: 5px solid #38bdf8; border-radius: 12px; padding: 18px; margin-bottom: 16px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h3 style='margin: 0; font-size: 18px; color: #38bdf8; display:flex; align-items:center; gap:8px;'>{icon_html(icon)} <span>Step {step_order}: {stage_title}</span></h3>
            <span style='background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 700;'>Triggers: {events}</span>
        </div>
        <hr style='border-color: rgba(255,255,255,0.1); margin: 12px 0;'>
        <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;'>
            <div style='background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px;'>
                <span style='font-size: 11px; color: #94a3b8; text-transform: uppercase;'>Dynamic Class Transition</span>
                <p style='margin: 4px 0 0 0; font-size: 13px; color: #cbd5e1;'><b>{b_class}</b> -> <b style='color: #38bdf8;'>{a_class}</b></p>
            </div>
            <div style='background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px;'>
                <span style='font-size: 11px; color: #94a3b8; text-transform: uppercase;'>Segment Transition</span>
                <p style='margin: 4px 0 0 0; font-size: 13px; color: #cbd5e1;'><b>{b_seg}</b> -> <b style='color: #34d399;'>{a_seg}</b></p>
            </div>
            <div style='background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px;'>
                <span style='font-size: 11px; color: #94a3b8; text-transform: uppercase;'>Resolved Persona Blueprint</span>
                <p style='margin: 4px 0 0 0; font-size: 13px; color: #cbd5e1;'><b>{b_per}</b> -> <b style='color: #fbbf24;'>{a_per}</b></p>
            </div>
        </div>
        <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 10px;'>
            <div style='background: rgba(15, 23, 42, 0.4); padding: 8px 12px; border-radius: 6px; font-size: 12px;'>
                <span style='color: #94a3b8;'>CLV Amount:</span> <b>{b_clv:.2f} MAD</b> -> <b style='color: #38bdf8;'>{a_clv:.2f} MAD</b> <span style='color: {clv_color};'>({clv_diff:+.2f})</span>
            </div>
            <div style='background: rgba(15, 23, 42, 0.4); padding: 8px 12px; border-radius: 6px; font-size: 12px;'>
                <span style='color: #94a3b8;'>RFM-ES Score:</span> <b>{b_rfm:.2f}</b> -> <b style='color: #34d399;'>{a_rfm:.2f}</b>
            </div>
            <div style='background: rgba(15, 23, 42, 0.4); padding: 8px 12px; border-radius: 6px; font-size: 12px;'>
                <span style='color: #94a3b8;'>Churn Risk:</span> <b>{b_churn:.2f}</b> -> <b style='color: {churn_color};'>{a_churn:.2f}</b>
            </div>
        </div>
        <div style='margin-top: 12px; background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 8px;'>
            <p style='margin: 0; font-size: 13px; color: #cbd5e1;'><b>Analytical Explanation (FR):</b> {exp_fr}</p>
            <p style='margin: 6px 0 0 0; font-size: 13px; color: #34d399;'><b>Recommandation Strategique:</b> {rec_fr}</p>
        </div>
    </div>
    """).strip()
    return card_html

    return card_html


