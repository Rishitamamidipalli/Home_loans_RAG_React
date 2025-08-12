from typing import Dict, Tuple

class Applicant:
    def __init__(self, data: Dict):
        self.name = data.get("full_name")
        self.income = data.get("monthly_income", 10000)
        self.loan_amount = data.get("loan_amount", 0)
        self.property_value = data.get("property_value", 10000000)
        self.credit_score = data.get("credit_score", 720)  # Default if not provided
        self.employment_status = data.get("employment_status")
        self.existing_debt = data.get("existing_loans", 0)

class EligibilityAgent:
    def __init__(self, rules: Dict = None):
        self.rules = rules or {
            "max_ltv": 0.7,
            "min_credit_score": 700,
            "allowed_employment": ["salaried", "self-employed"],
            "max_dti": 0.5,
            "min_income": 15000,
        }

    def calculate_ltv(self, applicant: Applicant) -> float:
        """Calculate Loan-to-Value ratio"""
        return applicant.loan_amount / applicant.property_value

    def calculate_dti(self, applicant: Applicant) -> float:
        """Calculate Debt-to-Income ratio"""
        return applicant.existing_debt / applicant.income

    def check_eligibility(self, applicant: Applicant) -> Tuple[bool, Dict[str, bool]]:
        """Run all eligibility checks"""
        ltv_check = 'Yes' if self.calculate_ltv(applicant) <= self.rules["max_ltv"] else 'No'
        credit_score_check = 'Yes' if applicant.credit_score >= self.rules["min_credit_score"] else 'No'
        income_check = 'Yes' if applicant.income >= self.rules["min_income"] else 'No'
        employment_check = applicant.employment_status.lower() in self.rules["allowed_employment"]
        dti_check = 'Yes' if self.calculate_dti(applicant) <= self.rules["max_dti"] else 'No'

        checks = {
            "ltv_check": ltv_check,
            "credit_score_check": credit_score_check,
            "income_check": income_check,
            "employment_check": employment_check,
            "dti_check": dti_check
        }

        return all(checks.values()), checks

def eligibility_node(state: dict) -> dict:
    """LangGraph node for eligibility check"""
    applicant_data = state.get("applicant_data")
    if not applicant_data:
        state["error"] = "Missing applicant_data"
        return state

    applicant = Applicant(applicant_data)
    agent = EligibilityAgent()
    is_eligible, checks = agent.check_eligibility(applicant)

    state.update({
        "eligibility_result": is_eligible,
        "eligibility_checks": checks,
        "applicant_name": applicant.name
    })
    return state