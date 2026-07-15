"""
LangGraph agent that powers the conversational side of the Log Interaction
Screen. The agent's job: take whatever the rep types in the chat box, figure
out which of the 5 tools is needed (or ask a clarifying question), run it
against the DB, and reply in natural language.

Graph shape:

    START -> classify_intent -> route -> {log, edit, history, followup, compliance} -> respond -> END

classify_intent uses the LLM (Groq) to decide which tool applies and to pull
out any parameters (interaction_id, hcp_id, etc.) from the message + running
conversation state. Each tool node calls the corresponding function in
tools.py against the real DB session, then `respond` turns the tool's result
back into a friendly chat reply (also via the LLM).
"""
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from ..llm import safe_invoke, extract_json
from . import tools as T


class AgentState(TypedDict, total=False):
    message: str
    hcp_id: Optional[int]
    session_id: str
    intent: str
    params: dict
    tool_result: dict
    reply: str
    error: Optional[str]


ROUTER_SYSTEM_PROMPT = """You are the router for a pharma CRM chat agent.
Classify the rep's message into exactly one of these intents:
- "log_interaction": rep is describing a new visit/call/email with a doctor
- "edit_interaction": rep wants to change/correct a previously logged interaction
- "fetch_hcp_history": rep is asking about a doctor's profile or past visits
- "schedule_followup": rep wants to set/change a follow-up/next-step/reminder
- "compliance_check": rep is asking to re-check compliance on a logged note
- "chitchat": greeting, thanks, or anything not matching the above

Respond ONLY with JSON:
{"intent": "<one of the above>",
 "interaction_id": <int or null, if the message references an existing log>,
 "follow_up_date": "<ISO date string or null>"}
"""


def classify_intent(state: AgentState) -> AgentState:
    raw = safe_invoke(state["message"], system=ROUTER_SYSTEM_PROMPT)
    data = extract_json(raw)
    state["intent"] = data.get("intent", "chitchat")
    state["params"] = {
        "interaction_id": data.get("interaction_id"),
        "follow_up_date": data.get("follow_up_date"),
    }
    return state


def route(state: AgentState) -> Literal[
    "log_interaction", "edit_interaction", "fetch_hcp_history",
    "schedule_followup", "compliance_check", "chitchat"
]:
    return state["intent"] if state["intent"] in (
        "log_interaction", "edit_interaction", "fetch_hcp_history",
        "schedule_followup", "compliance_check",
    ) else "chitchat"


def make_node_log_interaction(db: Session):
    def _node(state: AgentState) -> AgentState:
        if not state.get("hcp_id"):
            state["error"] = "no_hcp_selected"
            return state
        interaction = T.log_interaction(
            db, hcp_id=state["hcp_id"], raw_notes=state["message"], created_via="chat"
        )
        state["tool_result"] = {
            "tool": "log_interaction",
            "interaction_id": interaction.id,
            "summary": interaction.summary,
            "sentiment": interaction.sentiment,
            "topics": interaction.topics_discussed,
            "compliance_flag": interaction.compliance_flag,
        }
        return state
    return _node


def make_node_edit_interaction(db: Session):
    def _node(state: AgentState) -> AgentState:
        interaction_id = state["params"].get("interaction_id")
        if not interaction_id:
            state["error"] = "no_interaction_id"
            return state
        interaction = T.edit_interaction(db, interaction_id, {"raw_notes": state["message"]})
        state["tool_result"] = {
            "tool": "edit_interaction",
            "interaction_id": interaction.id,
            "summary": interaction.summary,
        }
        return state
    return _node


def make_node_fetch_history(db: Session):
    def _node(state: AgentState) -> AgentState:
        if not state.get("hcp_id"):
            state["error"] = "no_hcp_selected"
            return state
        result = T.fetch_hcp_history(db, state["hcp_id"])
        state["tool_result"] = {"tool": "fetch_hcp_history", **result}
        return state
    return _node


def make_node_schedule_followup(db: Session):
    def _node(state: AgentState) -> AgentState:
        interaction_id = state["params"].get("interaction_id")
        if not interaction_id:
            state["error"] = "no_interaction_id"
            return state
        interaction = T.schedule_followup(
            db, interaction_id, follow_up_action=state["message"],
            follow_up_date=state["params"].get("follow_up_date"),
        )
        state["tool_result"] = {
            "tool": "schedule_followup",
            "interaction_id": interaction.id,
            "follow_up_action": interaction.follow_up_action,
        }
        return state
    return _node


def make_node_compliance_check(db: Session):
    def _node(state: AgentState) -> AgentState:
        interaction_id = state["params"].get("interaction_id")
        if not interaction_id:
            state["error"] = "no_interaction_id"
            return state
        interaction = T.compliance_check(db, interaction_id)
        state["tool_result"] = {
            "tool": "compliance_check",
            "interaction_id": interaction.id,
            "compliance_flag": interaction.compliance_flag,
            "compliance_reason": interaction.compliance_reason,
        }
        return state
    return _node


def node_chitchat(state: AgentState) -> AgentState:
    state["tool_result"] = {"tool": "chitchat"}
    return state


def respond(state: AgentState) -> AgentState:
    if state.get("error") == "no_hcp_selected":
        state["reply"] = "Please select an HCP first so I know whose record to update."
        return state
    if state.get("error") == "no_interaction_id":
        state["reply"] = "Which logged interaction do you mean? Please give me the interaction ID."
        return state

    prompt = f"""Rep said: "{state['message']}"
Tool that ran: {state['tool_result']}
Write a short, warm, professional confirmation reply to the field rep (2-3 sentences max),
summarizing what happened in plain English. If it's chitchat, just reply naturally."""
    state["reply"] = safe_invoke(prompt, system="You are a helpful CRM assistant for pharma field reps.")
    return state


def build_graph(db: Session):
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("log_interaction", make_node_log_interaction(db))
    graph.add_node("edit_interaction", make_node_edit_interaction(db))
    graph.add_node("fetch_hcp_history", make_node_fetch_history(db))
    graph.add_node("schedule_followup", make_node_schedule_followup(db))
    graph.add_node("compliance_check", make_node_compliance_check(db))
    graph.add_node("chitchat", node_chitchat)
    graph.add_node("respond", respond)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges("classify_intent", route, {
        "log_interaction": "log_interaction",
        "edit_interaction": "edit_interaction",
        "fetch_hcp_history": "fetch_hcp_history",
        "schedule_followup": "schedule_followup",
        "compliance_check": "compliance_check",
        "chitchat": "chitchat",
    })
    for node in ["log_interaction", "edit_interaction", "fetch_hcp_history",
                 "schedule_followup", "compliance_check", "chitchat"]:
        graph.add_edge(node, "respond")
    graph.add_edge("respond", END)

    return graph.compile()


def run_agent(db: Session, message: str, hcp_id: Optional[int], session_id: str) -> AgentState:
    app = build_graph(db)
    initial_state: AgentState = {
        "message": message, "hcp_id": hcp_id, "session_id": session_id,
    }
    final_state = app.invoke(initial_state)
    return final_state
