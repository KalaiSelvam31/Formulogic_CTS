

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from enum import Enum

# Corrected imports to match your project's structure
from app import database as models
from app.security import verify_token

# Import the model registry and the helper class directly
from app.ml_models.registry import ml_models
from app.ml_models.um_change_analyzer_helper import UMFormularyChangesAnalyzer

router = APIRouter()

# This mapping connects the URL path to the key used in main.py's startup event
COMPARISON_MAP = {
    "june-to-july": "um_change_jun_to_jul",
    "july-to-august": "um_change_jul_to_aug",
    "june-to-august": "um_change_jun_to_aug",
}


# Define an Enum for all possible analysis types
# This will automatically create a dropdown in the API docs
class AnalysisType(str, Enum):
    consolidated_insights = "consolidated_insights"  # ADDED THIS NEW TYPE
    insights = "insights"
    trends = "trends"
    impact = "impact"
    overview = "overview"
    pa_changes = "pa_changes"
    st_changes = "st_changes"
    ql_changes = "ql_changes"
    additions = "additions"
    removals = "removals"


@router.get("/um-change/{comparison_period}/{analysis_type}", response_model=Dict[str, Any], tags=["UM Analysis"])
def get_um_analysis(
        comparison_period: str,
        analysis_type: AnalysisType,  # Use the Enum here for automatic validation and docs
        current_user: models.User = Depends(verify_token)
):
    """
    Retrieves a specific section of a pre-computed UM (Utilization Management) change analysis.
    """
    if comparison_period not in COMPARISON_MAP:
        raise HTTPException(status_code=404, detail=f"Comparison period '{comparison_period}' not found.")

    comparison_key = COMPARISON_MAP[comparison_period]
    analyzer: UMFormularyChangesAnalyzer = ml_models.get(comparison_key)

    if not analyzer:
        raise HTTPException(status_code=503,
                            detail=f"Analyzer for '{comparison_period}' is not available. Ensure the training script has been run.")

    # Dynamically find the analysis key inside the loaded object.
    if not analyzer.monthly_analyses:
        raise HTTPException(status_code=500, detail="Internal Error: Loaded analyzer contains no analysis data.")

    analysis_data_key = next(iter(analyzer.monthly_analyses))

    if not analyzer.set_current_analysis_by_key(analysis_data_key):
        raise HTTPException(status_code=500, detail="Internal Error: Could not set active analysis.")

    # Map the analysis_type string to the correct method on the analyzer object
    analysis_functions = {
        "consolidated_insights": analyzer.get_consolidated_insights,  # ADDED THIS NEW MAPPING
        "insights": analyzer.get_key_insights,
        "trends": analyzer.get_trend_analysis,
        "impact": analyzer.get_impact_analysis,
        "overview": analyzer.get_changes_overview,
        "pa_changes": analyzer.get_detailed_changes_prior_auth,
        "st_changes": analyzer.get_detailed_changes_step_therapy,
        "ql_changes": analyzer.get_detailed_changes_quantity_limit,
        "additions": analyzer.get_detailed_changes_drug_additions,
        "removals": analyzer.get_detailed_changes_drug_removals,
    }

    if analysis_type.value in analysis_functions:
        result = analysis_functions[analysis_type.value]()
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    else:

        raise HTTPException(status_code=404, detail=f"Invalid analysis type: '{analysis_type}'.")