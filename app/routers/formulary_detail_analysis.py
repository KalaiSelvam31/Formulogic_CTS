from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session


from app import database as models
from app import schemas
from app.deps import get_db
from app.security import verify_token
from app.ml_models.registry import ml_models


# Pydantic model for the incoming request body
class FormularyAnalyserIn(BaseModel):
    rxcui: str


router = APIRouter()


@router.post("/formulary-analyser", response_model=schemas.FormularyDetailOut, tags=["Analysis"])
def analyze_formulary(
        request: FormularyAnalyserIn,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(verify_token)
):

    model = ml_models.get("formulary_analyzer")
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Formulary Analyser model is not available."
        )

    result = model.predict(request.rxcui)

    cost_data = result.get("patient_cost", {})  # Use .get() for safety
    geo_data = result.get("geography", {})


    db_analysis = models.FormularyDetailAnalysis(
        drug_rxcui=result.get("drug_rxcui"),
        status=result.get("status"),
        plan_name=result.get("plan_name"),
        tier=result.get("tier"),
        restrictions=result.get("restrictions"),
        indications=result.get("indications"),

        preferred_cost=cost_data.get("preferred"),
        non_preferred_cost=cost_data.get("non_preferred"),
        state=geo_data.get("state"),
        county_code=geo_data.get("county_code"),


        user_id=current_user.id
    )

    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    if result.get("status") != "covered":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            # Use the message from the model's result for a more informative error
            detail=result.get("message", "Drug not covered or analysis failed.")
        )


    return result

