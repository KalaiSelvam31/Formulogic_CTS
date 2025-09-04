from fastapi import APIRouter, HTTPException, Depends, status
from app import schemas
from app.database import User
from app.security import verify_token
from app.ml_models.registry import ml_models
from app.ml_models.therapeutic_eq_helper import PBMRecommender
from app.ml_models.cpmp_helper import CPMPCalculator
router = APIRouter()
@router.post("/savings-analysis", response_model=schemas.CPMPSavingsResponse, tags=["CPMP Analysis"])
def get_cpmp_savings_analysis(
    request: schemas.CPMPSavingsRequest,
    current_user: User = Depends(verify_token)
):
    recommender_model: PBMRecommender = ml_models.get("therapeutic_equivalence")
    if not recommender_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Therapeutic Equivalence model is not available, which is required for this analysis."
        )

    cpmp_calculator = CPMPCalculator(recommender=recommender_model)

    # Call the new dedicated analysis function in the helper
    result = cpmp_calculator.analyze_savings_from_single_rxcui(
        rxcui=request.rxcui,
        current_cost=request.current_cost,
        utilization_rate=request.utilization_rate
    )

    return result