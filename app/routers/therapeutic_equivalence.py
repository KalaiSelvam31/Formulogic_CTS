from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app import database as models, schemas
from app.deps import get_db
from app.security import verify_token
from app.ml_models.registry import ml_models

router = APIRouter()

@router.post("/recommend-drug", response_model=schemas.DrugRecommenderResponse, tags=["Analysis"])
def get_drug_recommendation(
    request: schemas.DrugRecommenderRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_token)
):
    """
    Recommends alternative drug ingredients based on a given RXCUI.
    Requires authentication and logs the analysis to the database.
    """
    model = ml_models.get("drug_recommender")
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Drug Recommender model is not available."
        )

    result = model.predict(rxcui=request.rxcui, top_n=request.top_n)

    if result.get("message"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message")
        )

    if result.get("alternatives"):
        ingredients_str = ", ".join(
            [alt["ingredient"] for alt in result["alternatives"]]
        )
        db_analysis = models.RecommendationLogDB(
            rxcui=request.rxcui,
            recommended_ingredients=ingredients_str,
            user_id=current_user.id
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

    return result
