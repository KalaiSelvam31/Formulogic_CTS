import pandas as pd
import pickle


class DrugUtilizationForecaster:
    """
    Handles loading the pre-trained ARIMA models from the model bundle
    and generating forecasts for drug utilization.
    """

    def __init__(self, models_dict: dict, dataframe: pd.DataFrame):
        self.models = models_dict
        self.df = dataframe

    @classmethod
    def load_model(cls, path: str):
        """Loads the model bundle (models and dataframe) from a pickle file."""
        with open(path, 'rb') as f:
            bundle = pickle.load(f)
        return cls(bundle['models'], bundle['dataframe'])

    def forecast_drug(self, drug_name: str, steps: int = 5):
        """
        Generates a forecast for a specific drug for a given number of steps (years).
        """
        if drug_name not in self.models:
            return {"error": f"No model found for '{drug_name}'"}

        hist = self.df[self.df["Gnrc_Name"] == drug_name].sort_values("Year")
        if hist.empty:
            return {"error": f"No historical data found for '{drug_name}'"}

        last_year = hist["Year"].max()
        future_years = list(range(last_year + 1, last_year + 1 + steps))

        forecast_data = {}
        for target in ["Total_Claims", "Total_Beneficiaries"]:
            if target in self.models.get(drug_name, {}):
                fitted_model = self.models[drug_name][target]
                forecast = fitted_model.forecast(steps=steps)
                # Convert numpy types to native Python integers for JSON serialization
                forecast_data[target] = [int(x) for x in forecast]
            else:
                forecast_data[target] = []  # Return empty list if a model for a target failed to train

        response = {
            "drug": drug_name,
            "forecast_years": future_years,
            "historical": {
                "years": hist["Year"].tolist(),
                "Total_Claims": hist["Total_Claims"].astype(int).tolist(),
                "Total_Beneficiaries": hist["Total_Beneficiaries"].astype(int).tolist()
            },
            "forecast": forecast_data
        }

        return response

