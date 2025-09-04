from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

# Application-specific imports
from app import database as models, schemas
from app.deps import get_db
from app.security import verify_token
from app.ml_models.registry import ml_models
from app.ml_models.drug_utilization_helper import DrugUtilizationForecaster

router = APIRouter()

@router.post("/drug-utilization-forecast", response_model=schemas.DrugUtilizationResponse, tags=["Drug Utilization Forecast"])
def get_drug_utilization_forecast(
    request: schemas.DrugUtilizationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_token)
):
    """
    Provides a forecast for drug utilization (claims and beneficiaries)
    for a specified number of future years. This endpoint requires authentication.
    """
    # Retrieve the loaded model from the central registry
    model: DrugUtilizationForecaster = ml_models.get("drug_utilization")
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Drug Utilization Forecast model is not available."
        )

    # Call the model's prediction method with user input
    result = model.forecast_drug(drug_name=request.drug_name, steps=request.steps)

    # Handle cases where the model returns an error (e.g., drug not found)
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )

    # As requested, results are not logged to the database for this endpoint.
    # The request is authenticated, and the result is returned directly.
    return result

