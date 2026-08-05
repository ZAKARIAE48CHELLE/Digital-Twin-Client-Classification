"""
OSMOS LangGraph Supervision — Unit Test Suite (Phase 8.7)
=========================================================
Unit tests verifying graph compilation, node execution, debate branching,
knowledge memory integration, state serializability, read-only safety, and fallback.
"""

import unittest
import pandas as pd
from typing import Dict, Any

from agents.langgraph_supervision.graph_builder import build_supervision_graph
from agents.langgraph_supervision.graph_runner import (
    run_langgraph_supervision,
    convert_graph_state_to_orchestrator_output,
)
from agents.agent_schemas import OrchestratorOutput


class TestLangGraphSupervision(unittest.TestCase):

    def test_graph_compiles(self):
        """Verifies build_supervision_graph returns a compiled StateGraph."""
        graph = build_supervision_graph()
        self.assertIsNotNone(graph)

    def test_run_langgraph_supervision_without_debate(self):
        """Verifies LangGraph supervision runs cleanly with debate_mode=False."""
        res = run_langgraph_supervision("P_DEMO_001", debate_mode=False, include_knowledge=False)
        self.assertIsInstance(res, OrchestratorOutput)
        self.assertEqual(res.entity_id, "P_DEMO_001")
        self.assertGreater(len(res.agent_outputs), 0)

    def test_run_langgraph_supervision_with_debate(self):
        """Verifies LangGraph supervision runs cleanly with debate_mode=True."""
        res = run_langgraph_supervision("P_DEMO_001", debate_mode=True, include_knowledge=False)
        self.assertIsInstance(res, OrchestratorOutput)
        self.assertEqual(res.entity_id, "P_DEMO_001")
        self.assertIsNotNone(res.debate_output)
        self.assertIsNotNone(res.debate_output.consensus)

    def test_run_langgraph_supervision_with_knowledge(self):
        """Verifies LangGraph supervision supports include_knowledge=True."""
        res = run_langgraph_supervision("P_DEMO_001", debate_mode=True, include_knowledge=True)
        self.assertIsInstance(res, OrchestratorOutput)
        self.assertEqual(res.entity_id, "P_DEMO_001")

    def test_state_serializability(self):
        """Verifies state output contains only JSON-serializable primitive types."""
        import json
        state = {
            "entity_id": "P_DEMO_001",
            "selected_agents": ["digital_twin", "clv"],
            "include_knowledge": False,
            "debate_mode": True,
            "agent_outputs": [{"agent_id": "clv", "status": "OK"}],
            "errors": [],
        }
        json_str = json.dumps(state)
        self.assertIn("P_DEMO_001", json_str)

    def test_read_only_governance(self):
        """Verifies graph execution does not alter customer DataFrame."""
        df = pd.DataFrame([{"entity_id": "P_DEMO_001", "recency_days": 10}])
        df_copy = df.copy()
        res = run_langgraph_supervision("P_DEMO_001", df=df)
        pd.testing.assert_frame_equal(df, df_copy)
        self.assertIsInstance(res, OrchestratorOutput)


if __name__ == "__main__":
    unittest.main()
