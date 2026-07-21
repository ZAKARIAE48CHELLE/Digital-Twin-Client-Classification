import logging
from database.repositories import get_digital_twin_snapshot
from personas.persona_library import get_persona_by_segment, get_all_personas

logger = logging.getLogger("OSMOS_PERSONA_MATCHER")

def match_persona_for_segment(segment_name):
    """
    Explicit persona resolution from customer segment.
    Flow: customer_segment -> persona_library.segment_name -> persona definition
    """
    if not segment_name:
        segment_name = "Standard Active Clients"
    return get_persona_by_segment(segment_name)

def get_persona_for_entity(entity_id):
    """
    Retrieves the persona associated with an entity by resolving its customer_segment first.
    Strict Flow: entity_id -> customer_segment -> persona
    """
    snapshot = get_digital_twin_snapshot(entity_id)
    if not snapshot:
        # Fallback for uninitialized entity
        segment = "Prospect" if str(entity_id).startswith("P") else "Standard Active Clients"
    else:
        segment = snapshot.get("customer_segment") or snapshot.get("segment") or "Standard Active Clients"
        
    return match_persona_for_segment(segment)

def explain_persona_assignment(entity_id):
    """
    Provides a deterministic scientific explanation for how the persona was matched.
    """
    snapshot = get_digital_twin_snapshot(entity_id)
    segment = snapshot.get("customer_segment") if snapshot else "Standard Active Clients"
    persona = match_persona_for_segment(segment)
    
    explanation = {
        "entity_id": entity_id,
        "assigned_segment": segment,
        "matched_persona": persona.get("persona_name"),
        "resolution_chain": f"Entity [{entity_id}] ➔ Segment [{segment}] ➔ Persona [{persona.get('persona_name')}]",
        "description_fr": persona.get("description_fr"),
        "description_en": persona.get("description_en"),
        "recommended_action_fr": persona.get("recommended_action_fr"),
        "recommended_action_en": persona.get("recommended_action_en"),
        "preferred_channel": persona.get("preferred_channel"),
        "priority_level": persona.get("priority_level")
    }
    return explanation

def validate_segment_persona_consistency(df=None):
    """
    Validates that every client in the dataset has a persona matching its segment definition.
    Returns consistency audit results.
    """
    all_personas = get_all_personas()
    valid_segments = {p["segment_name"]: p["persona_name"] for p in all_personas}
    
    inconsistencies = []
    if df is not None and not df.empty:
        for idx, row in df.iterrows():
            e_id = row.get("entity_id")
            seg = row.get("customer_segment")
            pers = row.get("customer_persona")
            
            expected_persona = valid_segments.get(seg)
            if expected_persona and pers and pers != expected_persona:
                inconsistencies.append({
                    "entity_id": e_id,
                    "segment": seg,
                    "actual_persona": pers,
                    "expected_persona": expected_persona
                })
                
    return {
        "is_consistent": len(inconsistencies) == 0,
        "inconsistency_count": len(inconsistencies),
        "inconsistencies": inconsistencies
    }
