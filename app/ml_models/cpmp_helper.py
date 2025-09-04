from .therapeutic_eq_helper import PBMRecommender

class CPMPCalculator:

    def __init__(self, recommender: PBMRecommender, member_count: int = 10000):
        if not isinstance(recommender, PBMRecommender):
            raise TypeError("recommender must be an instance of PBMRecommender")
        self.recommender = recommender
        self.member_count = member_count

    def analyze_savings_from_single_rxcui(self, rxcui: int, current_cost: float, utilization_rate: float):


        recommendation_result = self.recommender.recommend_by_rxcui(rxcui=rxcui, cost=current_cost)

        if not recommendation_result.get("alternatives"):

            return {
                "message": f"No cheaper therapeutic alternatives found for RXCUI {rxcui}.",
                "analysis_summary": {
                    "original_rxcui": rxcui,
                    "original_cost_per_member": current_cost,
                    "best_alternative_rxcui": 0,
                    "alternative_cost_per_member": current_cost,
                    "utilization_rate_analyzed": utilization_rate
                },
                "original_cpmp": current_cost * utilization_rate,
                "potential_cpmp_with_alternative": current_cost * utilization_rate,
                "potential_savings": {
                    "cpmp_reduction": 0,
                    "percentage_reduction": 0,
                    "total_annual_savings": 0
                }
            }


        best_alternative = min(recommendation_result["alternatives"], key=lambda x: x["Alternative_cost"])
        best_alternative_cost = best_alternative["Alternative_cost"]
        best_alternative_rxcui = best_alternative["Alternative_RXCUI"]

        original_cpmp = current_cost * utilization_rate
        original_total_annual_cost = original_cpmp * self.member_count * 12


        alternative_cpmp = best_alternative_cost * utilization_rate
        alternative_total_annual_cost = alternative_cpmp * self.member_count * 12

        cpmp_reduction = original_cpmp - alternative_cpmp
        total_annual_savings = original_total_annual_cost - alternative_total_annual_cost
        percentage_reduction = (cpmp_reduction / original_cpmp * 100) if original_cpmp > 0 else 0

        return {
            "analysis_summary": {
                "original_rxcui": rxcui,
                "original_cost_per_member": current_cost,
                "best_alternative_rxcui": best_alternative_rxcui,
                "alternative_cost_per_member": best_alternative_cost,
                "utilization_rate_analyzed": utilization_rate
            },
            "original_cpmp": original_cpmp,
            "potential_cpmp_with_alternative": alternative_cpmp,
            "potential_savings": {
                "cpmp_reduction": cpmp_reduction,
                "percentage_reduction": round(percentage_reduction, 2),
                "total_annual_savings": total_annual_savings
            }
        }

    def calculate_overall_cpmp(self, drug_list: list, utilization_rates: dict, cost_overrides: dict):
        pass