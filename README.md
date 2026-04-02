# Nion Orchestration Engine

A Python implementation of Nion's three-tier AI orchestration architecture (L1 → L2 → L3).  
Given any inbound message (email, Slack, meeting transcript), the engine reasons about intent, builds a delegation plan, and executes it through a hierarchy of specialised agents — all powered by the Claude API.

---

## Table of Contents

1. [What This Does](#what-this-does)  
2. [Architecture Overview](#architecture-overview)  
3. [How It Works — Step by Step](#how-it-works--step-by-step)  
4. [Project Structure](#project-structure)  
5. [Setup & Installation](#setup--installation)  
6. [Running the Engine](#running-the-engine)  
7. [Test Cases](#test-cases)  
8. [Output Format](#output-format)  
9. [Design Decisions](#design-decisions)

---

## What This Does

The engine accepts a JSON message, analyses it with a three-tier agent hierarchy, and prints a full **Orchestration Map** showing:

- **L1 Plan** — which domains/agents the Orchestrator decided to activate, and why
- **L2/L3 Execution** — each domain coordinator's chosen agents and their detailed outputs

---

## Architecture Overview

```
Input JSON
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  L1 ORCHESTRATOR                                         │
│  • Ingests message, reasons about intent                 │
│  • Produces a task plan                                  │
│  • Delegates to L2 domains OR cross-cutting agents       │
│  • Visibility: L2 domains + cross-cutting agents only    │
└───────┬──────────────────────┬──────────────────────────┘
        │                      │
   L2 domain tasks        L3_CROSS tasks
        │                      │
        ▼                      ▼
┌───────────────┐     ┌──────────────────────┐
│ L2 COORDINATOR│     │ CROSS-CUTTING AGENTS  │
│ per domain    │     │  knowledge_retrieval  │
│               │     │  evaluation           │
│ Coordinates   │     └──────────────────────┘
│ its own L3s   │
└───────┬───────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  L3 AGENTS  (leaf executors)                              │
│                                                           │
│  TRACKING_EXECUTION:                                      │
│    action_item_extraction  action_item_validation         │
│    action_item_tracking    risk_extraction                │
│    risk_tracking           issue_extraction               │
│    issue_tracking          decision_extraction            │
│    decision_tracking                                      │
│                                                           │
│  COMMUNICATION_COLLABORATION:                             │
│    qna   report_generation  message_delivery              │
│    meeting_attendance                                     │
│                                                           │
│  LEARNING_IMPROVEMENT:                                    │
│    instruction_led_learning                               │
└──────────────────────────────────────────────────────────┘
```

### Visibility Rules (strictly enforced)

| Layer | Can See |
|-------|---------|
| L1    | L2 domains + cross-cutting agents |
| L2    | Its own L3 agents + cross-cutting agents |
| L3    | Nothing (leaf executor) |

---

## How It Works — Step by Step

### Step 1 — Input Parsing (`engine.py`)
The raw JSON is parsed into an `InboundMessage` dataclass capturing `message_id`, `source`, `sender`, `content`, and `project`.

### Step 2 — L1 Orchestration (`agents/l1_orchestrator.py`)
Claude is called with a strict system prompt that:
- Explains the visibility rules
- Lists exactly which L2 domains and cross-cutting agents are available
- Demands a JSON plan output with `task_id`, `target_type`, `target`, `purpose`, `depends_on`

The response is parsed and **validated** — any task referencing an agent outside L1's visibility scope raises an error.

### Step 3 — Task Dispatch (`engine.py`)
The engine iterates over the L1 plan:
- `target_type = "L2"` → instantiates an `L2Coordinator` for that domain and calls `.execute()`
- `target_type = "L3_CROSS"` → calls the `L3Executor` directly (cross-cutting agents bypass L2)

### Step 4 — L2 Coordination (`agents/l2_coordinator.py`)
Each L2Coordinator is called with the task and original message context. It calls Claude to decide:
- Which of *its own* L3 agents to invoke
- In what order

The response is parsed and **validated** against the domain's visible agent list.

### Step 5 — L3 Execution (`agents/l3_executor.py`)
Each L3 agent has a **tailored system prompt** defining exactly what it outputs (action items, risks, issues, decisions, QnA responses, evaluation results, etc.).  
Claude is called once per agent and returns structured bullet-point output.

### Step 6 — Rendering (`utils/renderer.py`)
The `OrchestrationResult` is formatted into the required output layout:
```
════ NION ORCHESTRATION MAP ════
[header]
════ L1 PLAN ════
[task list with purposes and dependencies]
════ L2/L3 EXECUTION ════
[domain blocks with nested L3 results]
```

---

## Project Structure

```
nion-orchestration/
│
├── main.py                          # CLI entry point
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── architecture.py              # Agent registry & visibility rules
│   ├── models.py                    # Dataclasses (InboundMessage, L1Task, etc.)
│   ├── engine.py                    # Main pipeline orchestrator
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── l1_orchestrator.py       # L1: intent analysis + planning via LLM
│   │   ├── l2_coordinator.py        # L2: domain coordination via LLM
│   │   └── l3_executor.py           # L3: specialist agent execution via LLM
│   │
│   └── utils/
│       ├── __init__.py
│       └── renderer.py              # Formats OrchestrationResult to text
│
├── test_cases/
│   ├── MSG-101_status_question.json
│   ├── MSG-102_feasibility.json
│   ├── MSG-103_decision.json
│   ├── MSG-104_meeting.json
│   ├── MSG-105_escalation.json
│   └── MSG-106_ambiguous.json
│
└── sample_outputs/                  # Auto-populated by --all-tests
    ├── MSG-101_status_question.txt
    ├── ...
```

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- An Anthropic API key

### Install

```bash
# Clone or unzip the project
cd nion-orchestration

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Running the Engine

### Run the default sample (MSG-001 from the assessment)
```bash
python main.py
```

### Run a specific test case
```bash
python main.py test_cases/MSG-101_status_question.json
```

### Pipe JSON directly
```bash
echo '{"message_id":"MSG-X","source":"slack","sender":{"name":"Alice","role":"Dev"},"content":"Build is broken","project":"PRJ-Z"}' | python main.py
```

### Run ALL test cases and save outputs
```bash
python main.py --all-tests
# Outputs are saved to sample_outputs/
```

---

## Test Cases

| File | Scenario | Key agents activated |
|------|----------|----------------------|
| MSG-101 | Simple status question | knowledge_retrieval, qna, message_delivery |
| MSG-102 | Feasibility / new feature | TRACKING_EXECUTION, knowledge_retrieval, qna |
| MSG-103 | Decision / recommendation | decision_extraction, knowledge_retrieval, qna |
| MSG-104 | Meeting transcript | meeting_attendance, issue_extraction, action_item_extraction |
| MSG-105 | Urgent escalation | knowledge_retrieval, issue_tracking, qna, evaluation |
| MSG-106 | Ambiguous request | knowledge_retrieval, qna (gap-aware) |

---

## Output Format

```
══════════════════════════════════════════════════════════════════════════════
NION ORCHESTRATION MAP
══════════════════════════════════════════════════════════════════════════════
Message : MSG-001
From    : Sarah Chen (Product Manager)
Project : PRJ-ALPHA

══════════════════════════════════════════════════════════════════════════════
L1 PLAN
══════════════════════════════════════════════════════════════════════════════
[TASK-001] → L2:TRACKING_EXECUTION
  Purpose    : Extract action items from customer request

[TASK-004] → L3:knowledge_retrieval (Cross-Cutting)
  Purpose    : Retrieve project context and timeline

[TASK-005] → L2:COMMUNICATION_COLLABORATION
  Purpose    : Formulate gap-aware response
  Depends On : TASK-001, TASK-002, TASK-003, TASK-004

══════════════════════════════════════════════════════════════════════════════
L2/L3 EXECUTION
══════════════════════════════════════════════════════════════════════════════

[TASK-001] L2:TRACKING_EXECUTION
  └─▶ [TASK-001-A] L3:action_item_extraction
        Status : COMPLETED
        Output :
          • AI-001: "Evaluate real-time notifications feature" ...

[TASK-004] L3:knowledge_retrieval (Cross-Cutting)
  Status : COMPLETED
  Output :
    • Project: PRJ-ALPHA
    • Current Release Date: Dec 15
    ...
══════════════════════════════════════════════════════════════════════════════
```

---

## Design Decisions

**Why call Claude at every tier?**  
Each layer (L1, L2, L3) has a different job. L1 reasons about high-level strategy. L2 decides which specialist tools to use. L3 executes with domain expertise. Separate calls with separate system prompts keep each layer focused and easier to audit.

**Why validate LLM outputs against visibility rules in code?**  
The LLM might hallucinate an agent name or bypass a rule. Hard-coded validation in `l1_orchestrator.py` and `l2_coordinator.py` guarantees the architecture contract is never violated regardless of what the model returns.

**Why dataclasses instead of dicts?**  
Type safety and readability. It's much easier to audit `task.target_type` than `task["target_type"]` across a multi-file codebase.

**Why agent-specific system prompts in `l3_executor.py`?**  
Generic prompts produce generic output. Each specialist agent has a concise system prompt that defines exactly what format it should produce (AI-NNN, RISK-NNN, etc.), making the output consistent and parseable.