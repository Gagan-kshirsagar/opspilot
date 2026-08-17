"""Typed read-only tools for the OpsPilot ReAct agent.

All tools call existing repositories and retriever. No direct raw SQL.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retriever import Retriever
from app.repositories.incident_repo import IncidentRepository
from app.repositories.service_repo import ServiceRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


# ── Pydantic Tool Input Schemas ──────────────────────────────


class RetrieveDocsInput(BaseModel):
    query: str = Field(
        ...,
        description="Search query to find operational runbooks, SLAs, disaster recovery procedures, or architecture documentation.",
    )


class QueryServicesInput(BaseModel):
    status: str | None = Field(
        default=None,
        description="Optional filter by service status: 'healthy', 'degraded', or 'down'.",
    )
    search: str | None = Field(
        default=None,
        description="Optional search term to match against service name or description note.",
    )


class QueryIncidentsInput(BaseModel):
    status: str | None = Field(
        default=None,
        description="Optional filter by incident status: 'open', 'investigating', or 'resolved'.",
    )
    severity: str | None = Field(
        default=None,
        description="Optional filter by incident severity: 'sev1', 'sev2', or 'sev3'.",
    )
    service_name: str | None = Field(
        default=None,
        description="Optional name of the associated service (e.g. 'API Gateway').",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of incident records to return (default 10, max 20).",
    )


class QueryUsersInput(BaseModel):
    role: str | None = Field(
        default=None,
        description="Optional filter by user role: 'admin', 'manager', or 'viewer'.",
    )
    search: str | None = Field(
        default=None,
        description="Optional search string matching user name or email address.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of user records to return (default 10, max 20).",
    )


class GetServiceDetailInput(BaseModel):
    name_or_id: str = Field(
        ...,
        description="Exact service name (e.g. 'Payment Service') or service UUID.",
    )


# ── Tool Definitions for LLM Function Calling ────────────────


TOOL_DEFINITIONS = [
    {
        "name": "retrieve_docs",
        "description": "Search the OpsPilot knowledge base for operational runbooks, service SLAs, recovery guides, and incident response procedures.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific query to search runbooks and documentation for.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_services",
        "description": "Query the live services catalog for status, availability uptime percentage, and operational notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["healthy", "degraded", "down"],
                    "description": "Filter services by status.",
                },
                "search": {
                    "type": "string",
                    "description": "Search term matching service name or notes.",
                },
            },
        },
    },
    {
        "name": "query_incidents",
        "description": "Query live incident records with filters for severity (sev1/sev2/sev3), status (open/investigating/resolved), and associated service.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "investigating", "resolved"],
                    "description": "Filter by incident status.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["sev1", "sev2", "sev3"],
                    "description": "Filter by incident severity.",
                },
                "service_name": {
                    "type": "string",
                    "description": "Filter by service name (e.g. 'Auth Service').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max records to return (1-20).",
                },
            },
        },
    },
    {
        "name": "query_users",
        "description": "Query live user accounts and team assignments to find service owners, on-call engineers, or administrators.",
        "parameters": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["admin", "manager", "viewer"],
                    "description": "Filter by role.",
                },
                "search": {
                    "type": "string",
                    "description": "Search query for user name or email.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max records to return (1-20).",
                },
            },
        },
    },
    {
        "name": "get_service_detail",
        "description": "Get complete detailed operational status and active open incident count for a specific service by name or ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "name_or_id": {
                    "type": "string",
                    "description": "Exact service name or UUID.",
                }
            },
            "required": ["name_or_id"],
        },
    },
]


# ── Tool Execution Handlers ───────────────────────────────────


async def execute_retrieve_docs(
    args: dict[str, Any],
    session: AsyncSession,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Execute knowledge base retrieval tool."""
    query = str(args.get("query", "")).strip()
    if not query:
        return {"error": "Missing query parameter", "chunks": []}

    r = retriever or Retriever(top_k=4)
    chunks = await r.retrieve(query, session)
    # Filter by minimal score
    filtered = [c for c in chunks if c.score >= 0.45]
    return {
        "query": query,
        "count": len(filtered),
        "chunks": [
            {
                "document_title": c.document_title,
                "ordinal": c.ordinal,
                "snippet": c.content[:350] + ("..." if len(c.content) > 350 else ""),
                "score": round(c.score, 4),
            }
            for c in filtered
        ],
    }


async def execute_query_services(
    args: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    """Execute live services query tool."""
    repo = ServiceRepository(session)
    status_filter = [args["status"]] if args.get("status") else None
    search = args.get("search")

    services = await repo.list_services(
        search=search,
        status_filter=status_filter,
    )
    # Cap to max 15 services
    services_capped = services[:15]
    return {
        "count": len(services),
        "services": [
            {
                "id": str(s.id),
                "name": s.name,
                "status": s.status.value,
                "uptime_pct": float(s.uptime_pct),
                "note": s.note,
            }
            for s in services_capped
        ],
    }


async def execute_query_incidents(
    args: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    """Execute live incidents query tool."""
    repo = IncidentRepository(session)
    status_filter = [args["status"]] if args.get("status") else None
    severity_filter = [args["severity"]] if args.get("severity") else None
    limit = min(int(args.get("limit", 10)), 20)

    service_id: uuid.UUID | None = None
    if args.get("service_name"):
        s_repo = ServiceRepository(session)
        matching = await s_repo.list_services(search=args["service_name"])
        if matching:
            service_id = matching[0].id

    incidents, total = await repo.list_paginated(
        page=1,
        page_size=limit,
        status_filter=status_filter,
        severity_filter=severity_filter,
        service_id_filter=service_id,
    )

    return {
        "total_count": total,
        "returned_count": len(incidents),
        "incidents": [
            {
                "id": str(inc.id),
                "title": inc.title,
                "severity": inc.severity.value,
                "status": inc.status.value,
                "created_at": inc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "resolved_at": (
                    inc.resolved_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                    if inc.resolved_at
                    else None
                ),
            }
            for inc in incidents
        ],
    }


async def execute_query_users(
    args: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    """Execute live users query tool."""
    repo = UserRepository(session)
    role_filter = [args["role"]] if args.get("role") else None
    search = args.get("search")
    limit = min(int(args.get("limit", 10)), 20)

    users, total = await repo.list_paginated(
        page=1,
        page_size=limit,
        role_filter=role_filter,
        search=search,
    )

    return {
        "total_count": total,
        "returned_count": len(users),
        "users": [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role.value,
                "status": u.status.value,
            }
            for u in users
        ],
    }


async def execute_get_service_detail(
    args: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    """Execute single service detail lookup with open incidents."""
    name_or_id = str(args.get("name_or_id", "")).strip()
    if not name_or_id:
        return {"error": "Missing name_or_id parameter"}

    repo = ServiceRepository(session)
    service = None
    try:
        service_uuid = uuid.UUID(name_or_id)
        service = await repo.get_by_id(service_uuid)
    except ValueError:
        # Search by name
        results = await repo.list_services(search=name_or_id)
        for s in results:
            if s.name.lower() == name_or_id.lower() or name_or_id.lower() in s.name.lower():
                service = s
                break

    if not service:
        return {"error": f"Service '{name_or_id}' not found"}

    open_count = await repo.get_open_incident_count(service.id)
    return {
        "id": str(service.id),
        "name": service.name,
        "status": service.status.value,
        "uptime_pct": float(service.uptime_pct),
        "open_incidents": open_count,
        "note": service.note,
    }


async def execute_tool(
    name: str,
    args: dict[str, Any],
    session: AsyncSession,
    retriever: Retriever | None = None,
) -> tuple[dict[str, Any], str]:
    """Dispatch tool by name and return (result_data, concise_summary_string)."""
    logger.info("Agent calling tool '%s' with args: %s", name, args)

    if name == "retrieve_docs":
        res = await execute_retrieve_docs(args, session, retriever)
        count = res.get("count", 0)
        summary = f"Found {count} relevant knowledge base source(s)"
        return res, summary

    elif name == "query_services":
        res = await execute_query_services(args, session)
        count = res.get("count", 0)
        summary = f"Retrieved {count} live service status record(s)"
        return res, summary

    elif name == "query_incidents":
        res = await execute_query_incidents(args, session)
        total = res.get("total_count", 0)
        summary = f"Found {total} incident record(s)"
        return res, summary

    elif name == "query_users":
        res = await execute_query_users(args, session)
        total = res.get("total_count", 0)
        summary = f"Found {total} user account(s)"
        return res, summary

    elif name == "get_service_detail":
        res = await execute_get_service_detail(args, session)
        if "error" in res:
            summary = res["error"]
        else:
            summary = f"Service '{res.get('name')}' is {res.get('status')} ({res.get('open_incidents')} open incidents)"
        return res, summary

    else:
        return {"error": f"Unknown tool '{name}'"}, f"Unknown tool '{name}'"
