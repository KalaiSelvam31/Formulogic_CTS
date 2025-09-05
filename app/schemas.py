from typing import Optional, List, Dict, Literal

from pydantic import BaseModel, Field,EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Register(BaseModel):
    username:str
    first_name:str
    last_name:str
    email:EmailStr
    password:str

class VerifyOTP(BaseModel):
     email: EmailStr
     otp: str
class ForgotPasswordRequest(BaseModel):

    email: EmailStr

class ResetPasswordRequest(BaseModel):

    email: EmailStr
    otp: str
    new_password: str
#
class Regional_out(BaseModel):
    rxcui: str
    status: str
    message: Optional[str] = None
    model_prediction: Optional[str] = None
    total_plans_covering_drug: Optional[int] = None
    states_with_coverage: Optional[str] = None
    coverage_gap_percentage: Optional[str] = None
    drug_tier: Optional[str] = None
    prior_auth_required: Optional[str] = None
    step_therapy_required: Optional[str] = None
    missing_states: Optional[List[str]] = None
    disparity_message: Optional[str] = None

    class Config:
        from_attributes = True

class Regional_in(BaseModel):
    rxcui: str


class FormularyDetailOut(BaseModel):
    drug_rxcui: str
    status: str
    plan_name: str
    tier: str
    restrictions: str
    indications: str
    patient_cost: Dict[str, str]
    geography: Dict[str, str]

    class Config:
        orm_mode = True

class ResendOTPRequest(BaseModel):
    email: str
    context: Literal["register", "forgot_password"]

class TherapeuticEquivalentRequest(BaseModel):
    rxcui: int
    cost: float

class AlternativeDrug(BaseModel):
    Ingredient: str
    Alternative_RXCUI: int
    Alternative_cost: float
    Cost_difference: float
    Percentage_reduction: str

class TherapeuticEquivalentResponse(BaseModel):
    input_rxcui: int
    input_cost: float
    ingredient: str
    alternatives: List[AlternativeDrug]

class DrugUtilizationRequest(BaseModel):

    drug_name: str
    steps: int = 5

class HistoricalData(BaseModel):

    years: List[int]
    Total_Claims: List[int]
    Total_Beneficiaries: List[int]

class ForecastData(BaseModel):

    Total_Claims: List[int]
    Total_Beneficiaries: List[int]

class DrugUtilizationResponse(BaseModel):
    drug: str
    forecast_years: List[int]
    historical: HistoricalData
    forecast: ForecastData

class CPMPSavingsRequest(BaseModel):
    rxcui: int
    current_cost: float
    utilization_rate: float

class CPMPSavingsSummary(BaseModel):
    original_rxcui: int
    original_cost_per_member: float
    best_alternative_rxcui: int
    alternative_cost_per_member: float
    utilization_rate_analyzed: float

class CPMPSavingsPotential(BaseModel):
    cpmp_reduction: float
    percentage_reduction: float
    total_annual_savings: float

class CPMPSavingsResponse(BaseModel):
    analysis_summary: CPMPSavingsSummary
    original_cpmp: float
    potential_cpmp_with_alternative: float
    potential_savings: CPMPSavingsPotential
    message: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    role: str
    message: str


class ChatResponse(BaseModel):
    reply: str