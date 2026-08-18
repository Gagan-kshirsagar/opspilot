"""Pydantic data models for the OpsPilot evaluation harness."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class EvalCategory(str, Enum):
    KB = "kb"
    SERVICES = "services"
    INCIDENTS = "incidents"
    USERS = "users"
    MULTI_TOOL = "multi_tool"
    OUT_OF_SCOPE = "out_of_scope"


class EvalCase(BaseModel):
    """A single evaluation case with ground truth criteria."""

    id: str = Field(..., description="Unique slug identifying the evaluation case.")
    question: str = Field(..., description="User question or prompt to submit to the agent/retriever.")
    category: EvalCategory = Field(..., description="Category of the test case.")
    expected_points: list[str] = Field(
        default_factory=list,
        description="Key factual phrases or tokens the final synthesized answer must contain.",
    )
    must_cite: list[str] = Field(
        default_factory=list,
        description="Exact or fuzzy document titles that must appear in citations (for KB/multi cases).",
    )
    expected_tools: list[str] = Field(
        default_factory=list,
        description="Names of tools the agent should invoke during reasoning.",
    )
    should_decline: bool = Field(
        default=False,
        description="Whether the agent is expected to decline answering due to missing/out-of-scope info.",
    )


class CaseResult(BaseModel):
    """Execution and scoring result for an individual evaluation case."""

    case_id: str
    category: EvalCategory
    question: str
    passed: bool
    retrieval_hit: float = Field(..., ge=0.0, le=1.0, description="Citation recall vs must_cite docs.")
    tool_selection: float = Field(..., ge=0.0, le=1.0, description="Tool selection accuracy vs expected_tools.")
    point_coverage: float = Field(..., ge=0.0, le=1.0, description="Deterministic factual point coverage score.")
    llm_judge_score: float | None = Field(default=None, description="Optional LLM-as-judge score (1.0 to 5.0).")
    declined: bool = Field(default=False, description="Whether the agent successfully declined.")
    latency_ms: float = Field(..., ge=0.0, description="Wall clock execution time in milliseconds.")
    invoked_tools: list[str] = Field(default_factory=list)
    cited_sources: list[str] = Field(default_factory=list)
    actual_answer: str = Field(default="")
    failure_reasons: list[str] = Field(default_factory=list)


class CategorySummary(BaseModel):
    """Aggregated evaluation metrics for a specific category."""

    total_cases: int
    passed_cases: int
    pass_rate: float
    avg_point_coverage: float
    avg_retrieval_hit: float
    avg_tool_accuracy: float
    avg_latency_ms: float


class AggregateReport(BaseModel):
    """Full evaluation run report and summary metrics."""

    timestamp: str
    mode: str  # "offline" or "live"
    threshold: float
    total_cases: int
    passed_cases: int
    pass_rate: float
    overall_passed: bool
    retrieval_hit_rate: float
    tool_accuracy: float
    decline_accuracy: float
    avg_latency_ms: float
    by_category: dict[str, CategorySummary]
    results: list[CaseResult]
