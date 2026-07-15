"""
The 5 LangGraph tools used by the HCP field-rep agent.

1. log_interaction        - creates a new interaction record, using the LLM
                             to summarize free-text notes and extract entities
                             (topics, products, sentiment, samples).
2. edit_interaction       - updates fields on an already-logged interaction.
3. fetch_hcp_history      - retrieves an HCP's profile + past interactions so
                             the agent has context before logging a new one.
4. schedule_followup      - sets/updates a follow-up action + date on an
                             interaction (next call, sample drop, RTM, etc.)
5. compliance_check       - runs the logged interaction text through the LLM
                             to flag anything that looks like an off-label
                             promotion / compliance risk, per pharma norms.
"""
import json
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from ..models import HCP, Interaction
from ..llm import safe_invoke, extract_json

# ---------------------------------------------------------------------------
# NOTE: tools take a plain dict payload + a live db session is injected by the
# graph node (see graph.py) rather than through the @tool decorator directly,
# since LangGraph tool-calling here is orchestrated manually node-by-node for
# transparency/demo purposes. Each function below is still exposed as a
# LangChain @tool so it can also be bound directly to an LLM tool-calling
# loop if desired.
# ---------------------------------------------------------------------------


EXTRACTION_SYSTEM_PROMPT = """You are a life-sciences CRM assistant helping a
pharma field representative log a call/visit with a doctor (HCP).
Given the rep's raw notes, extract structured data.
Respond ONLY with JSON, no prose, in this exact shape:
{
  "summary": "1-2 sentence professional summary of the interaction",
  "topics_discussed": "comma separated list of clinical/product topics",
  "products_discussed": "comma separated list of drug/product names mentioned, or empty string",
  "sentiment": "Positive | Neutral | Negative (the HCP's receptiveness)",
  "samples_dropped": "comma separated list of samples mentioned as dropped/left, or empty string",
  "follow_up_action": "a concise next-step action if one is implied, else empty string"
}
"""

COMPLIANCE_SYSTEM_PROMPT = """You are a pharma compliance reviewer. Given a
summary of a rep-HCP interaction, decide if it contains any red flags such as:
off-label promotion claims, unapproved efficacy/safety claims, promises of
payment/gifts tied to prescribing, or disparagement of competitor products
with unverified claims.
Respond ONLY with JSON:
{"flag": "OK" or "REVIEW", "reason": "short reason, empty string if OK"}
"""


def _run_extraction(raw_notes: str) -> dict:
    raw = safe_invoke(raw_notes, system=EXTRACTION_SYSTEM_PROMPT)
    data = extract_json(raw)
    return {
        "summary": data.get("summary", "")[:1000],
        "topics_discussed": data.get("topics_discussed", ""),
        "products_discussed": data.get("products_discussed", ""),
        "sentiment": data.get("sentiment", "Neutral"),
        "samples_dropped": data.get("samples_dropped", ""),
        "follow_up_action": data.get("follow_up_action", ""),
    }


def _run_compliance(text: str) -> dict:
    raw = safe_invoke(text, system=COMPLIANCE_SYSTEM_PROMPT)
    data = extract_json(raw)
    return {
        "flag": data.get("flag", "OK"),
        "reason": data.get("reason", ""),
    }


# --- Tool 1: Log Interaction -------------------------------------------------
def log_interaction(db: Session, hcp_id: int, raw_notes: str,
                     interaction_type: str = "Visit", channel: str = "In-person",
                     created_via: str = "chat") -> Interaction:
    """Creates a new interaction. Uses the LLM to summarize free-text notes,
    extract topics/products/sentiment/samples, then runs a compliance check
    on the resulting summary before saving."""
    extracted = _run_extraction(raw_notes)
    compliance = _run_compliance(extracted["summary"] or raw_notes)

    interaction = Interaction(
        hcp_id=hcp_id,
        interaction_type=interaction_type,
        channel=channel,
        raw_notes=raw_notes,
        summary=extracted["summary"],
        topics_discussed=extracted["topics_discussed"],
        products_discussed=extracted["products_discussed"],
        sentiment=extracted["sentiment"],
        samples_dropped=extracted["samples_dropped"],
        follow_up_action=extracted["follow_up_action"],
        compliance_flag=compliance["flag"],
        compliance_reason=compliance["reason"],
        created_via=created_via,
        date=datetime.utcnow(),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


# --- Tool 2: Edit Interaction ------------------------------------------------
def edit_interaction(db: Session, interaction_id: int, updates: dict) -> Interaction:
    """Modifies fields on an existing interaction. If raw_notes is updated,
    re-runs the LLM extraction so summary/topics/sentiment stay in sync."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise ValueError(f"Interaction {interaction_id} not found")

    if "raw_notes" in updates and updates["raw_notes"]:
        extracted = _run_extraction(updates["raw_notes"])
        updates = {**extracted, **updates}

    for key, value in updates.items():
        if hasattr(interaction, key) and value is not None:
            setattr(interaction, key, value)

    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return interaction


# --- Tool 3: Fetch HCP History -----------------------------------------------
def fetch_hcp_history(db: Session, hcp_id: int, limit: int = 5) -> dict:
    """Retrieves an HCP's profile and their most recent interactions, giving
    the agent context (segment, past sentiment, last topics) before it logs
    or edits anything new."""
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise ValueError(f"HCP {hcp_id} not found")
    history = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp_id)
        .order_by(Interaction.date.desc())
        .limit(limit)
        .all()
    )
    return {
        "hcp": {"id": hcp.id, "name": hcp.name, "specialty": hcp.specialty,
                "hospital": hcp.hospital, "segment": hcp.segment},
        "recent_interactions": [
            {"id": i.id, "date": i.date.isoformat(), "summary": i.summary,
             "sentiment": i.sentiment, "topics": i.topics_discussed}
            for i in history
        ],
    }


# --- Tool 4: Schedule Follow-up ----------------------------------------------
def schedule_followup(db: Session, interaction_id: int, follow_up_action: str,
                       follow_up_date: datetime = None) -> Interaction:
    """Sets or updates the follow-up action/date on an interaction (e.g.
    'send updated study data', 'drop samples next visit')."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise ValueError(f"Interaction {interaction_id} not found")
    interaction.follow_up_action = follow_up_action
    if follow_up_date:
        interaction.follow_up_date = follow_up_date
    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return interaction


# --- Tool 5: Compliance Check -------------------------------------------------
def compliance_check(db: Session, interaction_id: int) -> Interaction:
    """Re-runs the compliance review on an interaction's summary/raw_notes
    and stores the resulting flag + reason. Useful as a standalone re-check
    after edits, or for a manager auditing older logs."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise ValueError(f"Interaction {interaction_id} not found")
    text = interaction.summary or interaction.raw_notes or ""
    result = _run_compliance(text)
    interaction.compliance_flag = result["flag"]
    interaction.compliance_reason = result["reason"]
    db.commit()
    db.refresh(interaction)
    return interaction
