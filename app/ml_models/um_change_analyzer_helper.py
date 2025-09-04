# um_change_analyzer_helper.py

import pandas as pd
import pickle
from typing import Dict, List, Any


class UMFormularyChangesAnalyzer:

    def __init__(self):
        self.monthly_analyses = {}
        self.current_analysis_key = None

    # --- Public Methods for API Access ---

    def set_current_analysis_by_key(self, key: str) -> bool:
        """Sets the active analysis based on the key from the loaded .pkl file."""
        if key in self.monthly_analyses:
            self.current_analysis_key = key
            return True
        print(f"Warning: Analysis key '{key}' not found in loaded data.")
        self.current_analysis_key = None
        return False

    def _get_active_analysis(self) -> Dict[str, Any]:
        """Helper to safely get the currently active analysis dictionary."""
        if not self.current_analysis_key:
            return None
        return self.monthly_analyses.get(self.current_analysis_key)

    # --- NEW CONSOLIDATED METHOD ---
    def get_consolidated_insights(self) -> Dict[str, Any]:
        """
        Combines key insights, top drugs, and recommendations into a single object
        perfect for a UI dashboard card.
        """
        analysis = self._get_active_analysis()
        if not analysis:
            return {"error": "No active analysis set"}

        # Fetch the raw insights and recommendations
        key_insights_data = analysis.get("analysis_result", {}).get("key_insights", {})
        insights_list = key_insights_data.get("insights", [])
        recommendations_list = key_insights_data.get("recommendations", [])

        # Fetch the top 5 most impacted drugs by combining additions and removals
        additions = self._get_detailed_table_by_type('DRUG_ADDED', 3)
        removals = self._get_detailed_table_by_type('DRUG_REMOVED', 3)
        top_affected_drugs = additions.get("changes", []) + removals.get("changes", [])

        # Structure the final output to match the UI mockup
        response = {
            "insights": insights_list,
            "recommendations": recommendations_list,
            "top_affected_drugs": top_affected_drugs
        }

        return response

    def get_key_insights(self) -> Dict[str, Any]:
        analysis = self._get_active_analysis()
        return analysis.get("analysis_result", {}).get("key_insights",
                                                       {"error": "Insights not available"}) if analysis else {
            "error": "No active analysis set"}

    def get_trend_analysis(self) -> Dict[str, Any]:
        analysis = self._get_active_analysis()
        return analysis.get("analysis_result", {}).get("trend_analysis",
                                                       {"error": "Trends not available"}) if analysis else {
            "error": "No active analysis set"}

    def get_impact_analysis(self) -> Dict[str, Any]:
        analysis = self._get_active_analysis()
        return analysis.get("analysis_result", {}).get("impact_analysis",
                                                       {"error": "Impact analysis not available"}) if analysis else {
            "error": "No active analysis set"}

    def get_changes_overview(self) -> Dict[str, Any]:
        analysis = self._get_active_analysis()
        return analysis.get("analysis_result", {}).get("changes_overview",
                                                       {"error": "Overview not available"}) if analysis else {
            "error": "No active analysis set"}

    def get_detailed_changes_prior_auth(self, limit: int = 15):
        return self._get_detailed_table_by_type('pa_change', limit)

    def get_detailed_changes_step_therapy(self, limit: int = 15):
        return self._get_detailed_table_by_type('st_change', limit)

    def get_detailed_changes_quantity_limit(self, limit: int = 15):
        return self._get_detailed_table_by_type('ql_change', limit)

    def get_detailed_changes_drug_additions(self, limit: int = 15):
        return self._get_detailed_table_by_type('DRUG_ADDED', limit)

    def get_detailed_changes_drug_removals(self, limit: int = 15):
        return self._get_detailed_table_by_type('DRUG_REMOVED', limit)

    def _get_detailed_table_by_type(self, change_key: str, limit: int):
        analysis = self._get_active_analysis()
        if not analysis:
            return {"error": "No active analysis set", "total_changes": 0, "displayed_changes": 0, "changes": []}

        all_changes = analysis.get("changes", [])

        if change_key in ['DRUG_ADDED', 'DRUG_REMOVED']:
            filtered_changes = [c for c in all_changes if c.get('change_type') == change_key]
        else:
            filtered_changes = [c for c in all_changes if change_key in c]

        table = self._generate_detailed_changes_table(filtered_changes[:limit])
        return {
            "total_changes": len(filtered_changes),
            "displayed_changes": len(table),
            "changes": table
        }

    # --- Helper methods for formatting API responses (copied from notebook) ---
    def _generate_detailed_changes_table(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        detailed_changes = []
        for change in changes:
            detail = {
                "rxcui": change.get('rxcui'), "formulary_id": change.get('formulary_id'),
                "change_type": self._get_change_type_description(change),
                "previous_value": self._get_previous_value(change), "new_value": self._get_new_value(change),
                "impact": self._get_impact_label(change),
                "tier_previous": self._handle_nan_values(change.get('tier_previous')),
                "tier_current": self._handle_nan_values(change.get('tier_current'))
            }
            detailed_changes.append(detail)
        return detailed_changes

    def _handle_nan_values(self, value):
        return "N/A" if pd.isna(value) else value

    def _get_impact(self, change: Dict[str, Any]) -> str:
        if change.get('change_type') == 'DRUG_ADDED': return "LESS_RESTRICTIVE"
        if change.get('change_type') == 'DRUG_REMOVED': return "MORE_RESTRICTIVE"
        if 'pa_change' in change: return "MORE_RESTRICTIVE" if change['pa_change'][
                                                                   'type'] == 'PA_ADDED' else "LESS_RESTRICTIVE"
        if 'st_change' in change: return "MORE_RESTRICTIVE" if change['st_change'][
                                                                   'type'] == 'ST_ADDED' else "LESS_RESTRICTIVE"
        if 'ql_change' in change: return "MORE_RESTRICTIVE" if change['ql_change'][
                                                                   'type'] == 'QL_ADDED' else "LESS_RESTRICTIVE"
        return "NEUTRAL"

    def _get_impact_label(self, change: Dict[str, Any]) -> str:
        impact = self._get_impact(change)
        if impact == "MORE_RESTRICTIVE": return "🔴 More restrictive"
        if impact == "LESS_RESTRICTIVE": return "🟢 Less restrictive"
        return "🟡 Neutral"

    def _get_change_type_description(self, change: Dict[str, Any]) -> str:
        if change.get('change_type') == 'DRUG_ADDED': return "Drug Added to Formulary"
        if change.get('change_type') == 'DRUG_REMOVED': return "Drug Removed from Formulary"
        if 'pa_change' in change: return "Prior Auth " + change['pa_change']['type'].replace('PA_', '').title()
        if 'st_change' in change: return "Step Therapy " + change['st_change']['type'].replace('ST_', '').title()
        if 'ql_change' in change: return "Quantity Limit " + change['ql_change']['type'].replace('QL_', '').title()
        return "Unknown Change"

    def _get_previous_value(self, change: Dict[str, Any]) -> str:
        if change.get('change_type') == 'DRUG_REMOVED': return "Was in Formulary"
        if change.get('change_type') == 'DRUG_ADDED': return "Not in Formulary"
        return "N/A"

    def _get_new_value(self, change: Dict[str, Any]) -> str:
        if change.get('change_type') == 'DRUG_ADDED': return "Added to Formulary"
        if change.get('change_type') == 'DRUG_REMOVED': return "Removed from Formulary"
        return "N/A"

    @classmethod
    def load_from_pickle(cls, filename: str):
        """Load an analyzer object from a pickle file."""
        with open(filename, 'rb') as f:
            analyzer = pickle.load(f)
        print(f"✅ Analyzer loaded from {filename}")
        return analyzer