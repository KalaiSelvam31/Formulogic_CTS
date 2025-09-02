import pickle, gzip


class RegionalDisparityModel:


    def __init__(self):
        self.formulary_df = None
        self.plan_info_df = None
        self.beneficiary_cost_df = None
        self.geographic_df = None
        self.indication_df = None
        self.excluded_drugs_df = None
        self.all_states = None
        self.is_trained = False

    def load_data(self):

        pass



    @classmethod
    def load_model(cls, filepath='regional_disparity_model.pkl'):
        """Rebuild class from saved state"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
        except Exception:
            with gzip.open(filepath, 'rb') as f:
                state = pickle.load(f)

        model = cls()
        model.__dict__.update(state)
        print(f"Model loaded from {filepath}")
        return model

    def predict(self, rxcui_input):

        if not self.is_trained:
            return {
                'rxcui': rxcui_input,
                'status': 'error',
                'message': 'Model not trained. The loaded .pkl file might be invalid.'
            }

        try:
            rxcui_input = str(rxcui_input)

            drug_coverage = self.formulary_df[self.formulary_df['RXCUI'] == rxcui_input]

            if drug_coverage.empty:
                return {
                    'rxcui': rxcui_input,
                    'status': 'not_covered',
                    'message': 'Drug not covered in any formulary',
                    'missing_states': self.all_states if self.all_states is not None else []
                }

            covering_formulary_ids = drug_coverage['FORMULARY_ID'].unique()
            covering_plans = self.plan_info_df[self.plan_info_df['FORMULARY_ID'].isin(covering_formulary_ids)]

            if covering_plans.empty:
                return {
                    'rxcui': rxcui_input,
                    'status': 'no_active_plans',
                    'message': 'Drug in formularies but no active plans',
                    'missing_states': self.all_states if self.all_states is not None else []
                }

            covering_plans_with_geo = covering_plans.merge(
                self.geographic_df, on='COUNTY_CODE', how='left'
            )

            covering_plans_with_geo.dropna(subset=['STATENAME'], inplace=True)

            coverage_by_state = covering_plans_with_geo.groupby('STATENAME').agg(
                PLAN_COUNT=('PLAN_NAME', 'count')
            ).reset_index()

            drug_details = drug_coverage.iloc[0]
            tier = drug_details.get('TIER_LEVEL_VALUE', 'N/A')
            prior_auth = "Yes" if drug_details.get('PRIOR_AUTHORIZATION_YN') == 'Y' else "No"
            step_therapy = "Yes" if drug_details.get('STEP_THERAPY_YN') == 'Y' else "No"

            states_with_coverage = coverage_by_state['STATENAME'].tolist()
            states_without_coverage = [s for s in self.all_states if s not in states_with_coverage]

            total_covering_states = len(states_with_coverage)
            total_states = len(self.all_states)
            total_plans = covering_plans.shape[0]

            coverage_ratio = (total_covering_states / total_states) if total_states > 0 else 0
            coverage_gap_percentage = round((1.0 - coverage_ratio) * 100, 1)

            return {
                'rxcui': rxcui_input,
                'total_plans_covering_drug': int(total_plans),
                'states_with_coverage': f"{total_covering_states}/{total_states}",
                'coverage_gap_percentage': f"{coverage_gap_percentage}%",
                'drug_tier': tier,
                'prior_auth_required': prior_auth,
                'step_therapy_required': step_therapy,
                'missing_states': states_without_coverage,
                'disparity_message': (
                    f"Regional disparities detected - not covered in {len(states_without_coverage)} states/territories"
                    if states_without_coverage else "No regional disparities - covered in all states/territories"
                ),
                'status': 'success'
            }

        except Exception as e:
            return {
                'rxcui': rxcui_input,
                'status': 'error',
                'message': f"Analysis error: {str(e)}"
            }

    def save_model(self, filepath='regional_disparity_model.pkl'):


        pass



