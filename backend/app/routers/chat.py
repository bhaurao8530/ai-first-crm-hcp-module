from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, models
from ..agent.graph import run_agent

router = APIRouter(prefix="/api/chat", tags=["Chat Agent"])


@router.post("/", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatMessage, db: Session = Depends(get_db)):
    """Entry point for the CONVERSATIONAL path of the Log Interaction Screen.
    Runs the LangGraph agent, which classifies intent and dispatches to one
    of the 5 tools (log/edit/history/followup/compliance)."""
    final_state = run_agent(db, message=payload.message, hcp_id=payload.hcp_id, session_id=payload.session_id)

    interaction_out = None
    tool_result = final_state.get("tool_result", {})
    interaction_id = tool_result.get("interaction_id")
    if interaction_id:
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if interaction:
            interaction_out = schemas.InteractionOut.model_validate(interaction)

    return schemas.ChatResponse(
        reply=final_state.get("reply", ""),
        tool_used=tool_result.get("tool"),
        interaction=interaction_out,
        state=tool_result,
    )
