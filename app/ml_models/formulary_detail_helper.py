import pandas as pd
import pickle, gzip


class FormularyAnalyzer:

    def __init__(self):
        self.formulary_df = None
        self.plan_info_df = None
        self.beneficiary_cost_df = None
        self.geographic_df = None
        self.indication_df = None
        self.excluded_drugs_df = None
        self.is_trained = False



    @classmethod
    def load_model_state(cls, filepath: str):
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
        except Exception:
            with gzip.open(filepath, 'rb') as f:
                state = pickle.load(f)

        model = cls()
        model.__dict__.update(state)
        print(f"Model loaded and rebuilt from {filepath}")
        return model

    def predict(self, rxcui_input):

        if not self.is_trained:
            return {'status': 'error', 'message': 'Model is not trained or the .pkl file is invalid.'}

        try:
            rxcui_input = str(rxcui_input)
            drug_info = self.formulary_df[self.formulary_df['RXCUI'] == rxcui_input]
            if drug_info.empty:
                return {'drug_rxcui': rxcui_input, 'status': 'not_covered',
                        'message': 'Drug not covered in any formulary'}

            if not self.excluded_drugs_df[self.excluded_drugs_df['RXCUI'] == rxcui_input].empty:
                return {'drug_rxcui': rxcui_input, 'status': 'excluded',
                        'message': 'Drug explicitly excluded from coverage'}

            formulary_id = drug_info['FORMULARY_ID'].iloc[0]
            tier = drug_info['TIER_LEVEL_VALUE'].iloc[0]

            plan_info = self.plan_info_df[self.plan_info_df['FORMULARY_ID'] == formulary_id]
            if plan_info.empty:
                return {'drug_rxcui': rxcui_input, 'status': 'covered_no_info',
                        'message': 'Covered but no plan information available'}

            selected_plan = plan_info.iloc[0]
            plan_name = selected_plan['PLAN_NAME']
            contract_id = selected_plan['CONTRACT_ID']
            plan_id = selected_plan['PLAN_ID']
            county_code = selected_plan['COUNTY_CODE']

            state = "Unknown"
            if pd.notna(county_code):
                geo_info = self.geographic_df[self.geographic_df['COUNTY_CODE'] == county_code]
                if not geo_info.empty:
                    state = geo_info['STATENAME'].iloc[0]

            prior_auth = "Yes" if drug_info['PRIOR_AUTHORIZATION_YN'].iloc[0] == 'Y' else "No"
            step_therapy = "Yes" if drug_info['STEP_THERAPY_YN'].iloc[0] == 'Y' else "No"

            quantity_limit = ""
            qty_yn = drug_info['QUANTITY_LIMIT_YN'].iloc[0]
            if pd.notna(qty_yn) and qty_yn == 'Y':
                qty_amount = drug_info['QUANTITY_LIMIT_AMOUNT'].iloc[0]
                qty_days = drug_info['QUANTITY_LIMIT_DAYS'].iloc[0]
                if pd.notna(qty_amount) and pd.notna(qty_days):
                    quantity_limit = f"{qty_amount} per {qty_days} days"

            restrictions = f"Prior Auth = {prior_auth}, Step Therapy = {step_therapy}"
            if quantity_limit:
                restrictions += f", Quantity limit = {quantity_limit}"

            indications = self.indication_df[self.indication_df['RXCUI'] == rxcui_input]['DISEASE'].unique()
            indications_str = ", ".join([str(ind) for ind in indications if pd.notna(ind)]) or "Not specified"

            cost_info = self.beneficiary_cost_df[(self.beneficiary_cost_df['CONTRACT_ID'] == contract_id) & (
                        self.beneficiary_cost_df['PLAN_ID'] == plan_id) & (self.beneficiary_cost_df['TIER'] == tier)]
            pref_cost, nonpref_cost = "0", "0"
            if not cost_info.empty:
                thirty_day_cost = cost_info[cost_info['DAYS_SUPPLY'] == '1']
                if not thirty_day_cost.empty:
                    pref_cost = thirty_day_cost['COST_AMT_PREF'].iloc[0] or "0"
                    nonpref_cost = thirty_day_cost['COST_AMT_NONPREF'].iloc[0] or "0"

            return {
                "drug_rxcui": rxcui_input, "status": "covered", "plan_name": plan_name,
                "tier": tier, "restrictions": restrictions, "indications": indications_str,
                "patient_cost": {"preferred": str(pref_cost), "non_preferred": str(nonpref_cost)},
                "geography": {"state": state,
                              "county_code": str(county_code) if pd.notna(county_code) else "not_available"}
            }
        except Exception as e:
            return {"drug_rxcui": rxcui_input, "status": "error", "message": f"Analysis error: {str(e)}"}



