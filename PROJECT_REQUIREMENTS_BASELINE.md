# Project Requirements Baseline — AI-First CRM HCP Module

## 1. Project objective
Build an AI-first CRM module for pharma field representatives to log interactions with Healthcare Professionals (HCPs) in a fast, compliant, and structured way.

The solution must support two input modes for the same workflow:
- A structured form for deterministic entry
- A conversational chat interface for rapid voice-of-rep style input

Both paths must write to the same database and use the same core business logic.

---

## 2. Problem statement
Field representatives often visit HCPs and later struggle to document the meeting accurately. Manual notes are inconsistent, follow-ups are missed, and compliance review is slow.

This module should help reps:
- record visits quickly,
- capture structured data from unstructured notes,
- retrieve prior history for context,
- schedule follow-ups,
- and maintain compliance guardrails.

---

## 3. Functional requirements

### 3.1 Log Interaction Screen
The app must provide a Log Interaction Screen with:
- HCP selection
- interaction type and channel
- free-text notes or chat input
- AI-generated structured summary
- ability to save or edit records

### 3.2 Dual input experience
The user must be able to submit interaction information through either:
1. A structured form, or
2. A conversational chat interface.

Both input modes must produce the same data model and save into the same interaction records.

### 3.3 HCP context retrieval
Before logging a new interaction, the system should allow the user to fetch HCP context such as:
- HCP name
- specialty
- segment/tier
- recent interactions/history

### 3.4 Interaction editing
The system should allow editing an existing interaction and re-running the AI extraction logic so summaries and structured fields remain consistent.

### 3.5 Follow-up scheduling
The system should allow the user to set or change a follow-up action/date for a logged interaction.

### 3.6 Compliance review
The system should run a compliance review on logged interactions and flag issues such as:
- off-label claims
- unapproved efficacy/safety claims
- payment-for-prescribing wording

### 3.7 Conversation-based assistance
The chat experience should allow the rep to request actions in natural language such as:
- log a new interaction
- edit a previous interaction
- fetch HCP history
- schedule follow-up
- run compliance review

---

## 4. Technical requirements

### 4.1 Frontend
- React UI
- Redux Toolkit for state management
- Google Inter font
- UI must support both structured form and conversational chat modes

### 4.2 Backend
- Python with FastAPI
- SQLAlchemy ORM
- REST endpoints for HCPs, interactions, and chat

### 4.3 AI and agent framework
- LangGraph is mandatory
- LLM is mandatory
- Primary model: Groq gemma2-9b-it
- Fallback model: llama-3.3-70b-versatile (optional but recommended)

### 4.4 Database
- PostgreSQL is the target production database
- SQLite is acceptable as a local/dev fallback

---

## 5. LangGraph agent role
The LangGraph agent is the intelligent orchestration layer between the rep’s message and the CRM workflow.

Its role is to:
- understand the user intent,
- choose the correct tool,
- execute the relevant action against the database,
- and return a natural-language response to the rep.

The agent must serve as the single intelligence layer for conversational workflow handling.

---

## 6. Required LangGraph tools
The LangGraph agent must implement at least five tools for sales-related CRM activity.

| Tool | Purpose |
|---|---|
| log_interaction | Create a new interaction from raw notes or chat text and extract structured details |
| edit_interaction | Update an existing interaction and re-run extraction so the summary stays current |
| fetch_hcp_history | Retrieve HCP profile context and past interactions |
| schedule_followup | Create or update follow-up action/date for an interaction |
| compliance_check | Review the interaction note and flag compliance concerns |

These tools must be reusable from both the chat flow and the structured form path where appropriate.

---

## 7. Data model requirements

### HCP
- id
- name
- specialty
- hospital
- email
- phone
- segment

### Interaction
- id
- hcp_id
- interaction_type
- channel
- interaction_date
- raw_notes
- summary
- topics_discussed
- products_discussed
- sentiment
- samples_dropped
- follow_up_action
- follow_up_date
- compliance_flag
- compliance_reason
- created_via (form or chat)

---

## 8. API requirements
The backend should expose endpoints for:
- listing HCPs
- creating/selecting an HCP
- creating a new interaction
- editing an existing interaction
- retrieving HCP history
- scheduling follow-up
- reviewing compliance
- chat-based agent interaction

---

## 9. UI requirements
The interface should include:
- a sidebar or selection panel for HCPs
- a structured form tab
- a conversational chat tab
- an interaction history panel
- buttons/actions to edit or recheck compliance

The UI must feel simple and fast for a field rep, not like a complex enterprise form.

---

## 10. Non-functional requirements
- Fast response time for simple chat requests
- Clear and professional AI-generated responses
- Safe handling of compliance-sensitive content
- Structured outputs should be deterministic enough to save into the database
- Local development must be easy to run without heavy setup

---

## 11. Acceptance criteria
The solution is accepted when:
- the user can log an interaction through a form
- the user can log an interaction through chat
- the agent can route to at least five tools
- the system can retrieve HCP history
- the system can schedule follow-up actions
- the system can review compliance and return a flag/reason
- the structured and chat flow both persist data into the same system

---

## 12. Recommended implementation scope for Round 1
For the first submission, prioritize:
1. HCP selection
2. interaction logging
3. chat-based agent routing
4. five core tools
5. basic history/follow-up/compliance flow
6. clean UI with React + Redux

This scope is sufficient to demonstrate the assignment objective without over-scoping the build.
