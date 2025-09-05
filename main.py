from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import pickle
from app.routers import chatbot

# This path fix ensures the server can always find your modules.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import all model helper classes
from app.ml_models.regional_disparity_helper import RegionalDisparityModel
from app.ml_models.formulary_detail_helper import FormularyAnalyzer

from app.ml_models.um_change_analyzer_helper import UMFormularyChangesAnalyzer
from app.ml_models.therapeutic_eq_helper import PBMRecommender
from app.ml_models.drug_utilization_helper import DrugUtilizationForecaster

# Import the central model registry
from app.ml_models.registry import ml_models

# Import all routers
from app.routers import (
    auth,
    regional_disparity_analysis,
    formulary_detail_analysis,
    therapeutic_equivalence,
    um_change_router,
    drug_utilization_router,
    cpmp_analysis
)

from app import database

# Create DB tables if they don't exist
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CTS Project API")


@app.on_event("startup")
def startup_event():
    print("Application is starting up, loading ML models...")

    # --- Load Regional Disparity Model ---
    try:
        regional_model = RegionalDisparityModel.load_model("app/ml_models/models/regional_disparity_model_.pkl")
        ml_models["regional_disparity"] = regional_model
    except Exception as e:
        print(f"CRITICAL: Failed to load the Regional Disparity model. {e}")

    # --- Load Formulary Analyzer Model ---
    try:
        formulary_model = FormularyAnalyzer.load_model_state("app/ml_models/models/formulary_analyzer_model.pkl")
        ml_models["formulary_analyzer"] = formulary_model
    except Exception as e:
        print(f"CRITICAL: Failed to load the Formulary Analyzer model. {e}")

    try:
        with open("app/ml_models/models/th_eq.pkl", "rb") as f:
            model_data = pickle.load(f)
        th_eq_model = PBMRecommender(df=model_data)
        ml_models["therapeutic_equivalence"] = th_eq_model
    except FileNotFoundError:
        print("INFO: 'th_eq.pkl' data file not found. Please run the training script.")
    except Exception as e:
        print(f"CRITICAL: Failed to load the Therapeutic Equivalence model. Error: {e}")

    # --- Load Drug Utilization Model (Robust Method) ---
    try:
        with open("app/ml_models/models/drug_utilization_models.pkl", "rb") as f:
            bundle = pickle.load(f)
        utilization_model = DrugUtilizationForecaster(models_dict=bundle['models'], dataframe=bundle['dataframe'])
        ml_models["drug_utilization"] = utilization_model
        print("✅ Drug Utilization Forecast model loaded successfully.")
    except FileNotFoundError:
        print("INFO: 'drug_utilization_models.pkl' not found. Please run the training script.")
    except Exception as e:
        print(f"CRITICAL: Failed to load the Drug Utilization model. Error: {e}")

    # --- Load all UM Change Analyzer models ---
    um_comparisons = {
        "um_change_jun_to_jul": "um_analyzer_junetojuly.pkl",
        "um_change_jul_to_aug": "um_analyzer_julytoaugust.pkl",
        "um_change_jun_to_aug": "um_analyzer_junetoaugust.pkl",
    }
    for key, filename in um_comparisons.items():
        try:
            path = f"app/ml_models/models/{filename}"
            with open(path, "rb") as f:
                 ml_models[key] = pickle.load(f)
        except FileNotFoundError:
            print(f"INFO: UM Analyzer file not found, skipping: {filename}")
        except Exception as e:
            print(f"CRITICAL: Failed to load UM Analyzer '{filename}'. {e}")

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
app.include_router(regional_disparity_analysis.router, prefix="/api", tags=["Formulary_Impact"])
app.include_router(formulary_detail_analysis.router, prefix="/api", tags=["Formulary_Impact"])
app.include_router(therapeutic_equivalence.router, prefix="/api", tags=["Therapeutic Equivalence"])
app.include_router(um_change_router.router, prefix="/api", tags=["Formulary_Impact"])
app.include_router(drug_utilization_router.router, prefix="/api", tags=["Drug Utilization Forecast"])

app.include_router(chatbot.router, prefix="/api", tags=["chat"])

app.include_router(cpmp_analysis.router, prefix="/api", tags=["CPMP Analysis"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the CTS Project API"}

