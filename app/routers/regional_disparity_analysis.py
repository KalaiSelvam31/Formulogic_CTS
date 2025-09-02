
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, database as models
from app.deps import get_db
from app.security import verify_token


from app.ml_models.registry import ml_models

router = APIRouter()

@router.post("/analyze", response_model=schemas.Regional_out)
def analyze_drug(
        request: schemas.Regional_in,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(verify_token)
):


    model = ml_models.get("regional_disparity")

    if not model:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The Regional Disparity model is not available. Check server logs."
        )


    analysis_result = model.predict(request.rxcui)

    if analysis_result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result.get("message")
        )

    db_analysis = models.RegionalDisparityAnalysis(
        input_rxcui=request.rxcui,
        rxcui=analysis_result.get("rxcui"),
        status=analysis_result.get("status"),
        total_plans_covering_drug=analysis_result.get("total_plans_covering_drug"),
        states_with_coverage=analysis_result.get("states_with_coverage"),
        coverage_gap_percentage=analysis_result.get("coverage_gap_percentage"),
        drug_tier=analysis_result.get("drug_tier"),
        prior_auth_required=analysis_result.get("prior_auth_required"),
        step_therapy_required=analysis_result.get("step_therapy_required"),
        missing_states=", ".join(analysis_result.get("missing_states", [])),
        disparity_message=analysis_result.get("disparity_message"),
        user_id=current_user.id
    )

    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return analysis_result