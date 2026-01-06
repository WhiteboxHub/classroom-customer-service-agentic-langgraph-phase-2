# LangGraph Agentic AI Architecture

## Overview

This is a production-grade Agentic AI system built on LangGraph that evolves a RAG chatbot into a stateful, action-taking, human-supervised AI execution engine.

## Architectural Principles

### Core Rules (DO NOT VIOLATE)

1. **LLMs are "brains" (planning, reasoning, evaluation)** - They generate plans and suggestions
2. **Tools are "hands" (deterministic execution)** - All tool execution is explicit and permission-checked
3. **LangGraph controls all execution flow** - LLMs never control flow directly
4. **State is the single source of truth** - All state transitions are explicit and auditable
5. **Human approvals are graph nodes** - Not exceptions, but first-class nodes
6. **Sentinel has veto power** - Safety agent can block execution
7. **No agent may access tools outside its domain** - Permission enforcement is mandatory

## Architecture Components

### 1. State Schema (`src/core/graph/state_schema.py`)

The `AgentState` TypedDict is the shared blackboard:

- **messages**: Conversation history (append-only)
- **plan**: LLM-generated execution plan with steps
- **tool_calls**: All tool invocations (pending, approved, executed)
- **approval_requests**: Human-in-the-loop approvals
- **audit_trail**: All state transitions for replayability
- **sentinel_veto**: Safety agent veto decision
- **scratchpad**: Agent-to-agent communication
- **user_info**: Session and auth context

### 2. Graph Engine (`src/core/graph/engine.py`)

LangGraph execution engine with complete node graph:

```
orchestrator → (claims|billing|scheduling) → sentinel → __end__
```

- **orchestrator**: LLM-powered intent classification and planning
- **claims/billing/scheduling**: Domain agents with LLM-assisted tool selection
- **sentinel**: LLM-powered safety critic with veto power

### 3. LLM Integration (`src/core/llm.py`)

Centralized LLM initialization with agent-specific configurations:
- Orchestrator: temperature 0.1 (precise routing)
- Claims: temperature 0.2 (balanced)
- Billing: temperature 0.1 (strict accuracy)
- Scheduling: temperature 0.3 (flexible)
- Sentinel: temperature 0.0 (deterministic safety)

### 4. Tool Registry (`src/core/tools/registry.py`)

Permission-based tool registry:
- **ToolPermission**: Enum of permission levels (CLAIMS_READ, BILLING_WRITE, etc.)
- **AGENT_PERMISSIONS**: Mapping of agents to their allowed permissions
- **ToolRegistry**: Central registry with permission checking
- **No agent may access tools outside its domain**

### 5. MCP Client (`src/interfaces/mcp_client.py`)

Model Context Protocol client with:
- Permission enforcement on every tool call
- Tool call creation and tracking
- Audit logging integration

### 6. Agent Nodes

#### Orchestrator (`src/agents/orchestrator.py`)
- LLM analyzes user intent
- Creates structured execution plan
- Routes to appropriate domain agent

#### Domain Agents (`src/agents/{claims,billing,scheduling}/agent.py`)
- LLM selects which tools to use
- Tools are executed via MCP client (permission-checked)
- LLM synthesizes response from tool results

#### Sentinel (`src/agents/backend/sentinel.py`)
- LLM-powered safety/compliance checks
- Can veto execution if violations detected
- Checks: HIPAA, PCI-DSS, fraud, policy violations

### 7. Memory System

#### Short-term (`src/core/memory/short_term.py`)
- Postgres-based conversation summaries
- Summaries created after each step
- Used for grounding only (not control decisions)

#### Long-term (`src/core/memory/long_term.py`)
- Vector DB for historical context retrieval
- Used for grounding only (not control decisions)

### 8. Security Layers

- **PII Scrubbing** (`src/core/security/pii_scrubber.py`): Input sandboxing
- **Auth Context** (`src/core/security/auth_context.py`): Identity propagation
- **Audit Logger** (`src/core/security/audit_logger.py`): All state transitions logged

## Execution Flow

1. **User Input** → PII scrubbed
2. **Initial State** → Created with scrubbed input
3. **Orchestrator Node** → LLM classifies intent, creates plan
4. **Domain Agent Node** → LLM selects tools, tools executed (permission-checked)
5. **Sentinel Node** → LLM checks safety/compliance, can veto
6. **Memory Summary** → Step summary saved (non-blocking)
7. **Response** → Final response returned to user

## State Transitions

All state transitions are:
- **Explicit**: Returned as dict updates from nodes
- **Auditable**: Logged in audit_trail
- **Replayable**: Full state history available
- **Immutable**: Nodes return updates, state is merged

## Tool Execution

1. LLM suggests tools (in domain agent node)
2. ToolCall objects created
3. Permission check via ToolRegistry
4. Tool executed via MCP client
5. Results added to state
6. LLM synthesizes response from results

## Safety & Compliance

- **Sentinel Veto**: Can block execution at any time
- **Permission Enforcement**: Agents can only use their domain tools
- **Audit Trail**: All actions logged for compliance
- **PII Scrubbing**: Input sanitization before processing
- **Human Approvals**: Write operations can require approval (framework in place)

## Memory Usage

- **Short-term**: Summaries after each step (Postgres)
- **Long-term**: Historical context retrieval (Vector DB)
- **Rule**: Memory is for grounding only, never for control decisions

## Error Handling

- Graceful degradation: Memory failures don't block execution
- Fallback routing: If LLM fails, keyword-based routing used
- Audit logging: All errors logged
- User-friendly: Errors return helpful messages

## Production Considerations

- All LLM outputs are structured JSON and validated
- No magic globals
- No hidden side effects
- All node functions follow `(state) -> state` pattern
- Minimal but correct business logic
- Clear separation of concerns

## Next Steps for Production

1. Add database migrations for `conversation_summaries` table
2. Implement async tool execution properly
3. Add human approval workflow nodes
4. Enhance sentinel with more compliance checks
5. Add monitoring and observability
6. Implement rate limiting and throttling
7. Add comprehensive error recovery
8. Implement state persistence for long-running sessions

