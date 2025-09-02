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

class DrugRecommenderRequest(BaseModel):
    rxcui: int
    top_n: Optional[int] = 2

class AlternativeIngredient(BaseModel):
    ingredient: str

class DrugRecommenderResponse(BaseModel):
    rxcui: int
    alternatives: List[AlternativeIngredient]
    message: Optional[str] = None