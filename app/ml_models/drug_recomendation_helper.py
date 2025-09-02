import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle, gzip

class DrugRecommenderModel:

    def __init__(self, model: RandomForestClassifier, encoder: LabelEncoder, dataframe: pd.DataFrame):
        self.model = model
        self.encoder = encoder
        self.dataframe = dataframe



    @classmethod
    def load_model(cls, path: str):
        try:
            # Try normal pickle first
            with open(path, 'rb') as f:
                bundle = pickle.load(f)
        except Exception:
            # If it fails, assume gzip-compressed
            with gzip.open(path, 'rb') as f:
                bundle = pickle.load(f)

        return cls(bundle['model'], bundle['encoder'], bundle['dataframe'])

    def predict(self, rxcui: int, top_n: int = 2) -> dict:

        df = self.dataframe
        drug_df = df[df['RXCUI'] == rxcui]
        if drug_df.empty:
            return {"rxcui": rxcui, "alternatives": [], "message": "RXCUI not found in the eligible drug list"}

        tier = drug_df['TIER_LEVEL_VALUE'].iloc[0]
        cost = drug_df['BENEFICIARY_COST'].iloc[0]

        input_df = pd.DataFrame([{
            'RXCUI': rxcui, 'TIER_LEVEL_VALUE': tier, 'BENEFICIARY_COST': cost,
            'EXCLUDED': 0, 'STEP_THERAPY_YN': 0,
            'PRIOR_AUTHORIZATION_YN': 0, 'QUANTITY_LIMIT_YN': 0
        }])

        proba = self.model.predict_proba(input_df)[0]
        top_indices = proba.argsort()[-top_n:][::-1]
        predicted_ingredients = self.encoder.inverse_transform(top_indices)

        recommendations = [{"ingredient": ing} for ing in predicted_ingredients]

        return {"rxcui": rxcui, "alternatives": recommendations}
