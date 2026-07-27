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
    generate_dynamic_persona_priority,
    get_value_level,
    get_engagement_level,
    get_risk_level,
    is_outlier_cluster,
    get_cluster_reliability_label,
    get_priority_reason
)
from personas.persona_library import DEFAULT_PERSONA_MAP, get_all_personas


class TestDynamicPersonas(unittest.TestCase):

    def setUp(self):
        # Mock dataframe with 10 entities across 2 clusters
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

        # Mock dataframe with 5 clusters
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
            "avg_clv", "avg_rfm", "avg_churn_risk", "value_level",
            "engagement_level", "risk_level", "is_outlier", "reliability_label",
            "description", "recommended_action", "recommended_channel",
            "priority_level", "priority_reason"
        ]
        for p in dynamic_personas:
            for field in required_fields:
                self.assertIn(field, p, f"Missing field '{field}' in dynamic persona")
                self.assertIsNotNone(p[field], f"Field '{field}' is None")

    def test_value_level_thresholds(self):
        self.assertEqual(get_value_level(9000), "High-Value")
        self.assertEqual(get_value_level(5000), "Medium-Value")
        self.assertEqual(get_value_level(134), "Low-Value")
        self.assertEqual(get_value_level(0), "No Current Value / Value Collapse")

    def test_engagement_level_thresholds(self):
        self.assertEqual(get_engagement_level(0.85), "High engagement")
        self.assertEqual(get_engagement_level(0.50), "Moderate engagement")
        self.assertEqual(get_engagement_level(0.30), "Low engagement")
        self.assertEqual(get_engagement_level(0.10), "Very low engagement")

    def test_risk_level_thresholds(self):
        self.assertEqual(get_risk_level(0.80), "High risk")
        self.assertEqual(get_risk_level(0.50), "Medium risk")
        self.assertEqual(get_risk_level(0.10), "Low risk")

    def test_low_clv_low_risk_not_high_priority(self):
        summary_low = {
            "cluster_id": 1,
            "count": 242,
            "total_dataset_count": 1000,
            "avg_clv": 134.0,
            "avg_rfm": 0.52,
            "avg_engagement": 0.52,
            "avg_churn_risk": 0.16,
            "avg_conversion_prob": 0.20,
            "avg_complaints": 0.0,
            "dominant_entity_type": "Client",
            "dominant_dynamic_class": "Active Client",
            "dominant_segment": "Standard Active Clients"
        }
        val_lvl = get_value_level(summary_low["avg_clv"])
        eng_lvl = get_engagement_level(summary_low["avg_rfm"])
        risk_lvl = get_risk_level(summary_low["avg_churn_risk"])
        prio = generate_dynamic_persona_priority(summary_low)

        self.assertEqual(val_lvl, "Low-Value")
        self.assertEqual(eng_lvl, "Moderate engagement")
        self.assertEqual(risk_lvl, "Low risk")
        self.assertNotEqual(prio, "High", "Low CLV with low risk must NOT be High priority")

    def test_high_rfm_not_described_as_low_engagement(self):
        summary_rfm = {
            "cluster_id": 1,
            "count": 10,
            "total_dataset_count": 100,
            "avg_clv": 172679.0,
            "avg_rfm": 0.80,
            "avg_engagement": 0.80,
            "avg_churn_risk": 0.00,
            "avg_conversion_prob": 0.5,
            "dominant_entity_type": "Client",
            "dominant_dynamic_class": "VIP Client",
            "dominant_segment": "High-Value Loyalists"
        }
        eng_lvl = get_engagement_level(summary_rfm["avg_rfm"])
        self.assertEqual(eng_lvl, "High engagement")

        desc = generate_dynamic_persona_description(summary_rfm)
        self.assertIn("high engagement", desc.lower())
        self.assertNotIn("low behavioral engagement", desc.lower())

    def test_micro_cluster_detected(self):
        self.assertTrue(is_outlier_cluster(1, 500, 1000))
        self.assertTrue(is_outlier_cluster(2, 500, 1000))
        self.assertFalse(is_outlier_cluster(50, 500, 1000))

        label_outlier = get_cluster_reliability_label(1, 500)
        self.assertEqual(label_outlier, "Micro-cluster / Outlier")

        label_stable = get_cluster_reliability_label(100, 500)
        self.assertEqual(label_stable, "Stable cluster")

    def test_one_entity_high_clv_named_as_outlier(self):
        summary_one = {
            "cluster_id": 3,
            "count": 1,
            "total_dataset_count": 500,
            "avg_clv": 172679.0,
            "avg_rfm": 0.80,
            "avg_engagement": 0.80,
            "avg_churn_risk": 0.00,
            "avg_conversion_prob": 0.5,
            "dominant_entity_type": "Client",
            "dominant_dynamic_class": "VIP Client",
            "dominant_segment": "High-Value Loyalists"
        }
        name = assign_dynamic_persona_name(summary_one)
        prio = generate_dynamic_persona_priority(summary_one)
        desc = generate_dynamic_persona_description(summary_one)

        self.assertIn("Outlier", name)
        self.assertEqual(prio, "High")
        self.assertIn("micro-cluster", desc.lower())

    def test_priority_reason_exists(self):
        dynamic_personas = generate_dynamic_personas(self.df_2clusters, cluster_col="ml_cluster_id")
        for p in dynamic_personas:
            self.assertIn("priority_reason", p)
            self.assertTrue(len(p["priority_reason"]) > 10)

    def test_duplicate_persona_names_get_qualifier_or_remain_traceable(self):
        df_dups = pd.DataFrame({
            "entity_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
            "entity_type": ["Client"] * 6,
            "dynamic_class": ["Regular"] * 6,
            "customer_segment": ["Standard Cohort"] * 6,
            "predicted_clv_amount_mad": [3000] * 6,
            "rfm_score": [0.55] * 6,
            "churn_risk_score": [0.20] * 6,
            "ml_cluster_id": [0, 0, 0, 1, 1, 1]
        })
        dyn_p = generate_dynamic_personas(df_dups, cluster_col="ml_cluster_id")
        self.assertEqual(len(dyn_p), 2)
        self.assertNotEqual(dyn_p[0]["persona_name"], dyn_p[1]["persona_name"])
        self.assertIn("Cluster 0", dyn_p[0]["persona_name"])
        self.assertIn("Cluster 1", dyn_p[1]["persona_name"])

    def test_description_matches_numeric_levels(self):
        summary = {
            "cluster_id": 1,
            "count": 244,
            "total_dataset_count": 500,
            "avg_clv": 134.0,
            "avg_rfm": 0.53,
            "avg_engagement": 0.53,
            "avg_churn_risk": 0.15,
            "dominant_entity_type": "Client",
            "dominant_dynamic_class": "Active Client",
            "dominant_segment": "Standard Cohort"
        }
        desc = generate_dynamic_persona_description(summary)
        self.assertIn("Low-Value", desc)
        self.assertIn("moderate engagement", desc)
        self.assertIn("low risk", desc)
        self.assertIn("134 MAD", desc)
        self.assertIn("0.15", desc)

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
        generate_dynamic_personas(self.df_2clusters, cluster_col="ml_cluster_id")
        self.assertEqual(len(DEFAULT_PERSONA_MAP), initial_count)


if __name__ == "__main__":
    unittest.main()
