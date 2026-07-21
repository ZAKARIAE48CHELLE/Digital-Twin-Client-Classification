# OSMOS Persona Library & Matching Layer (Phase 6)

## Overview
The **Persona Library** provides segment-level marketing representations linked to OSMOS customer segments. Personas provide human-readable behavior profiles, risk profiles, value profiles, and recommended communication channels.

---

## Architectural Principles
1. **Segment-First Resolution**: Entities are NEVER assigned a persona directly from raw attributes. The assignment flow strictly passes through the `customer_segment`.
   ```
   entity_id → customer_segment → persona_library.segment_name → persona
   ```
2. **PostgreSQL Persistence**: Predefined personas are stored in the `persona_library` PostgreSQL table. In Excel fallback mode, built-in in-memory fallback dictionaries are served seamlessly.

---

## Predefined Persona Mapping (10 Segments)
1. **Prospect** ➔ *New Explorer*
2. **New Customers** ➔ *New Explorer*
3. **High-Value Loyalists** ➔ *Premium Loyalist*
4. **At-Risk Premium Clients** ➔ *Silent VIP at Risk*
5. **Growth Potential Clients** ➔ *Emerging Loyalist*
6. **Price-Sensitive Occasional Buyers** ➔ *Deal Seeker*
7. **Complaint-Driven Risk Clients** ➔ *Frustrated Client*
8. **Dormant Low-Value Clients** ➔ *Sleeping Client*
9. **Social Advocates** ➔ *Brand Advocate*
10. **Standard Active Clients** ➔ *Regular Buyer*

---

## Module Components
- `persona_library.py`: Database CRUD methods (`get_all_personas`, `get_persona_by_segment`, `upsert_persona`, `seed_default_personas`) with fallback defaults.
- `seed_persona_library.py`: Executable seed script to populate PostgreSQL.
- `persona_matcher.py`: Resolution functions ensuring segment-first persona matching and consistency audits.
- `persona_dashboard.py`: Streamlit catalog viewer and persona blueprint card renderer.
