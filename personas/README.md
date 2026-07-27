# OSMOS Persona Library & Matching Layer (Phase 6 & Dynamic Expansion)

## Overview
The **Persona Layer** provides both predefined strategic blueprints and exploratory data-driven profiles linked to OSMOS customer segments and clustering models. Personas provide human-readable behavior profiles, risk profiles, value profiles, and recommended marketing actions.

OSMOS distinguishes between **stable personas** and **dynamic personas**:
> *OSMOS distinguishes between stable personas and dynamic personas. Stable personas are predefined strategic blueprints linked to official customer segments and used by the Digital Twin resolution chain. Dynamic personas are temporary, data-driven profiles generated from clustering results and used for exploratory analysis. Their number varies with the selected number of clusters (2 to 9).*
>
> *Dynamic personas are generated from clustering outputs using deterministic business interpretation rules. OSMOS assigns value level, engagement level, risk level, priority, recommended channel, and action based on cluster-level metrics. Micro-clusters and one-entity clusters are flagged as outliers to avoid presenting statistically weak groups as stable personas.*


---

## Architectural Principles
1. **Segment-First Resolution for Digital Twin**: Entities are NEVER assigned a persona directly from raw attributes. The assignment flow strictly passes through the `customer_segment`.
   ```
   entity_id → Digital Twin → customer_segment → persona_library.segment_name → stable_persona
   ```
2. **Exploratory Dynamic Personas**: Generated on-demand from KMeans clustering outputs without overwriting `persona_library` or Digital Twin persona resolutions.
3. **PostgreSQL Persistence**: Predefined stable personas are stored in the `persona_library` PostgreSQL table with fallback to in-memory dictionaries.

---

## Stable Persona Mapping (Predefined Official Blueprints)
1. **Prospect / New Customers** ➔ *New Explorer*
2. **High-Value Loyalists** ➔ *Premium Loyalist*
3. **At-Risk Premium Clients** ➔ *Silent VIP at Risk*
4. **Growth Potential Clients** ➔ *Emerging Loyalist*
5. **Price-Sensitive Occasional Buyers** ➔ *Deal Seeker*
6. **Complaint-Driven Risk Clients** ➔ *Frustrated Client*
7. **Dormant Low-Value Clients** ➔ *Sleeping Client*
8. **Social Advocates** ➔ *Brand Advocate*
9. **Standard Active Clients** ➔ *Regular Buyer*

---

## Module Components
- `persona_library.py`: Database CRUD methods (`get_all_personas`, `get_persona_by_segment`, `upsert_persona`, `seed_default_personas`) with fallback defaults.
- `seed_persona_library.py`: Executable seed script to populate PostgreSQL.
- `persona_matcher.py`: Resolution functions ensuring segment-first persona matching and consistency audits.
- `dynamic_persona_generator.py`: Generates data-driven profiles (`generate_dynamic_personas`, `summarize_cluster_profile`, `build_dynamic_persona_cards`) for 2-9 clusters.
- `persona_dashboard.py`: Streamlit catalog viewer for Stable Personas, Dynamic Personas, and Comparison tabs.
- `test_dynamic_personas.py`: Unit test suite verifying dynamic persona card generation, schema integrity, and isolation from `persona_library`.
