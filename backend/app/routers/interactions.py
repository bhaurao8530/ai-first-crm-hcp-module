from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..agent import tools as T

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.get("/", response_model=List[schemas.InteractionOut])
def list_interactions(hcp_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.date.desc()).all()


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@router.post("/", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Used by the STRUCTURED FORM path. Calls tool #1 (log_interaction)."""
    try:
        interaction = T.log_interaction(
            db,
            hcp_id=payload.hcp_id,
            raw_notes=payload.raw_notes or "",
            interaction_type=payload.interaction_type,
            channel=payload.channel,
            created_via="form",
        )
        return interaction
    except Exception as e:
        raise HTTPException(400, str(e))


@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    """Used by the STRUCTURED FORM edit path. Calls tool #2 (edit_interaction)."""
    try:
        updates = {k: v for k, v in payload.model_dump().items() if v is not None}
        interaction = T.edit_interaction(db, interaction_id, updates)
        return interaction
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"ok": True}


@router.post("/{interaction_id}/compliance-check", response_model=schemas.InteractionOut)
def recheck_compliance(interaction_id: int, db: Session = Depends(get_db)):
    """Tool #5 exposed directly (e.g. a 'Re-run compliance' button in the UI)."""
    try:
        return T.compliance_check(db, interaction_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
