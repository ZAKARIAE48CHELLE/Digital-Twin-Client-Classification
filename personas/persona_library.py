import logging
import psycopg2.extras
from database.db import get_cursor, get_connection
from admin.database_metrics import is_postgres_available

logger = logging.getLogger("OSMOS_PERSONA_LIBRARY")

DEFAULT_PERSONA_MAP = {
    "Prospect": {
        "persona_id": 1,
        "segment_name": "Prospect",
        "persona_name": "New Explorer",
        "description_fr": "Prospect en phase de découverte exploratoire de la marque.",
        "description_en": "Prospect in initial discovery and exploration phase.",
        "behavior_profile_fr": "Consultation occasionnelle des produits, pas encore d'achat.",
        "behavior_profile_en": "Occasional product browsing, no purchase history yet.",
        "value_profile_fr": "Valeur actuelle faible, potentiel d'acquisition modéré à élevé.",
        "value_profile_en": "Low current value, moderate to high acquisition potential.",
        "risk_profile_fr": "Risque d'abandon d'intérêt précoce.",
        "risk_profile_en": "Risk of early interest drop-off.",
        "recommended_action_fr": "Nourrir avec du contenu éducatif et une offre de bienvenue.",
        "recommended_action_en": "Nurture with educational content and a low-friction welcome offer.",
        "preferred_channel": "Email / Web Popup",
        "priority_level": "Medium",
        "is_active": True
    },
    "New Customers": {
        "persona_id": 2,
        "segment_name": "New Customers",
        "persona_name": "New Explorer",
        "description_fr": "Nouveau client avec un historique d'achat très récent.",
        "description_en": "New customer with very limited purchase history.",
        "behavior_profile_fr": "Premier achat effectué, découverte de l'écosystème.",
        "behavior_profile_en": "First purchase completed, exploring ecosystem.",
        "value_profile_fr": "Valeur initiale enregistrée, potentiel de réachat.",
        "value_profile_en": "Initial value recorded, repeat purchase potential.",
        "risk_profile_fr": "Risque d'attrition post-premier achat.",
        "risk_profile_en": "Risk of post-first purchase churn.",
        "recommended_action_fr": "Accompagner le parcours d'accueil et encourager le 2ème achat.",
        "recommended_action_en": "Onboarding support and first loyalty incentive.",
        "preferred_channel": "Email / In-App Message",
        "priority_level": "Medium",
        "is_active": True
    },
    "High-Value Loyalists": {
        "persona_id": 3,
        "segment_name": "High-Value Loyalists",
        "persona_name": "Premium Loyalist",
        "description_fr": "Client fidèle à très forte valeur et récurrence élevée.",
        "description_en": "Loyal high-value client with strong engagement and low churn risk.",
        "behavior_profile_fr": "Achats fréquents, réponses très positives aux campagnes.",
        "behavior_profile_en": "Frequent purchases, highly responsive to campaigns.",
        "value_profile_fr": "Valeur vie client (CLV) très élevée.",
        "value_profile_en": "Very high Customer Lifetime Value (CLV).",
        "risk_profile_fr": "Faible risque d'attrition, mais sensibilité aux défaillances de service.",
        "risk_profile_en": "Low churn risk, sensitive to service disruptions.",
        "recommended_action_fr": "Récompenser la fidélité avec un statut VIP et des privilèges exclusifs.",
        "recommended_action_en": "Reward loyalty with VIP program, premium benefits, and personalized rewards.",
        "preferred_channel": "Direct Phone / Email VIP",
        "priority_level": "High",
        "is_active": True
    },
    "At-Risk Premium Clients": {
        "persona_id": 4,
        "segment_name": "At-Risk Premium Clients",
        "persona_name": "Silent VIP at Risk",
        "description_fr": "Client à haute valeur historique montrant des signes d'inactivité.",
        "description_en": "Valuable client showing risk and inactivity signals.",
        "behavior_profile_fr": "Diminution soudaine de la fréquence d'achat et des visites.",
        "behavior_profile_en": "Sudden decrease in visit and purchase frequency.",
        "value_profile_fr": "Potentiel de perte financière important si le churn se concrétise.",
        "value_profile_en": "Substantial financial loss potential if churn completes.",
        "risk_profile_fr": "Risque de résiliation ou d'abandon critique (Churn Élevé).",
        "risk_profile_en": "Critical risk of cancellation or churn (High Risk).",
        "recommended_action_fr": "Campagne de rétention urgente et contact personnalisé.",
        "recommended_action_en": "Urgent retention campaign and direct follow-up.",
        "preferred_channel": "Phone / Direct Account Manager",
        "priority_level": "Critical",
        "is_active": True
    },
    "Growth Potential Clients": {
        "persona_id": 5,
        "segment_name": "Growth Potential Clients",
        "persona_name": "Emerging Loyalist",
        "description_fr": "Client prometteur en croissance de valeur et d'engagement.",
        "description_en": "Promising client with increasing value and engagement.",
        "behavior_profile_fr": "Interaction régulière et comportement d'achat en hausse.",
        "behavior_profile_en": "Regular interaction and increasing order frequency.",
        "value_profile_fr": "Valeur intermédiaire avec forte opportunité d'expansion.",
        "value_profile_en": "Intermediate value with strong expansion opportunity.",
        "risk_profile_fr": "Modéré.",
        "risk_profile_en": "Moderate risk.",
        "recommended_action_fr": "Cross-selling ciblé et incitations à la montée en gamme.",
        "recommended_action_en": "Personalized cross-sell and loyalty activation.",
        "preferred_channel": "Email / SMS",
        "priority_level": "Medium",
        "is_active": True
    },
    "Price-Sensitive Occasional Buyers": {
        "persona_id": 6,
        "segment_name": "Price-Sensitive Occasional Buyers",
        "persona_name": "Deal Seeker",
        "description_fr": "Acheteur occasionnel très réactif aux promotions et réductions.",
        "description_en": "Occasional buyer with high price sensitivity.",
        "behavior_profile_fr": "Achats concentrés lors des périodes de soldes et remises.",
        "behavior_profile_en": "Purchases concentrated during discount periods.",
        "value_profile_fr": "Panier moyen modéré, marge plus faible.",
        "value_profile_en": "Moderate average order value, lower margin.",
        "risk_profile_fr": "Sensible à la concurrence sur les prix.",
        "risk_profile_en": "Highly sensitive to competitor pricing.",
        "recommended_action_fr": "Offres promotionnelles ciblées et ventes flash.",
        "recommended_action_en": "Targeted discounts and bundle offers.",
        "preferred_channel": "SMS / Push Notification",
        "priority_level": "Low",
        "is_active": True
    },
    "Complaint-Driven Risk Clients": {
        "persona_id": 7,
        "segment_name": "Complaint-Driven Risk Clients",
        "persona_name": "Frustrated Client",
        "description_fr": "Client insatisfait ayant émis des réclamations ou avis négatifs.",
        "description_en": "Client affected by dissatisfaction or complaints.",
        "behavior_profile_fr": "Réclamations enregistrées ou sentiment social négatif.",
        "behavior_profile_en": "Log of complaints or negative social sentiment.",
        "value_profile_fr": "Valeur variable, risque de détérioration de l'image de marque.",
        "value_profile_en": "Variable value, risk of brand reputation damage.",
        "risk_profile_fr": "Risque d'attrition motivé par la frustration.",
        "risk_profile_en": "Churn risk driven by unresolved frustration.",
        "recommended_action_fr": "Prise en charge prioritaire du support et geste commercial.",
        "recommended_action_en": "Service recovery and personalized support.",
        "preferred_channel": "Phone / Dedicated Support Email",
        "priority_level": "High",
        "is_active": True
    },
    "Dormant Low-Value Clients": {
        "persona_id": 8,
        "segment_name": "Dormant Low-Value Clients",
        "persona_name": "Sleeping Client",
        "description_fr": "Client inactif depuis plus de 60 jours à faible valeur historique.",
        "description_en": "Inactive or low-value client with no recent engagement.",
        "behavior_profile_fr": "Aucune visite récente, taux d'ouverture email très faible.",
        "behavior_profile_en": "No recent visits, very low email open rate.",
        "value_profile_fr": "Faible contribution au chiffre d'affaires.",
        "value_profile_en": "Low contribution to overall revenue.",
        "risk_profile_fr": "Pratiquement inactif (Dormant).",
        "risk_profile_en": "Virtually inactive (Dormant).",
        "recommended_action_fr": "Campagne de réactivation automatisée à bas coût.",
        "recommended_action_en": "Reactivation campaign or low-cost communication.",
        "preferred_channel": "Automated Email Batch",
        "priority_level": "Low",
        "is_active": True
    },
    "Social Advocates": {
        "persona_id": 9,
        "segment_name": "Social Advocates",
        "persona_name": "Brand Advocate",
        "description_fr": "Client enthousiaste exprimant un sentiment très positif sur les réseaux.",
        "description_en": "Positive and engaged customer with advocacy potential.",
        "behavior_profile_fr": "Engage sur le contenu web et relais positif des campagnes.",
        "behavior_profile_en": "High content engagement and positive brand mentions.",
        "value_profile_fr": "Valeur directe moyenne à élevée + valeur d'influence indirecte.",
        "value_profile_en": "Moderate-high direct value plus indirect referral influence.",
        "risk_profile_fr": "Très faible.",
        "risk_profile_en": "Very low.",
        "recommended_action_fr": "Programme de parrainage et accès aux avant-premières.",
        "recommended_action_en": "Referral program and social engagement campaign.",
        "preferred_channel": "Email / Social Channels",
        "priority_level": "Medium",
        "is_active": True
    },
    "Standard Active Clients": {
        "persona_id": 10,
        "segment_name": "Standard Active Clients",
        "persona_name": "Regular Buyer",
        "description_fr": "Client actif régulier avec des métriques de comportement stables.",
        "description_en": "Normal active customer with stable behavior.",
        "behavior_profile_fr": "Achats et visites conformes à la moyenne du portefeuille.",
        "behavior_profile_en": "Purchases and visits matching baseline portfolio metrics.",
        "value_profile_fr": "Valeur stable dans la moyenne.",
        "value_profile_en": "Stable baseline value.",
        "risk_profile_fr": "Faible à modéré.",
        "risk_profile_en": "Low to moderate.",
        "recommended_action_fr": "Maintenir l'engagement avec des recommandations personnalisées.",
        "recommended_action_en": "Maintain engagement and monitor evolution.",
        "preferred_channel": "Standard Email Newsletter",
        "priority_level": "Low",
        "is_active": True
    }
}

def get_all_personas():
    """Retrieves all persona library entries from PostgreSQL, or built-in defaults if unavailable."""
    if not is_postgres_available():
        return list(DEFAULT_PERSONA_MAP.values())
        
    query = "SELECT * FROM persona_library WHERE is_active = TRUE ORDER BY persona_id ASC;"
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            if rows:
                return [dict(r) for r in rows]
            return list(DEFAULT_PERSONA_MAP.values())
    except Exception as e:
        logger.error(f"Failed to query persona_library from DB: {e}")
        return list(DEFAULT_PERSONA_MAP.values())

def get_persona_by_segment(segment_name):
    """Retrieves a persona definition for a given segment name."""
    if not segment_name:
        return DEFAULT_PERSONA_MAP.get("Standard Active Clients")
        
    if not is_postgres_available():
        return DEFAULT_PERSONA_MAP.get(segment_name) or DEFAULT_PERSONA_MAP.get("Standard Active Clients")
        
    query = "SELECT * FROM persona_library WHERE segment_name = %s AND is_active = TRUE LIMIT 1;"
    try:
        with get_cursor(commit=False) as cur:
            cur.execute(query, (segment_name,))
            res = cur.fetchone()
            if res:
                return dict(res)
            return DEFAULT_PERSONA_MAP.get(segment_name) or DEFAULT_PERSONA_MAP.get("Standard Active Clients")
    except Exception as e:
        logger.error(f"Failed to fetch persona for segment '{segment_name}' from DB: {e}")
        return DEFAULT_PERSONA_MAP.get(segment_name) or DEFAULT_PERSONA_MAP.get("Standard Active Clients")

def upsert_persona(persona_dict):
    """Inserts or updates a persona entry in PostgreSQL."""
    if not is_postgres_available():
        logger.warning("upsert_persona called in Excel mode. Persistence skipped.")
        return False
        
    query = """
        INSERT INTO persona_library (
            segment_name, persona_name, description_fr, description_en,
            behavior_profile_fr, behavior_profile_en, value_profile_fr, value_profile_en,
            risk_profile_fr, risk_profile_en, recommended_action_fr, recommended_action_en,
            preferred_channel, priority_level, is_active, updated_at
        ) VALUES (
            %(segment_name)s, %(persona_name)s, %(description_fr)s, %(description_en)s,
            %(behavior_profile_fr)s, %(behavior_profile_en)s, %(value_profile_fr)s, %(value_profile_en)s,
            %(risk_profile_fr)s, %(risk_profile_en)s, %(recommended_action_fr)s, %(recommended_action_en)s,
            %(preferred_channel)s, %(priority_level)s, %(is_active)s, NOW()
        )
        ON CONFLICT (segment_name) DO UPDATE SET
            persona_name = EXCLUDED.persona_name,
            description_fr = EXCLUDED.description_fr,
            description_en = EXCLUDED.description_en,
            behavior_profile_fr = EXCLUDED.behavior_profile_fr,
            behavior_profile_en = EXCLUDED.behavior_profile_en,
            value_profile_fr = EXCLUDED.value_profile_fr,
            value_profile_en = EXCLUDED.value_profile_en,
            risk_profile_fr = EXCLUDED.risk_profile_fr,
            risk_profile_en = EXCLUDED.risk_profile_en,
            recommended_action_fr = EXCLUDED.recommended_action_fr,
            recommended_action_en = EXCLUDED.recommended_action_en,
            preferred_channel = EXCLUDED.preferred_channel,
            priority_level = EXCLUDED.priority_level,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        RETURNING persona_id;
    """
    params = dict(persona_dict)
    if "is_active" not in params:
        params["is_active"] = True
        
    try:
        with get_cursor() as cur:
            cur.execute(query, params)
            res = cur.fetchone()
            return res["persona_id"] if res else True
    except Exception as e:
        logger.error(f"Failed to upsert persona for segment '{persona_dict.get('segment_name')}': {e}")
        return False

def deactivate_persona(persona_id):
    """Deactivates a persona by ID."""
    if not is_postgres_available():
        return False
        
    query = "UPDATE persona_library SET is_active = FALSE, updated_at = NOW() WHERE persona_id = %s;"
    try:
        with get_cursor() as cur:
            cur.execute(query, (persona_id,))
            return True
    except Exception as e:
        logger.error(f"Failed to deactivate persona id {persona_id}: {e}")
        return False

def seed_default_personas():
    """Seeds or updates the default 10 personas into PostgreSQL without creating duplicate records."""
    if not is_postgres_available():
        logger.info("seed_default_personas: PostgreSQL offline, using in-memory default map.")
        return 10
        
    count = 0
    for p_dict in DEFAULT_PERSONA_MAP.values():
        res = upsert_persona(p_dict)
        if res:
            count += 1
    logger.info(f"Successfully seeded {count} default personas into PostgreSQL.")
    return count
