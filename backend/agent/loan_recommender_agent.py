# agents/loan_recommender_agent.py
import json
import boto3
from typing import List, Dict

def loan_recommender_node(state: dict) -> dict:
    """LangGraph node for loan recommendation using Claude"""
    data = state.get("applicant_data")
    if not data:
        state["error"] = "Missing applicant_data in state"
        return state

    income = data.get("monthly_income")
    property_value = data.get("property_value")
    loan_amount = data.get("loan_amount")
    credit_score = data.get("credit_score", 700)  # Default to 700 if not provided
    
    # Check for high-income but low credit score scenario
    high_income_low_credit = False
    if credit_score < 600 and income > 200000:  # Example threshold for high income
        high_income_low_credit = True

    prompt = f"""
You are a smart home loan advisor. The user has requested a loan of ₹{loan_amount}, 
for a property worth ₹{property_value}. Their monthly income is ₹{income}.
Credit score: {credit_score}. srictly calculate EMI based on given formula below.

Bank rules:
- Max Loan-to-Value (LTV): 70%
- EMI must be <30% of monthly income
- Minimum credit score: 700 (except for special high-income cases)
- **Calculate EMI using the formula: EMI = (P * r * (1 + r)^n) / ((1 + r)^n - 1)
where P is the loan amount, r is the monthly interest rate (annual rate / 12), and n is the number of months.**


Task:
1. Calculate maximum eligible loan amount based on LTV rules
2. Generate 3 loan options with different tenures and interest rates
3. For applicants with credit score <600 but high income (>₹200k/month), 
   provide a special high-interest loan option they can afford
4. Format response with:
   - Brief explanation of the applicant's situation (2-3 lines before table)
   - Markdown table with columns: 
     Loan Option | Loan Amount | Interest Rate | Tenure (years) | Monthly EMI | Eligibility
   - Follow-up explanation of why these offers were made (5-6 lines after table)

Example format:
**Current Scenario Analysis:**
Based on your requested loan of ₹X against a property worth ₹Y, with monthly income ₹Z and credit score ABC, we note [key observations about eligibility]. The maximum LTV-eligible amount is ₹P, and your maximum affordable EMI is ₹Q.

[Table would go here]

**Offer Rationale:**
These options were created because [explain main factors]. The [specific option] was included due to [reason]. We recommend [suggestion] because [benefit to applicant].

Current scenario:
- Requested amount: ₹{loan_amount}
- Property value: ₹{property_value}
- Monthly income: ₹{income}
- Credit score: {credit_score}
{'NOTE: Applicant has high income but low credit score - considering special approval' if high_income_low_credit else ''}

Provide your recommendations with explanations before and after the table:
"""

    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    try:
        response = client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3  # Lower temperature for more structured output
            })
        )
        recommendation = json.loads(response['body'].read().decode())["content"][0]["text"]
        
        # Store both raw text and parsed recommendations
        state["loan_recommendation"] = {
            "text": recommendation.strip(),
            "table": extract_loan_options(recommendation)  # Parse table into structured data
        }
    except Exception as e:
        state["error"] = f"Claude API error: {str(e)}"

    return state

def extract_loan_options(markdown_text: str) -> List[Dict]:
    """Helper function to parse markdown table into structured data"""
    # This is a simplified parser - you may need to enhance it based on actual Claude output
    options = []
    lines = [line.strip() for line in markdown_text.split('\n') if line.strip()]
    
    # Find the table rows (skip header and separator lines)
    for line in lines:
        if line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Split and remove empty parts
            if len(parts) >= 6:  # Ensure we have all columns
                options.append({
                    "option": parts[0],
                    "loan_amount": parts[1],
                    "interest_rate": parts[2],
                    "tenure": parts[3],
                    "monthly_emi": parts[4],
                    "eligibility": parts[5]
                })
    
    return options