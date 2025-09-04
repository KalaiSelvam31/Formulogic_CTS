import pandas as pd
import pickle
import os
from statsmodels.tsa.arima.model import ARIMA
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# --- ADDED: Suppress specific, non-critical warnings from the ARIMA model ---
# This will make the output cleaner without hiding other potential issues.
warnings.filterwarnings("ignore", category=ConvergenceWarning)


# --- END OF ADDITION ---

def main():
    """
    Trains ARIMA models for drug utilization forecasting and saves the results
    and historical data into a self-contained pickle file. This script is
    independent of the main application's helper files.
    """
    print("--- Starting Drug Utilization Model Build Process ---")

    try:
        df = pd.read_csv("synthetic_drug_dataccc.csv")
    except FileNotFoundError:
        print("❌ ERROR: 'synthetic_drug_dataccc.csv' not found. Please place it in the project's root directory.")
        return

    print(f"Found {df['Gnrc_Name'].nunique()} unique drugs to model.")
    trained_models = {}

    for drug in df["Gnrc_Name"].unique():
        trained_models[drug] = {}
        drug_data = df[df["Gnrc_Name"] == drug].sort_values("Year")

        for target in ["Total_Claims", "Total_Beneficiaries"]:
            y = drug_data[target].values
            try:
                # Using a simple ARIMA(1,1,1) order as in the notebook
                model = ARIMA(y, order=(1, 1, 1))
                fitted = model.fit()
                trained_models[drug][target] = fitted
            except Exception as e:
                print(f"⚠️ ARIMA failed for {drug}-{target}: {e}. Skipping this model.")

    # Bundle the trained models and the historical data together into a dictionary
    model_bundle = {
        'models': trained_models,
        'dataframe': df
    }

    output_dir = "app/ml_models"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, "drug_utilization_models.pkl")

    with open(output_path, "wb") as f:
        pickle.dump(model_bundle, f)

    print(f"✅ {len(trained_models)} drug models built and saved to '{output_path}'")
    print("You can now start your FastAPI server.")


if __name__ == "__main__":
    main()

