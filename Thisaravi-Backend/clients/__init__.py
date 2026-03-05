"""
Client libraries for external service integration.

Modules:
  - agent_runtime_client: Agent-Runtime API wrapper (CV processing, gap analysis, XAI)
  - recommendation_client: Advanced-Recommendation API wrapper (courses, projects, GNN)
  - integration_test: End-to-end workflow demonstration

Usage:
  from clients import AgentRuntimeClient, RecommendationClient
  
  agent = AgentRuntimeClient()
  rec = RecommendationClient()
"""

from .agent_runtime_client import AgentRuntimeClient
from .recommendation_client import RecommendationClient, SkillDeficit

__all__ = [
    "AgentRuntimeClient",
    "RecommendationClient",
    "SkillDeficit",
]
