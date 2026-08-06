"""
Default Scenario Definitions for OSMOS Digital Twin Journey Tree Simulator (Phase 8.7).
Supports realistic demo timeline offsets, 6 lifecycle stages, and segment-first persona alignment.
"""

DEFAULT_SCENARIO_NAME = "Prospect to VIP to Churn Risk (Standard Demo Scenario)"
DEFAULT_SCENARIO_DESCRIPTION = (
    "A 6-stage customer lifecycle simulation illustrating Digital Twin evolution, "
    "dynamic classification updates, segment transitions, segment-first persona matching, "
    "and optional service recovery simulation."
)

DEFAULT_STAGES = [
    {
        "step_order": 1,
        "stage_name": "1. New Prospect Discovery",
        "description_fr": "Prospect initial en phase de découverte exploratoire.",
        "description_en": "Initial prospect in early exploratory discovery phase.",
        "trigger_events": ["page_visit", "product_view", "email_open"],
        "event_values": [None, None, None],
        "event_offsets": [-20, -20, -20],
        "expected_dynamic_class": "Cold Prospect",
        "expected_segment": "Prospect",
        "expected_persona": "New Explorer",
        "explanation_fr": "Le prospect visite le site et consulte un produit. Le Digital Twin enregistre l'activité exploratoire initiale.",
        "explanation_en": "Prospect visits site and views a product. Digital Twin records initial exploratory activity.",
        "recommendation_fr": "Envoyer un email de bienvenue avec une offre de découverte.",
        "recommendation_en": "Send a welcome email with an exploratory offer."
    },
    {
        "step_order": 2,
        "stage_name": "2. Warm Prospect Engagement",
        "description_fr": "Interactions fréquentes et engagement actif avant conversion.",
        "description_en": "Frequent interactions and active engagement prior to conversion.",
        "trigger_events": ["product_view", "email_click", "add_to_cart", "social_positive_mention"],
        "event_values": [None, None, None, None],
        "event_offsets": [-14, -14, -14, -14],
        "expected_dynamic_class": "Warm Prospect",
        "expected_segment": "Prospect",
        "expected_persona": "New Explorer",
        "explanation_fr": "Le prospect ouvre les emails, clique sur les produits et ajoute un article au panier. La probabilité de conversion augmente.",
        "explanation_en": "Prospect opens emails, clicks links, and adds an item to cart. Conversion probability increases.",
        "recommendation_fr": "Afficher un popup avec une réduction de 10% pour finaliser le premier achat.",
        "recommendation_en": "Display a popup with 10% discount to prompt first purchase."
    },
    {
        "step_order": 3,
        "stage_name": "3. Prospect-to-Client Conversion",
        "description_fr": "Premier achat effectué, conversion officielle de Prospect en Client.",
        "description_en": "First purchase completed, official conversion from Prospect to Client.",
        "trigger_events": ["purchase"],
        "event_values": [1800.0],
        "event_offsets": [-10],
        "expected_dynamic_class": "New Client",
        "expected_segment": "New Customers",
        "expected_persona": "New Explorer",
        "explanation_fr": "Premier achat validé! L'entité est officiellement convertie de Prospect à Client. Le segment passe à 'New Customers'.",
        "explanation_en": "First purchase confirmed! Entity converts from Prospect to Client. Segment updates to 'New Customers'.",
        "recommendation_fr": "Déclencher la séquence de bienvenue client et collecter les préférences d'achat.",
        "recommendation_en": "Trigger client onboarding sequence and gather product preferences."
    },
    {
        "step_order": 4,
        "stage_name": "4. VIP Client / Premium Loyalist",
        "description_fr": "Achats répétés à forte valeur, avis positifs et forte fidélité.",
        "description_en": "Repeated high-value purchases, positive reviews, and strong loyalty.",
        "trigger_events": ["purchase", "purchase", "positive_review", "social_positive_mention", "email_click"],
        "event_values": [8500.0, 12000.0, None, None, None],
        "event_offsets": [-6, -5, -5, -5, -5],
        "expected_dynamic_class": "VIP Client",
        "expected_segment": "High-Value Loyalists",
        "expected_persona": "Premium Loyalist",
        "explanation_fr": "Achats répétés d'une valeur totale de >20 000 MAD avec avis positif. Le Digital Twin atteint le statut VIP Client & Premium Loyalist.",
        "explanation_en": "Repeated purchases exceeding 20,000 MAD with positive feedback. Digital Twin reaches VIP Client & Premium Loyalist status.",
        "recommendation_fr": "Attribuer un conseiller dédié VIP et offrir un accès anticipé aux nouvelles collections.",
        "recommendation_en": "Assign a dedicated VIP account advisor and provide early access to new collections."
    },
    {
        "step_order": 5,
        "stage_name": "5. At-Risk Premium Client / Churn Risk",
        "description_fr": "Réclamation formulée, sentiment négatif et période d'inactivité.",
        "description_en": "Customer complaint filed, negative sentiment, and extended inactivity.",
        "trigger_events": ["complaint", "negative_review", "inactivity_period", "social_negative_mention"],
        "event_values": [None, None, None, None],
        "event_offsets": [-1, -1, -1, -1],
        "expected_dynamic_class": "At-Risk Client",
        "expected_segment": "Complaint-Driven Risk Clients",
        "expected_persona": "Frustrated Client",
        "explanation_fr": "Dégradation de la satisfaction suite à une réclamation et inactivité prolongée. Le score de risque de churn augmente fortement.",
        "explanation_en": "Satisfaction drops due to a complaint and extended inactivity. Churn risk score increases significantly.",
        "recommendation_fr": "Lancer une campagne de conciliation prioritaire (appel direct du service client + geste commercial).",
        "recommendation_en": "Execute priority conciliation campaign (direct call from client relations + service recovery gesture)."
    },
    {
        "step_order": 6,
        "stage_name": "6. Service Recovery / Retention Simulation",
        "description_fr": "Simulation d'une prise en charge du service client et geste commercial de rétention.",
        "description_en": "Simulation of service recovery outreach and commercial retention gesture.",
        "trigger_events": ["service_recovery_contact", "retention_offer_sent", "email_click", "positive_feedback"],
        "event_values": [None, None, None, None],
        "event_offsets": [0, 0, 0, 0],
        "expected_dynamic_class": "At-Risk Client",
        "expected_segment": "Complaint-Driven Risk Clients",
        "expected_persona": "Frustrated Client",
        "explanation_fr": "Action de rétention initiée. Le journal enregistre le contact du service client et la proposition de geste commercial.",
        "explanation_en": "Retention attempt initiated. History logs service recovery contact and promotional retention offer.",
        "recommendation_fr": "Suivre la réponse du client au geste commercial et évaluer la baisse du risque d'attrition.",
        "recommendation_en": "Monitor customer response to retention gesture and evaluate churn risk reduction."
    }
]

def get_default_scenario_definition():
    """Returns default scenario metadata and stages."""
    return {
        "scenario_name": DEFAULT_SCENARIO_NAME,
        "description": DEFAULT_SCENARIO_DESCRIPTION,
        "stages": DEFAULT_STAGES
    }
