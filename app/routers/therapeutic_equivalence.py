from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app import database as models, schemas
from app.deps import get_db
from app.security import verify_token
from app.ml_models.registry import ml_models
from app.ml_models.therapeutic_eq_helper import PBMRecommender

router = APIRouter()

@router.post("/therapeutic-equivalence", response_model=schemas.TherapeuticEquivalentResponse, tags=["Therapeutic Equivalence"])
def get_therapeutic_equivalence(
    request: schemas.TherapeuticEquivalentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_token)
):

    model: PBMRecommender = ml_models.get("therapeutic_equivalence")
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Therapeutic Equivalence model is not available."
        )

    result = model.recommend_by_rxcui(rxcui=request.rxcui, cost=request.cost)

    if result.get("message"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message")
        )

    if result.get("alternatives"):
        db_log = models.TherapeuticEquivalentLog(
            input_rxcui=result["input_rxcui"],
            input_cost=result["input_cost"],
            input_ingredient=result["ingredient"],
            user_id=current_user.id
        )

        for alt in result["alternatives"]:
            db_alternative = models.TherapeuticEquivalentAlternative(
                ingredient=alt["Ingredient"],
                alternative_rxcui=alt["Alternative_RXCUI"],
                alternative_cost=alt["Alternative_cost"],
                cost_difference=alt["Cost_difference"],
                percentage_reduction=alt["Percentage_reduction"]
            )
            db_log.alternatives.append(db_alternative)

        db.add(db_log)
        db.commit()
        db.refresh(db_log)

    return result

