from typing import Optional, List, Dict, Literal

from pydantic import BaseModel, Field,EmailStr


class UserLogin(BaseModel):
    username: str
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