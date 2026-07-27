import unittest
import pandas as pd
import numpy as np
from personas.dynamic_persona_generator import (
    generate_dynamic_personas,
    summarize_cluster_profile,
    assign_dynamic_persona_name,
    generate_dynamic_persona_description,
    generate_dynamic_persona_recommended_action,
    generate_dynamic_persona_channel,
    generate_dynamic_persona_priority
)
from personas.persona_library import DEFAULT_PERSONA_MAP, get_all_personas


class TestDynamicPersonas(unittest.TestCase):

    def setUp(self):
        # Create a mock dataframe with 10 entities across 2 clusters
        self.df_2clusters = pd.DataFrame({
            "entity_id": [f"C{i:05d}" for i in range(1, 11)],
            "entity_type": ["Client"] * 10,
            "dynamic_class": ["High-Value Loyal Client"] * 5 + ["Cold Prospect"] * 5,
            "customer_segment": ["High-Value Loyalists"] * 5 + ["Dormant Low-Value Clients"] * 5,
            "predicted_clv_amount_mad": [12000, 11500, 14000, 10000, 13000, 800, 500, 1200, 900, 600],
            "rfm_score": [0.85, 0.80, 0.90, 0.75, 0.88, 0.20, 0.15, 0.25, 0.18, 0.22],
            "churn_risk_score": [0.10, 0.12, 0.08, 0.15, 0.05, 0.80, 0.75, 0.85, 0.70, 0.65],
            "behavioral_engagement_score": [0.8, 0.7, 0.9, 0.6, 0.8, 0.2, 0.1, 0.2, 0.1, 0.3],
            "ml_cluster_id": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })

        # Create a mock dataframe with 5 clusters
        self.df_5clusters = pd.DataFrame({
            "entity_id": [f"C{i:05d}" for i in range(1, 26)],
            "entity_type": ["Client"] * 25,
            "dynamic_class": ["Regular"] * 25,
            "customer_segment": ["Standard Cohort"] * 25,
            "predicted_clv_amount_mad": [5000] * 25,
            "rfm_score": [0.5] * 25,
            "churn_risk_score": [0.2] * 25,
            "ml_cluster_id": [0]*5 + [1]*5 + [2]*5 + [3]*5 + [4]*5
        })

    def test_cluster_count_2_returns_2_dynamic_personas(self):
        dynamic_personas = generate_dynamic_personas(self.df_2clusters, cluster_col="ml_cluster_id")
        self.assertEqual(len(dynamic_personas), 2)
        self.assertEqual(dynamic_personas[0]["cluster_id"], 0)
        self.assertEqual(dynamic_personas[1]["cluster_id"], 1)

    def test_cluster_count_5_returns_5_dynamic_personas(self):
        dynamic_personas = generate_dynamic_personas(self.df_5clusters, cluster_col="ml_cluster_id")
        self.assertEqual(len(dynamic_personas), 5)

    def test_required_fields_in_dynamic_persona(self):
        dynamic_personas = generate_dynamic_personas(self.df_2clusters, cluster_col="ml_cluster_id")
        required_fields = [
            "cluster_id", "persona_name", "entity_count", "percentage",
            "dominant_entity_type", "dominant_dynamic_class", "dominant_segment",
            "avg_clv", "avg_rfm", "avg_churn_risk", "description",
            "recommended_action", "recommended_channel", "priority_level"
        ]
        for p in dynamic_personas:
            for field in required_fields:
                self.assertIn(field, p, f"Missing field '{field}' in dynamic persona")
                self.assertIsNotNone(p[field], f"Field '{field}' is None")

    def test_naming_and_actions(self):
        summary_vip = {
            "cluster_id": 1,
            "dominant_entity_type": "Client",
            "dominant_dynamic_class": "High-Value Loyal Client",
            "dominant_segment": "High-Value Loyalists",
            "avg_clv": 15000.0,
            "avg_rfm": 0.85,
            "avg_churn_risk": 0.10,
            "avg_engagement": 0.8,
            "avg_conversion_prob": 0.7,
            "avg_purchases_90d": 5.0,
            "avg_total_spent_90d": 12000.0,
            "avg_complaints": 0.0,
            "avg_sentiment": 4.5,
            "count": 10,
            "percentage": 50.0
        }
        name = assign_dynamic_persona_name(summary_vip)
        self.assertIn("Cluster 1 — Dynamic VIP Loyalists", name)

        action = generate_dynamic_persona_recommended_action(summary_vip)
        self.assertIn("VIP loyalty perks", action)

        prio = generate_dynamic_persona_priority(summary_vip)
        self.assertEqual(prio, "High")


    def test_graceful_missing_columns_handling(self):
        sparse_df = pd.DataFrame({
            "entity_id": ["E1", "E2"],
            "ml_cluster_id": [0, 1]
        })
        dynamic_personas = generate_dynamic_personas(sparse_df, cluster_col="ml_cluster_id")
        self.assertEqual(len(dynamic_personas), 2)
        self.assertIn("Cluster 0", dynamic_personas[0]["persona_name"])

    def test_fixed_persona_library_remains_unchanged(self):
        initial_count = len(DEFAULT_PERSONA_MAP)
        self.assertGreaterEqual(initial_count, 9)
        # Generating dynamic personas must not modify DEFAULT_PERSONA_MAP
        generate_dynamic_personas(self.df_2clusters, cluster_col="ml_cluster_id")
        self.assertEqual(len(DEFAULT_PERSONA_MAP), initial_count)


if __name__ == "__main__":
    unittest.main()
