# Nion Orchestration Engine

A simplified implementation of Nion's orchestration engine — an AI Program Manager agent that tracks action items, risks, issues, and decisions across projects by routing messages through a structured **L1 → L2 → L3** agent hierarchy.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Environment Setup & API Keys](#environment-setup--api-keys)
5. [LLM Provider Options (All Free Tiers Available)](#llm-provider-options)
6. [Running the Engine](#running-the-engine)
7. [Test Cases](#test-cases)
8. [Sample Outputs](#sample-outputs)
9. [How It Works — Deep Dive](#how-it-works--deep-dive)
10. [Visibility Rules Enforcement](#visibility-rules-enforcement)
11. [Extending the Engine](#extending-the-engine)
12. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
INPUT MESSAGE (JSON)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  L1 ORCHESTRATOR                                            │
│  • Ingests and parses message                               │
│  • Reasons about intent                                     │
│  • Identifies information gaps                              │
│  • Selects strategy                                         │
│  • Generates ordered task plan (TASK-001 → TASK-00N)       │
│                                                             │
│  Visibility: L2 domains + Cross-Cutting agents ONLY        │
└──────┬───────────────────────────────────────┬─────────────┘
       │ delegates to                          │ or directly calls
       ▼                                       ▼
┌─────────────────┐  ┌────────────────┐  ┌─────────────────────┐
│ L2: TRACKING_   │  │ L2: COMM_      │  │  CROSS-CUTTING L3   │
│ EXECUTION       │  │ COLLABORATION  │  │  (visible to all)   │
│                 │  │                │  │                     │
│ Coordinates:    │  │ Coordinates:   │  │ • knowledge_        │
│ • action_item_  │  │ • qna          │  │   retrieval         │
│   extraction    │  │ • report_      │  │ • evaluation        │
│ • action_item_  │  │   generation   │  └─────────────────────┘
│   validation    │  │ • message_     │
│ • action_item_  │  │   delivery     │  ┌─────────────────────┐
│   tracking      │  │ • meeting_     │  │ L2: LEARNING_       │
│ • risk_         │  │   attendance   │  │ IMPROVEMENT         │
│   extraction    │  └────────────────┘  │                     │
│ • risk_tracking │                      │ Coordinates:        │
│ • issue_        │                      │ • instruction_led_  │
│   extraction    │                      │   learning          │
│ • issue_tracking│                      └─────────────────────┘
│ • decision_     │
│   extraction    │
│ • decision_     │
│   tracking      │
└─────────────────┘
```

### Three-Tier Hierarchy

| Layer | Role | Description |
|-------|------|-------------|
| **L1** | Orchestrator | Ingests message, reasons about intent, identifies gaps, selects strategy, generates plan |
| **L2** | Coordinator | Receives directions from L1, coordinates multiple L3 agents, aggregates results |
| **L3** | Agent | Executes specific tasks, returns structured results |

### Visibility Rules (strictly enforced in code)

| Layer | Can See |
|-------|---------|
| L1 | L2 domains + Cross-Cutting agents **only** |
| L2: TRACKING_EXECUTION | Its own L3 agents + Cross-Cutting agents |
| L2: COMMUNICATION_COLLABORATION | Its own L3 agents + Cross-Cutting agents |
| L2: LEARNING_IMPROVEMENT | Its own L3 agents + Cross-Cutting agents |

> L1 **never** delegates directly to L3 domain agents. It delegates to L2, which coordinates L3.

---

## Project Structure

```
nion_orchestration/
│
├── main.py                         # Entry point — CLI runner
│
├── core/
│   ├── __init__.py
│   ├── engine.py                   # NionOrchestrationEngine — main pipeline
│   ├── models.py                   # Data classes: InputMessage, PlannedTask, ExecutedTask, etc.
│   ├── formatter.py                # Renders NION ORCHESTRATION MAP text output
│   └── llm_provider.py             # Unified LLM abstraction (Gemini/Groq/OpenRouter/Anthropic/OpenAI/Mock)
│
├── agents/
│   ├── __init__.py
│   ├── l1/
│   │   ├── __init__.py
│   │   └── orchestrator.py         # L1Orchestrator — plans task graph via LLM
│   ├── l2/
│   │   ├── __init__.py
│   │   └── coordinator.py          # L2Coordinator + CrossCuttingExecutor
│   └── l3/
│       ├── __init__.py
│       └── agents.py               # All 14 L3 agent implementations
│
├── test_cases/
│   ├── test_0.json                 # Sample from assessment (MSG-001)
│   ├── test_1.json                 # Simple Status Question (MSG-101)
│   ├── test_2.json                 # Feasibility Question (MSG-102)
│   ├── test_3.json                 # Decision/Recommendation (MSG-103)
│   ├── test_4.json                 # Meeting Transcript (MSG-104)
│   ├── test_5.json                 # Urgent Escalation (MSG-105)
│   └── test_6.json                 # Ambiguous Request (MSG-106)
│
├── outputs/                        # Auto-generated output files (created at runtime)
│
├── .env.example                    # Environment variable template — copy to .env
├── requirements.txt                # All dependencies (choose your provider)
├── requirements-minimal.txt        # Minimal deps for mock mode only
└── README.md                       # This file
```

---

## Quick Start

### Option A — Zero API Key (Mock Mode, instant setup)

```bash
# 1. Clone / download the project
cd nion_orchestration

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install minimal dependencies
pip install -r requirements-minimal.txt

# 4. Set up environment (mock mode needs no API key)
cp .env.example .env
# In .env, ensure: LLM_PROVIDER=mock

# 5. Run all test cases
python main.py

# Or run a specific test case
python main.py --test 1
```

### Option B — With a Real LLM (Gemini recommended, free)

```bash
# 1-3. Same as above, but install full requirements
pip install -r requirements.txt

# 4. Get a free Gemini API key:
#    https://aistudio.google.com/app/apikey
#    (No credit card required — 15 RPM, 1M tokens/day free)

# 5. Configure .env
cp .env.example .env
# Edit .env:
#   GEMINI_API_KEY=your_actual_key_here
#   LLM_PROVIDER=gemini

# 6. Run
python main.py
```

---

## Environment Setup & API Keys

Copy `.env.example` to `.env` and configure:

```env
# .env

# Choose your provider:
LLM_PROVIDER=gemini        # or: groq | openrouter | anthropic | openai | mock

# Set the matching API key:
GEMINI_API_KEY=your_key_here

# Optional overrides:
LLM_MODEL=                 # Leave blank for auto-selection
SAVE_OUTPUTS=true          # Save output txt files to /outputs
OUTPUT_DIR=outputs
VERBOSE=false              # Print internal engine logs
```

### Full `.env.example` Reference

```env
# =============================================================
# NION ORCHESTRATION ENGINE - Environment Configuration
# =============================================================

# OPTION 1: Google Gemini (RECOMMENDED - generous free tier)
# Get free API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# OPTION 2: Groq (extremely fast, very generous free tier)
# Get free API key at: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# OPTION 3: OpenRouter (aggregator, has free models)
# Get free API key at: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OPTION 4: Anthropic Claude
# Get API key at: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OPTION 5: OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Active provider (gemini | groq | openrouter | anthropic | openai | mock)
LLM_PROVIDER=gemini

# Model override (leave blank for auto-selection per provider)
LLM_MODEL=

# Output settings
SAVE_OUTPUTS=true
OUTPUT_DIR=outputs
VERBOSE=false
```

---

## LLM Provider Options

| Provider | Free Tier | Speed | Quality | Get Key |
|----------|-----------|-------|---------|---------|
| **Gemini** ⭐ | 15 RPM, 1M tokens/day | Fast | High | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Groq** | 14,400 req/day, 30 RPM | Very Fast | High | [console.groq.com](https://console.groq.com/keys) |
| **OpenRouter** | Free models available | Medium | Medium | [openrouter.ai](https://openrouter.ai/keys) |
| **Anthropic** | Paid only | Fast | Very High | [console.anthropic.com](https://console.anthropic.com/) |
| **OpenAI** | Paid only | Fast | Very High | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Mock** | No key needed | Instant | N/A (dummy) | — |

### Auto-selected Models per Provider

| Provider | Default Model |
|----------|--------------|
| Gemini | `gemini-1.5-flash` |
| Groq | `llama-3.1-8b-instant` |
| OpenRouter | `mistralai/mistral-7b-instruct:free` |
| Anthropic | `claude-3-haiku-20240307` |
| OpenAI | `gpt-4o-mini` |

Override any model via `LLM_MODEL=` in `.env`.

---

## Running the Engine

### CLI Usage

```bash
# Run all test cases (default)
python main.py

# Run a specific test case
python main.py --test 1          # Test 1: Simple Status Question
python main.py --test 2          # Test 2: Feasibility Question
python main.py --test 3          # Test 3: Decision/Recommendation
python main.py --test 4          # Test 4: Meeting Transcript
python main.py --test 5          # Test 5: Urgent Escalation
python main.py --test 6          # Test 6: Ambiguous Request
python main.py --test 0          # Sample from assessment (MSG-001)

# Run from your own JSON file
python main.py --input my_message.json

# List all available test cases
python main.py --list-tests

# Override provider on the fly
python main.py --test 1 --provider gemini
python main.py --test 1 --provider mock

# Don't save output to files
python main.py --test 1 --no-save

# Verbose internal logging
python main.py --test 1 --verbose

# Combine flags
python main.py --all --provider groq --verbose
```

### Input JSON Format

```json
{
  "message_id": "MSG-001",
  "source": "email",
  "sender": {
    "name": "Sarah Chen",
    "role": "Product Manager"
  },
  "content": "Your message text here...",
  "project": "PRJ-ALPHA"
}
```

**Field notes:**
- `source`: `email` | `slack` | `meeting` | `teams` | any string
- `project`: can be `null` for unknown projects
- `message_id`: any unique identifier string

---

## Test Cases

| # | Message ID | Source | Scenario | Key Agents Triggered |
|---|------------|--------|----------|----------------------|
| 0 | MSG-001 | email | Sample from assessment — scope change request with 20% revenue upsell | action_item_extraction, risk_extraction, decision_extraction, knowledge_retrieval, qna, evaluation, message_delivery |
| 1 | MSG-101 | slack | Simple status question — "What's the status of the authentication feature?" | knowledge_retrieval, qna, evaluation, message_delivery |
| 2 | MSG-102 | email | Feasibility question — "Can we add SSO integration before December release?" | action_item_extraction, risk_extraction, decision_extraction, knowledge_retrieval, qna, evaluation, message_delivery |
| 3 | MSG-103 | email | Decision/recommendation — "Should we prioritize security fixes or the new dashboard?" | knowledge_retrieval, risk_extraction, decision_extraction, qna, evaluation, message_delivery |
| 4 | MSG-104 | meeting | Meeting transcript — dev blockers, critical bugs, design update, tech debt | meeting_attendance, action_item_extraction, issue_extraction, risk_extraction, report_generation, evaluation, message_delivery |
| 5 | MSG-105 | email | Urgent escalation — client threatening legal action over missed Q3 delivery | knowledge_retrieval, issue_extraction, risk_extraction, decision_extraction, qna, evaluation, message_delivery |
| 6 | MSG-106 | slack | Ambiguous request — "We need to speed things up" (no project, no context) | knowledge_retrieval, action_item_extraction, qna, evaluation, message_delivery |

---

## Sample Outputs

All outputs are saved to the `outputs/` directory. Below is the expected output format:

```
==============================================================================
NION ORCHESTRATION MAP
==============================================================================
Message: MSG-001
From:    Sarah Chen (Product Manager)
Project: PRJ-ALPHA
Source:  email

==============================================================================
L1 PLAN
==============================================================================
[TASK-001] → L2:TRACKING_EXECUTION
  Purpose: Extract action items from customer request

[TASK-002] → L2:TRACKING_EXECUTION
  Purpose: Extract risks from scope change request

[TASK-003] → L2:TRACKING_EXECUTION
  Purpose: Extract decision needed

[TASK-004] → L3:knowledge_retrieval (Cross-Cutting)
  Purpose: Retrieve project context and timeline

[TASK-005] → L2:COMMUNICATION_COLLABORATION
  Purpose: Formulate gap-aware response
  Depends On: TASK-001, TASK-002, TASK-003, TASK-004

[TASK-006] → L3:evaluation (Cross-Cutting)
  Purpose: Evaluate response before sending
  Depends On: TASK-005

[TASK-007] → L2:COMMUNICATION_COLLABORATION
  Purpose: Send response to sender
  Depends On: TASK-006

==============================================================================
L2/L3 EXECUTION
==============================================================================

[TASK-001] L2:TRACKING_EXECUTION
  └─▶ [TASK-001-A] L3:action_item_extraction
        Status: COMPLETED
        Output:
          • AI-001: "Evaluate real-time notifications feature"
            Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]
          • AI-002: "Evaluate dashboard export feature"
            Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]

[TASK-004] L3:knowledge_retrieval (Cross-Cutting)
  Status: COMPLETED
  Output:
    • Project: PRJ-ALPHA
    • Current Release Date: Dec 15
    • Days Remaining: 20
    • Team Capacity: 85% utilized
    • Engineering Manager: Alex Kim

... (continues for all tasks)

==============================================================================
```

---

## How It Works — Deep Dive

### 1. Engine Pipeline (`core/engine.py`)

```
NionOrchestrationEngine.run(message)
  │
  ├─► L1Orchestrator.plan(message)
  │     └─► LLM call → JSON task array → List[PlannedTask]
  │
  ├─► _topological_sort(planned_tasks)
  │     └─► Kahn's algorithm — respects depends_on ordering
  │
  └─► For each task in order:
        ├─► If CROSS_CUTTING → CrossCuttingExecutor.execute()
        │     └─► run_l3_agent(agent_name, context)
        └─► If L2_DOMAIN → L2Coordinator.execute()
              ├─► _select_l3_agents_for_task(domain, purpose)
              └─► run_l3_agent(agent_name, context) for each selected L3
```

### 2. L1 Planning (`agents/l1/orchestrator.py`)

The L1 Orchestrator sends the full message to the LLM with a strict system prompt that:
- Enforces visibility (cannot plan direct L3 domain agent calls)
- Instructs JSON-only output (array of task objects)
- Provides domain descriptions so the LLM selects the right L2

The LLM returns a task plan like:
```json
[
  {"task_id": "TASK-001", "target": "L2:TRACKING_EXECUTION",
   "type": "l2", "purpose": "Extract action items", "depends_on": []},
  {"task_id": "TASK-002", "target": "L3:knowledge_retrieval",
   "type": "cross_cutting", "purpose": "Retrieve project context", "depends_on": []},
  ...
]
```

### 3. L2 Coordination (`agents/l2/coordinator.py`)

Each L2 coordinator receives a task and selects the appropriate L3 agent(s) based on:
- The task's `purpose` string (keyword matching)
- The message `content`
- Visibility rules (only agents belonging to that domain are allowed)

**TRACKING_EXECUTION** selects L3 based on keywords:
- "action item" / "task" → `action_item_extraction`
- "risk" / "blocker" → `risk_extraction`
- "issue" / "bug" / "blocked" → `issue_extraction`
- "decision" / "prioritize" → `decision_extraction`

**COMMUNICATION_COLLABORATION** selects L3 based on keywords:
- "meeting" / "transcript" → `meeting_attendance`
- "report" / "summary" → `report_generation`
- "send" / "deliver" → `message_delivery`
- Default → `qna`

### 4. L3 Agents (`agents/l3/agents.py`)

Each L3 agent builds a targeted LLM prompt from the execution context and returns structured output lines. The context includes:
- Original message content
- Sender name and role
- Project ID
- Task purpose
- Accumulated outputs from dependency tasks

### 5. Dependency Resolution (`core/engine.py`)

Uses **Kahn's topological sort algorithm**:
- Tasks with no dependencies execute first (in parallel conceptually)
- Tasks that depend on others wait for their dependencies
- Outputs from completed tasks are accumulated into context for dependents
- Cycle-safe: remaining tasks added after sort completes

### 6. LLM Provider Abstraction (`core/llm_provider.py`)

Single `call_llm(prompt, system, max_tokens)` function routes to the configured provider. Falls back to **mock mode** on any error, ensuring the engine always produces output even during development/testing.

---

## Visibility Rules Enforcement

The codebase enforces visibility rules at multiple layers:

### L1 — System Prompt Enforcement
```python
# agents/l1/orchestrator.py
L1_SYSTEM_PROMPT = """
VISIBILITY RULES (strictly enforced):
- You can ONLY delegate to L2 domain agents or Cross-Cutting agents
- You CANNOT delegate directly to L3 agents (except Cross-Cutting ones)
- Available L2 domains: L2:TRACKING_EXECUTION, L2:COMMUNICATION_COLLABORATION, L2:LEARNING_IMPROVEMENT
- Available Cross-Cutting (L3): L3:knowledge_retrieval, L3:evaluation
"""
```

### L2 — Code-Level Enforcement
```python
# agents/l2/coordinator.py
allowed = DOMAIN_AGENTS.get(domain, set()) | CROSS_CUTTING_AGENTS
if agent_name not in allowed:
    continue  # Agent not visible to this L2 — skip
```

### Agent Registry
```python
# agents/l3/agents.py
TRACKING_EXECUTION_AGENTS = {"action_item_extraction", "action_item_validation", ...}
COMMUNICATION_COLLABORATION_AGENTS = {"qna", "report_generation", ...}
CROSS_CUTTING_AGENTS = {"knowledge_retrieval", "evaluation"}

DOMAIN_AGENTS = {
    "TRACKING_EXECUTION": TRACKING_EXECUTION_AGENTS,
    "COMMUNICATION_COLLABORATION": COMMUNICATION_COLLABORATION_AGENTS,
    "LEARNING_IMPROVEMENT": LEARNING_IMPROVEMENT_AGENTS,
}
```

---

## Extending the Engine

### Add a New L3 Agent

1. Add agent to `agents/l3/agents.py`:
```python
# In TRACKING_EXECUTION_AGENTS set:
TRACKING_EXECUTION_AGENTS = {
    ...,
    "my_new_agent",      # Add here
}

# Add implementation function:
def _my_new_agent(ctx: Dict) -> str:
    prompt = _build_prompt("my_new_agent", ctx)
    prompt += "\nYour specific instructions here."
    return call_llm(prompt, max_tokens=400)

# Add to dispatch dict in run_l3_agent():
"my_new_agent": _my_new_agent,
```

2. Add selection logic in `agents/l2/coordinator.py`:
```python
if "keyword" in p:
    agents.append("my_new_agent")
```

### Add a New L2 Domain

1. Add to `DOMAIN_AGENTS` in `agents/l3/agents.py`
2. Add selection logic in `agents/l2/coordinator.py → _select_l3_agents_for_task()`
3. Update L1 system prompt in `agents/l1/orchestrator.py`

### Add a New LLM Provider

Add a new `_call_<provider>()` function in `core/llm_provider.py` and add a branch in `call_llm()`.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'dotenv'`
```bash
pip install python-dotenv
```

### `ModuleNotFoundError: No module named 'google.generativeai'`
```bash
pip install google-generativeai
```

### API key errors / rate limits
Switch to mock mode for testing:
```bash
python main.py --provider mock
```
Or set in `.env`: `LLM_PROVIDER=mock`

### Output looks like "Task completed successfully" for everything
This means the mock fallback is active. Either:
- `LLM_PROVIDER=mock` is set (intentional)
- Your API key is missing or invalid — check `.env`

### JSON parse errors in L1 plan
The engine has a robust fallback: if LLM returns invalid JSON, a generic 5-task plan is used. Enable verbose mode to see raw LLM output:
```bash
python main.py --test 1 --verbose
```

### Want to test with a real LLM but save API calls?
Use `--test N` to run a single test case instead of all 7.

---

## Dependencies

```
python-dotenv>=1.0.0      # .env loading (always required)
google-generativeai>=0.7.0 # Gemini provider
groq>=0.9.0               # Groq provider
requests>=2.31.0          # OpenRouter provider
anthropic>=0.34.0         # Anthropic provider
openai>=1.40.0            # OpenAI provider
```

Install only what you need:
```bash
# Mock only (no API key needed):
pip install python-dotenv

# Gemini only:
pip install python-dotenv google-generativeai

# Groq only:
pip install python-dotenv groq

# Everything:
pip install -r requirements.txt
```

---

## License

MIT — free to use and modify.
