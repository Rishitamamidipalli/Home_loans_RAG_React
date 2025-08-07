import os
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
import time
import random
import requests

class CreditScoreAgent:
    def __init__(self):
        # self.llm = ChatAnthropic(
        #     model="claude-3-sonnet-20240229",
        #     api_key=os.getenv("ANTHROPIC_API_KEY")
        # )
        
        # Mock credit bureau API endpoints
        self.credit_bureau_apis = {
            "cibil": "https://api.cibil.com/v1/credit-score",
            "experian": "https://api.experian.com/v1/credit-report",
            "equifax": "https://api.equifax.in/v1/credit-score"
        }
        
        # Credit score interpretation rules
        self.score_ranges = {
            "excellent": (750, 900),
            "good": (650, 749),
            "fair": (550, 649),
            "poor": (300, 549)
        }
        
        # Risk assessment criteria
        self.risk_factors = {
            "payment_history": 0.35,
            "credit_utilization": 0.30,
            "credit_history_length": 0.15,
            "credit_mix": 0.10,
            "new_credit": 0.10
        }
    
    def get_credit_score(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch and analyze credit score from credit bureaus
        In a real implementation, this would:
        1. Integrate with actual credit bureau APIs
        2. Handle authentication and authorization
        3. Process credit reports from multiple bureaus
        4. Apply advanced credit scoring algorithms
        """
        
        print("📊 Credit Score Agent: Fetching credit information...")
        
        # Simulate API call delay
        time.sleep(1.5)
        
        # Extract required information
        pan_number = application_data.get("pan_number", "")
        full_name = application_data.get("full_name", "")
        phone = application_data.get("phone", "")
        
        if not pan_number:
            return {
                "status": "error",
                "message": "PAN number required for credit score check",
                "credit_score": None,
                "risk_assessment": None
            }
        
        # Simulate credit bureau API calls
        credit_reports = self._fetch_credit_reports(pan_number, full_name, phone)
        
        # Analyze and interpret credit scores
        analysis_result = self._analyze_credit_score(credit_reports, application_data)
        
        print(f"✅ Credit Score Agent: Credit analysis completed. Score: {analysis_result.get('credit_score', 'N/A')}")
        
        return analysis_result
    
    def _fetch_credit_reports(self, pan_number: str, full_name: str, phone: str) -> Dict[str, Any]:
        """Simulate fetching credit reports from multiple bureaus"""
        
        # Mock credit bureau responses
        mock_reports = {
            "cibil": {
                "status": "success",
                "credit_score": random.randint(600, 850),
                "report_date": "2024-01-15",
                "payment_history": {
                    "total_accounts": random.randint(3, 8),
                    "accounts_in_good_standing": random.randint(2, 7),
                    "late_payments_30_days": random.randint(0, 2),
                    "late_payments_60_days": random.randint(0, 1),
                    "late_payments_90_days": random.randint(0, 1)
                },
                "credit_utilization": random.uniform(0.15, 0.75),
                "credit_history_length": random.randint(2, 15),
                "credit_mix": ["credit_card", "personal_loan", "home_loan"],
                "recent_inquiries": random.randint(0, 5)
            },
            "experian": {
                "status": "success",
                "credit_score": random.randint(580, 830),
                "report_date": "2024-01-15",
                "payment_history": {
                    "total_accounts": random.randint(2, 6),
                    "accounts_in_good_standing": random.randint(1, 5),
                    "late_payments_30_days": random.randint(0, 3),
                    "late_payments_60_days": random.randint(0, 2),
                    "late_payments_90_days": random.randint(0, 1)
                },
                "credit_utilization": random.uniform(0.20, 0.80),
                "credit_history_length": random.randint(1, 12),
                "credit_mix": ["credit_card", "auto_loan"],
                "recent_inquiries": random.randint(0, 4)
            },
            "equifax": {
                "status": "success",
                "credit_score": random.randint(590, 840),
                "report_date": "2024-01-15",
                "payment_history": {
                    "total_accounts": random.randint(2, 7),
                    "accounts_in_good_standing": random.randint(1, 6),
                    "late_payments_30_days": random.randint(0, 2),
                    "late_payments_60_days": random.randint(0, 1),
                    "late_payments_90_days": random.randint(0, 1)
                },
                "credit_utilization": random.uniform(0.18, 0.70),
                "credit_history_length": random.randint(1, 14),
                "credit_mix": ["credit_card", "personal_loan"],
                "recent_inquiries": random.randint(0, 3)
            }
        }
        
        # Simulate API failures
        if random.random() < 0.1:  # 10% chance of API failure
            mock_reports["experian"]["status"] = "error"
            mock_reports["experian"]["message"] = "Service temporarily unavailable"
        
        return mock_reports
    
    def _analyze_credit_score(self, credit_reports: Dict[str, Any], application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and interpret credit scores from multiple bureaus"""
        
        # Calculate average credit score
        valid_scores = []
        for bureau, report in credit_reports.items():
            if report.get("status") == "success" and report.get("credit_score"):
                valid_scores.append(report["credit_score"])
        
        if not valid_scores:
            return {
                "status": "error",
                "message": "No valid credit scores available",
                "credit_score": None,
                "risk_assessment": None
            }
        
        average_score = sum(valid_scores) / len(valid_scores)
        
        # Determine credit score category
        score_category = self._categorize_credit_score(average_score)
        
        # Perform risk assessment
        risk_assessment = self._assess_credit_risk(credit_reports, application_data)
        
        # Generate recommendations
        recommendations = self._generate_credit_recommendations(average_score, risk_assessment)
        
        return {
            "status": "completed",
            "credit_score": round(average_score, 0),
            "score_category": score_category,
            "bureau_reports": credit_reports,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "confidence_score": 0.95,
            "analysis_date": "2024-01-15"
        }
    
    def _categorize_credit_score(self, score: float) -> str:
        """Categorize credit score into risk levels"""
        if score >= 750:
            return "excellent"
        elif score >= 650:
            return "good"
        elif score >= 550:
            return "fair"
        else:
            return "poor"
    
    def _assess_credit_risk(self, credit_reports: Dict[str, Any], application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall credit risk based on multiple factors"""
        
        risk_score = 0
        risk_factors = []
        
        # Analyze payment history
        for bureau, report in credit_reports.items():
            if report.get("status") == "success":
                payment_history = report.get("payment_history", {})
                
                # Check late payments
                late_payments_30 = payment_history.get("late_payments_30_days", 0)
                late_payments_60 = payment_history.get("late_payments_60_days", 0)
                late_payments_90 = payment_history.get("late_payments_90_days", 0)
                
                if late_payments_90 > 0:
                    risk_score += 0.4
                    risk_factors.append("90+ day late payments")
                elif late_payments_60 > 0:
                    risk_score += 0.3
                    risk_factors.append("60+ day late payments")
                elif late_payments_30 > 0:
                    risk_score += 0.2
                    risk_factors.append("30+ day late payments")
                
                # Check credit utilization
                utilization = report.get("credit_utilization", 0)
                if utilization > 0.7:
                    risk_score += 0.3
                    risk_factors.append("High credit utilization")
                elif utilization > 0.5:
                    risk_score += 0.1
                    risk_factors.append("Moderate credit utilization")
                
                # Check recent inquiries
                inquiries = report.get("recent_inquiries", 0)
                if inquiries > 3:
                    risk_score += 0.2
                    risk_factors.append("Multiple recent credit inquiries")
        
        # Assess risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "risk_mitigation_suggestions": self._get_risk_mitigation_suggestions(risk_factors)
        }
    
    def _get_risk_mitigation_suggestions(self, risk_factors: List[str]) -> List[str]:
        """Generate suggestions to mitigate identified risk factors"""
        suggestions = []
        
        for factor in risk_factors:
            if "late payments" in factor:
                suggestions.append("Improve payment history by making timely payments")
            elif "credit utilization" in factor:
                suggestions.append("Reduce credit card balances to lower utilization ratio")
            elif "recent inquiries" in factor:
                suggestions.append("Avoid applying for new credit in the next 6 months")
        
        return suggestions
    
    def _generate_credit_recommendations(self, credit_score: float, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on credit score and risk assessment"""
        recommendations = []
        
        if credit_score < 650:
            recommendations.append("Consider improving credit score before applying for large loans")
            recommendations.append("Focus on reducing outstanding debt and making timely payments")
        
        if risk_assessment["risk_level"] == "high":
            recommendations.append("High risk profile - consider smaller loan amounts or co-applicant")
            recommendations.append("Address risk factors before proceeding with loan application")
        
        if credit_score >= 750:
            recommendations.append("Excellent credit score - eligible for best interest rates")
            recommendations.append("Consider negotiating for better loan terms")
        
        return recommendations
    
    def _call_credit_bureau_api(self, bureau: str, pan_number: str, api_key: str) -> Dict[str, Any]:
        """Simulate actual credit bureau API call"""
        # In a real implementation, this would make actual HTTP requests
        # to credit bureau APIs with proper authentication
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "pan_number": pan_number,
            "request_type": "credit_score",
            "consent": True
        }
        
        # Mock API response
        return {
            "status": "success",
            "data": {
                "credit_score": random.randint(600, 850),
                "report_date": "2024-01-15"
            }
        } 