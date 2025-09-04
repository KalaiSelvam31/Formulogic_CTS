import pandas as pd
import pickle


class PBMRecommender:
    """
    The runtime class for the Therapeutic Equivalence recommender.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Ensure the RXCUI column is numeric to prevent type mismatch errors during lookup.
        self.df['RXCUI'] = pd.to_numeric(self.df['RXCUI'], errors='coerce')

    @classmethod
    def load_model(cls, path: str):
        """Loads the recommender instance from a pickle file."""
        with open(path, 'rb') as f:
            return pickle.load(f)

    def recommend_by_rxcui(self, rxcui: int, cost: float, top_n: int = 2):
        """
        Finds cheaper alternatives for a given RXCUI and cost.
        """
        if rxcui not in self.df['RXCUI'].values:
            return {"rxcui": rxcui, "message": "Invalid RXCUI"}

        drug_df = self.df[self.df['RXCUI'] == rxcui]
        if drug_df.empty:
            return {"rxcui": rxcui, "message": "RXCUI not found in dataset."}

        cost = float(cost)
        input_ing_series = drug_df['ingredient'].dropna()
        if input_ing_series.empty:
            return {"rxcui": rxcui, "message": "Ingredient for the given RXCUI could not be found."}
        input_ing = input_ing_series.iloc[0]

        candidates = self.df[self.df['ingredient'] == input_ing].copy()
        candidates = candidates.sort_values(
            by=['TIER_LEVEL_VALUE', 'BENEFICIARY_COST'],
            ascending=[True, True]
        )

        recommendations = []
        seen_costs = set()

        for _, cand in candidates.iterrows():
            alt_rxcui = int(cand['RXCUI'])
            alt_cost = float(cand['BENEFICIARY_COST'])

            if alt_rxcui == rxcui and alt_cost == cost:
                continue
            if alt_cost in seen_costs:
                continue
            seen_costs.add(alt_cost)

            cost_diff = cost - alt_cost
            percent_reduction = (cost_diff / cost) * 100 if cost != 0 else 0

            if cost_diff > 0:
                # --- CRITICAL FIX: Changed dictionary keys to match Pydantic schema ---
                # Removed spaces from keys (e.g., "Alternative RXCUI" -> "Alternative_RXCUI")
                recommendations.append({
                    "Ingredient": input_ing,
                    "Alternative_RXCUI": alt_rxcui,
                    "Alternative_cost": alt_cost,
                    "Cost_difference": round(cost_diff, 2),
                    "Percentage_reduction": f"{round(percent_reduction, 2)}%"
                })
                # --- END OF FIX ---

            if len(recommendations) >= top_n:
                break

        return {
            "input_rxcui": int(rxcui),
            "input_cost": cost,
            "ingredient": input_ing,
            "alternatives": recommendations if recommendations else []
        }

