from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys

# Import your model classes
from app.ml_models.regional_disparity_helper import RegionalDisparityModel
from app.ml_models.formulary_detail_helper import FormularyAnalyzer

from app.ml_models.drug_recomendation_helper import DrugRecommenderModel
from app.ml_models.registry import ml_models

# Import your routers
from app.routers import auth, regional_disparity_analysis, formulary_detail_analysis
# Corrected import for the new router
from app.routers import therapeutic_equivalence

from app import database

# Create DB tables if they don't exist
database.Base.metadata.create_all(bind=database.engine)


app = FastAPI(title="CTS Project API")

@app.on_event("startup")
def startup_event():
    print("Application is starting up, loading ML models...")
    try:
        regional_model = RegionalDisparityModel.load_model(
            "app/ml_models/regional_disparity_model_.pkl"
        )
        ml_models["regional_disparity"] = regional_model
    except Exception as e:
        print(f"CRITICAL: Failed to load the Regional Disparity model. {e}")
        # sys.exit(1) # It's better to let it run to see other errors if any

    try:
        formulary_model = FormularyAnalyzer.load_model_state(
            "app/ml_models/formulary_analyzer_model.pkl"
        )
        ml_models["formulary_analyzer"] = formulary_model
    except Exception as e:
        print(f"CRITICAL: Failed to load the Formulary Analyzer model. {e}")
        # sys.exit(1)

    # --- NEW MODEL LOADING ---
    try:
        drug_model = DrugRecommenderModel.load_model(
            "app/ml_models/drug_recommender_model.pkl"
        )
        ml_models["drug_recommender"] = drug_model
    except Exception as e:
        print(f"CRITICAL: Failed to load the Drug Recommender model. {e}")
        # sys.exit(1)

    print(f"Successfully loaded models: {list(ml_models.keys())}")


# --- Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routers ---
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(regional_disparity_analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(formulary_detail_analysis.router, prefix="/api", tags=["Analysis"])
# ADD THE NEW ROUTER with correct variable name
app.include_router(therapeutic_equivalence.router, prefix="/api", tags=["Analysis"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the CTS Project API"}
