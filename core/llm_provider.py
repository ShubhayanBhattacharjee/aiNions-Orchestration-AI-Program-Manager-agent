
import os
import json
import random
import time
from typing import Optional


def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "mock").lower()


def get_model() -> Optional[str]:
    return os.getenv("LLM_MODEL", "").strip() or None


def call_llm(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    """
    Route to the correct LLM provider based on .env config.
    Falls back to mock if provider is 'mock' or on error.
    """
    provider = get_provider()

    try:
        if provider == "gemini":
            return _call_gemini(prompt, system, max_tokens)
        elif provider == "groq":
            return _call_groq(prompt, system, max_tokens)
        elif provider == "openrouter":
            return _call_openrouter(prompt, system, max_tokens)
        elif provider == "anthropic":
            return _call_anthropic(prompt, system, max_tokens)
        elif provider == "openai":
            return _call_openai(prompt, system, max_tokens)
        else:
            return _call_mock(prompt)
    except Exception as e:
        verbose = os.getenv("VERBOSE", "false").lower() == "true"
        if verbose:
            print(f"  [LLM ERROR] {provider}: {e} — falling back to mock")
        return _call_mock(prompt)

def _call_gemini(prompt: str, system: str, max_tokens: int) -> str:
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model_name = get_model() or "gemini-1.5-flash"
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system if system else None,
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
    )
    return response.text


def _call_groq(prompt: str, system: str, max_tokens: int) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)
    model_name = get_model() or "llama-3.1-8b-instant"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model_name, messages=messages, max_tokens=max_tokens
    )
    return response.choices[0].message.content


def _call_openrouter(prompt: str, system: str, max_tokens: int) -> str:
    import requests

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "your_openrouter_api_key_here":
        raise ValueError("OPENROUTER_API_KEY not set")

    model_name = get_model() or "mistralai/mistral-7b-instruct:free"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/nion-orchestration",
            "X-Title": "Nion Orchestration Engine",
        },
        json={"model": model_name, "messages": messages, "max_tokens": max_tokens},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_anthropic(prompt: str, system: str, max_tokens: int) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your_anthropic_api_key_here":
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model_name = get_model() or "claude-3-haiku-20240307"
    kwargs = {"model": model_name, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system

    message = client.messages.create(**kwargs)
    return message.content[0].text

def _call_openai(prompt: str, system: str, max_tokens: int) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)
    model_name = get_model() or "gpt-4o-mini"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=model_name, messages=messages, max_tokens=max_tokens
    )
    return resp.choices[0].message.content

def _call_mock(prompt: str) -> str:
    """
    Generates realistic-looking orchestration outputs without any API.
    Used for testing or when no API key is configured.
    """
    p = prompt.lower()

    # ── L1 Planning ──────────────────────────────────────────
    if "l1 orchestrator" in p or "create a task plan" in p:
        return _mock_l1_plan(prompt)

    # ── L3 Agents ────────────────────────────────────────────
    if "action_item_extraction" in p:
        return _mock_action_items(prompt)
    if "action_item_validation" in p:
        return "Validation complete. All action items reviewed. Missing owners flagged."
    if "action_item_tracking" in p:
        return "Tracking updated. 2 items open, 0 completed, 0 overdue."
    if "risk_extraction" in p:
        return _mock_risks(prompt)
    if "risk_tracking" in p:
        return "Risk register updated. 2 risks open. 1 HIGH, 1 MEDIUM."
    if "issue_extraction" in p:
        return _mock_issues(prompt)
    if "issue_tracking" in p:
        return "Issue tracker updated. 3 issues open. 1 CRITICAL, 2 HIGH."
    if "decision_extraction" in p:
        return _mock_decisions(prompt)
    if "decision_tracking" in p:
        return "Decision log updated. 1 decision pending stakeholder approval."
    if "qna" in p or "q&a" in p or "formulate" in p:
        return _mock_qna(prompt)
    if "report_generation" in p or "generate.*report" in p:
        return _mock_report(prompt)
    if "message_delivery" in p or "send.*message" in p:
        return _mock_delivery(prompt)
    if "meeting_attendance" in p or "meeting.*transcript" in p:
        return _mock_meeting(prompt)
    if "knowledge_retrieval" in p or "retrieve.*context" in p:
        return _mock_knowledge(prompt)
    if "evaluation" in p or "validate.*output" in p:
        return "Relevance: PASS | Accuracy: PASS | Tone: PASS | Gaps Acknowledged: PASS | Result: APPROVED"
    if "instruction_led_learning" in p or "learn.*instruction" in p:
        return "Instruction stored. SOP updated. Rule added to knowledge base."
    return "Task completed successfully."

def _mock_l1_plan(prompt: str) -> str:
    p = prompt.lower()

    if "what's the status" in p or "status of" in p:
        return json.dumps([
            {"task_id": "TASK-001", "target": "L3:knowledge_retrieval", "type": "cross_cutting",
             "purpose": "Retrieve current status of requested feature from project database", "depends_on": []},
            {"task_id": "TASK-002", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Formulate status response with retrieved data", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "target": "L3:evaluation", "type": "cross_cutting",
             "purpose": "Validate accuracy and completeness of response", "depends_on": ["TASK-002"]},
            {"task_id": "TASK-004", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Deliver status response via appropriate channel", "depends_on": ["TASK-003"]},
        ])
    if "can we add" in p or "feasib" in p or "before the" in p:
        return json.dumps([
            {"task_id": "TASK-001", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract action items from feature request", "depends_on": []},
            {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract risks from feasibility request", "depends_on": []},
            {"task_id": "TASK-003", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract decision needed on feature scope", "depends_on": []},
            {"task_id": "TASK-004", "target": "L3:knowledge_retrieval", "type": "cross_cutting",
             "purpose": "Retrieve project timeline and team capacity", "depends_on": []},
            {"task_id": "TASK-005", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Formulate gap-aware feasibility response", "depends_on": ["TASK-001", "TASK-002", "TASK-003", "TASK-004"]},
            {"task_id": "TASK-006", "target": "L3:evaluation", "type": "cross_cutting",
             "purpose": "Evaluate response before sending", "depends_on": ["TASK-005"]},
            {"task_id": "TASK-007", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Send response to requester", "depends_on": ["TASK-006"]},
        ])

    if "should we" in p or "prioritize" in p or "recommend" in p:
        return json.dumps([
            {"task_id": "TASK-001", "target": "L3:knowledge_retrieval", "type": "cross_cutting",
             "purpose": "Retrieve context on both options for informed recommendation", "depends_on": []},
            {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract risks associated with each option", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract decision record for prioritization choice", "depends_on": []},
            {"task_id": "TASK-004", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Formulate recommendation response with trade-off analysis", "depends_on": ["TASK-001", "TASK-002", "TASK-003"]},
            {"task_id": "TASK-005", "target": "L3:evaluation", "type": "cross_cutting",
             "purpose": "Validate recommendation before delivery", "depends_on": ["TASK-004"]},
            {"task_id": "TASK-006", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Deliver recommendation to VP Engineering", "depends_on": ["TASK-005"]},
        ])

    if "meeting" in p or "transcript" in p or "dev:" in p or "qa:" in p:
        return json.dumps([
            {"task_id": "TASK-001", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Capture and process meeting transcript", "depends_on": []},
            {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract action items from meeting discussion", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract issues raised during meeting", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-004", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract risks mentioned in meeting", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-005", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Generate meeting minutes report", "depends_on": ["TASK-002", "TASK-003", "TASK-004"]},
            {"task_id": "TASK-006", "target": "L3:evaluation", "type": "cross_cutting",
             "purpose": "Validate meeting minutes accuracy", "depends_on": ["TASK-005"]},
            {"task_id": "TASK-007", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Distribute meeting minutes to attendees", "depends_on": ["TASK-006"]},
        ])

    if "escalat" in p or "legal" in p or "threatening" in p or "promised" in p:
        return json.dumps([
            {"task_id": "TASK-001", "target": "L3:knowledge_retrieval", "type": "cross_cutting",
             "purpose": "Retrieve full history of promised feature X and delivery timeline", "depends_on": []},
            {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract issues from escalation report", "depends_on": []},
            {"task_id": "TASK-003", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract risks — legal escalation and client relationship", "depends_on": []},
            {"task_id": "TASK-004", "target": "L2:TRACKING_EXECUTION", "type": "l2",
             "purpose": "Extract decision: immediate response strategy", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-005", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Formulate urgent escalation response with facts", "depends_on": ["TASK-001", "TASK-002", "TASK-003", "TASK-004"]},
            {"task_id": "TASK-006", "target": "L3:evaluation", "type": "cross_cutting",
             "purpose": "Evaluate response for legal and reputational risk", "depends_on": ["TASK-005"]},
            {"task_id": "TASK-007", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
             "purpose": "Deliver escalation response with CC to leadership", "depends_on": ["TASK-006"]},
        ])

    # Ambiguous / generic fallback
    return json.dumps([
        {"task_id": "TASK-001", "target": "L3:knowledge_retrieval", "type": "cross_cutting",
         "purpose": "Retrieve context to interpret ambiguous request", "depends_on": []},
        {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION", "type": "l2",
         "purpose": "Extract any implied action items from vague request", "depends_on": ["TASK-001"]},
        {"task_id": "TASK-003", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
         "purpose": "Formulate clarification request response", "depends_on": ["TASK-001", "TASK-002"]},
        {"task_id": "TASK-004", "target": "L3:evaluation", "type": "cross_cutting",
         "purpose": "Validate clarification response", "depends_on": ["TASK-003"]},
        {"task_id": "TASK-005", "target": "L2:COMMUNICATION_COLLABORATION", "type": "l2",
         "purpose": "Deliver clarification request to sender", "depends_on": ["TASK-004"]},
    ])


def _mock_action_items(prompt: str) -> str:
    p = prompt.lower()
    if "sso" in p or "integration" in p:
        return (
            'AI-001: "Assess SSO integration scope and complexity" Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]\n'
            'AI-002: "Review December release timeline capacity" Owner: Engineering Manager | Due: ASAP | Flags: [MISSING_DUE_DATE]'
        )
    if "meeting" in p or "blocked" in p or "bug" in p:
        return (
            'AI-001: "Resolve API integration blocker for Dev" Owner: Tech Lead | Due: Tomorrow | Flags: [URGENT]\n'
            'AI-002: "Fix 3 critical bugs in payment flow" Owner: QA Team | Due: ? | Flags: [MISSING_DUE_DATE, CRITICAL]\n'
            'AI-003: "Review mobile mockups from Designer" Owner: Product Manager | Due: Thursday | Flags: []\n'
            'AI-004: "Evaluate auth module refactor proposal" Owner: Tech Lead | Due: ? | Flags: [MISSING_DUE_DATE]'
        )
    if "speed" in p or "ambiguous" in p:
        return 'AI-001: "Clarify what \'speed things up\' means — identify specific bottleneck" Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE, AMBIGUOUS]'
    return (
        'AI-001: "Evaluate real-time notifications feature" Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]\n'
        'AI-002: "Evaluate dashboard export feature" Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]'
    )


def _mock_risks(prompt: str) -> str:
    p = prompt.lower()
    if "sso" in p:
        return (
            'RISK-001: "SSO integration complexity may delay December release" Likelihood: HIGH | Impact: HIGH\n'
            'RISK-002: "Third-party SSO provider dependency" Likelihood: MEDIUM | Impact: HIGH'
        )
    if "security" in p or "dashboard" in p:
        return (
            'RISK-001: "Delaying security fixes exposes system to vulnerabilities" Likelihood: HIGH | Impact: CRITICAL\n'
            'RISK-002: "Dashboard deprioritization may impact Q4 roadmap commitments" Likelihood: MEDIUM | Impact: MEDIUM'
        )
    if "legal" in p or "escalat" in p:
        return (
            'RISK-001: "Legal escalation from client over missed Q3 commitment" Likelihood: HIGH | Impact: CRITICAL\n'
            'RISK-002: "Reputational damage if situation not resolved quickly" Likelihood: HIGH | Impact: HIGH\n'
            'RISK-003: "Contract breach if SLA violated" Likelihood: MEDIUM | Impact: CRITICAL'
        )
    if "meeting" in p or "blocked" in p:
        return (
            'RISK-001: "Staging environment down — blocks all QA testing" Likelihood: CONFIRMED | Impact: HIGH\n'
            'RISK-002: "Auth module refactor may introduce regressions" Likelihood: MEDIUM | Impact: HIGH'
        )
    return (
        'RISK-001: "Adding 2 features with same timeline" Likelihood: HIGH | Impact: HIGH\n'
        'RISK-002: "Scope creep for 20% revenue increase" Likelihood: MEDIUM | Impact: MEDIUM'
    )


def _mock_issues(prompt: str) -> str:
    p = prompt.lower()
    if "meeting" in p or "blocked" in p:
        return (
            'ISSUE-001: "Dev blocked on API integration — staging environment down" Severity: CRITICAL | Owner: DevOps\n'
            'ISSUE-002: "3 critical bugs found in payment flow" Severity: CRITICAL | Owner: QA Team\n'
            'ISSUE-003: "Auth module technical debt requiring refactor" Severity: MEDIUM | Owner: Tech Lead'
        )
    if "feature x" in p or "promised" in p:
        return (
            'ISSUE-001: "Feature X promised for Q3 not delivered" Severity: CRITICAL | Owner: ? | Flags: [MISSING_OWNER]\n'
            'ISSUE-002: "Client threatening legal escalation" Severity: CRITICAL | Owner: Customer Success\n'
            'ISSUE-003: "No communication sent to client about delay" Severity: HIGH | Owner: Product Manager'
        )
    return 'ISSUE-001: "Scope change request without feasibility assessment" Severity: MEDIUM | Owner: Product Manager'


def _mock_decisions(prompt: str) -> str:
    p = prompt.lower()
    if "sso" in p:
        return 'DEC-001: "Accept or defer SSO integration for December release" Decision Maker: VP Engineering | Status: PENDING'
    if "security" in p or "dashboard" in p:
        return (
            'DEC-001: "Security fixes vs Dashboard — prioritization decision" Decision Maker: VP Engineering | Status: REQUESTED\n'
            'DEC-002: "Resource allocation for chosen priority" Decision Maker: Engineering Manager | Status: PENDING'
        )
    if "legal" in p or "escalat" in p:
        return (
            'DEC-001: "Immediate response strategy for legal escalation" Decision Maker: VP Engineering + Legal | Status: URGENT\n'
            'DEC-002: "Compensation or remediation offer to client" Decision Maker: CEO / COO | Status: PENDING'
        )
    return 'DEC-001: "Accept or reject customer feature request" Decision Maker: ? | Status: PENDING'


def _mock_qna(prompt: str) -> str:
    p = prompt.lower()
    if "status" in p or "authentication" in p:
        return (
            "Response: \"Authentication Feature Status (PRJ-BETA):\n\n"
            "CURRENT STATUS: In Progress — 65% complete\n"
            "• Backend API: DONE\n"
            "• Frontend integration: IN PROGRESS (John's team)\n"
            "• Testing: NOT STARTED\n\n"
            "TIMELINE: On track for Dec 18 delivery\n\n"
            "BLOCKERS: None currently logged\n\n"
            "WHAT I NEED: Confirmation from QA on test plan readiness\""
        )
    if "sso" in p or "december" in p:
        return (
            "Response: \"SSO Integration Feasibility (PRJ-ALPHA):\n\n"
            "WHAT I KNOW:\n"
            "• December release: Dec 15 (code freeze Dec 10)\n"
            "• Team capacity: 85% utilized\n"
            "• SSO typical complexity: 2-3 weeks engineering effort\n\n"
            "WHAT I'VE LOGGED:\n"
            "• 2 action items for SSO scope assessment\n"
            "• 2 risks flagged (timeline + vendor dependency)\n"
            "• 1 pending decision\n\n"
            "WHAT I NEED:\n"
            "• Engineering estimate for SSO implementation\n"
            "• Vendor selection (Okta/Auth0/etc.)\n\n"
            "Preliminary assessment: HIGH RISK given 20 days remaining and 85% capacity.\""
        )
    if "security" in p or "prioritize" in p:
        return (
            "Response: \"Prioritization Recommendation (PRJ-GAMMA):\n\n"
            "RECOMMENDATION: Prioritize Security Fixes\n\n"
            "RATIONALE:\n"
            "• Security vulnerabilities carry compliance and legal risk\n"
            "• Dashboard feature can be deferred to next sprint\n"
            "• Risk profile: Security delay = CRITICAL | Dashboard delay = MEDIUM\n\n"
            "TRADE-OFF:\n"
            "• Dashboard delay may impact Q4 roadmap\n"
            "• Recommend communicating timeline shift to stakeholders\n\n"
            "DECISION NEEDED FROM: VP Engineering\""
        )
    if "legal" in p or "feature x" in p:
        return (
            "Response: \"Urgent: Feature X Escalation (PRJ-DELTA):\n\n"
            "WHAT I FOUND:\n"
            "• Feature X committed: Q3 (Sept 30 deadline)\n"
            "• Current status: NOT DELIVERED\n"
            "• Root cause: [REQUIRES ENGINEERING INPUT]\n\n"
            "IMMEDIATE GAPS:\n"
            "• No delivery timeline from engineering\n"
            "• No client communication about delay\n"
            "• Legal implications unclear\n\n"
            "WHAT I NEED URGENTLY:\n"
            "• Root cause from Engineering team\n"
            "• Legal counsel review\n"
            "• Escalation response approved by VP/CEO\""
        )
    if "speed" in p:
        return (
            "Response: \"Request Clarification Needed:\n\n"
            "I received your message: 'We need to speed things up'\n\n"
            "Could you clarify:\n"
            "1. Which project or workstream? (no project specified)\n"
            "2. What specifically is slow? (development / deployment / decisions / communication)\n"
            "3. What's the target timeline?\n\n"
            "I've logged this as an ambiguous action item and will update once clarified.\""
        )
    return "Response: \"I've processed your request and logged relevant items. Please review the extracted action items and risks.\""


def _mock_report(prompt: str) -> str:
    return (
        "Report generated:\n"
        "• Format: Markdown summary\n"
        "• Sections: Executive Summary, Action Items, Risks, Issues, Decisions\n"
        "• Length: 450 words\n"
        "• Status: READY FOR DELIVERY"
    )


def _mock_delivery(prompt: str) -> str:
    p = prompt.lower()
    channel = "slack" if "slack" in p else "email"
    return (
        f"Channel: {channel}\n"
        "• Recipient: Sender\n"
        "• CC: Project stakeholders\n"
        "• Delivery Status: SENT"
    )


def _mock_meeting(prompt: str) -> str:
    return (
        "Meeting transcript captured:\n"
        "• Duration: ~15 minutes\n"
        "• Participants: Dev, QA, Designer, Tech Lead\n"
        "• Key topics: API blocker, payment bugs, mobile mockups, auth refactor\n"
        "• Minutes: GENERATED\n"
        "• Action Items detected: 4\n"
        "• Issues detected: 3\n"
        "• Risks detected: 2"
    )


def _mock_knowledge(prompt: str) -> str:
    p = prompt.lower()
    if "beta" in p or "authentication" in p:
        return (
            "Project: PRJ-BETA\n"
            "• Feature: Authentication Module\n"
            "• Status: In Progress (65%)\n"
            "• Owner: Engineering Team\n"
            "• Target Date: Dec 18\n"
            "• Engineering Manager: John Doe\n"
            "• Last Update: 2 days ago\n"
            "• Blockers: None"
        )
    if "gamma" in p:
        return (
            "Project: PRJ-GAMMA\n"
            "• Security Fixes: 12 open CVEs (3 CRITICAL)\n"
            "• Dashboard Feature: 40% complete\n"
            "• Sprint capacity: 90% utilized\n"
            "• VP Engineering: Mike Johnson\n"
            "• Next release: Jan 10"
        )
    if "delta" in p:
        return (
            "Project: PRJ-DELTA\n"
            "• Feature X: Committed Q3, NOT DELIVERED\n"
            "• Client: Enterprise Client Corp\n"
            "• Contract value: $250K ARR\n"
            "• Last client contact: 3 weeks ago\n"
            "• Account Manager: Lisa Wong\n"
            "• Internal owner: ? (MISSING)"
        )
    return (
        "Project: PRJ-ALPHA\n"
        "• Current Release Date: Dec 15\n"
        "• Days Remaining: 20\n"
        "• Code Freeze: Dec 10\n"
        "• Current Progress: 70%\n"
        "• Team Capacity: 85% utilized\n"
        "• Engineering Manager: Alex Kim\n"
        "• Tech Lead: David Park"
    )
