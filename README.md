# Home Loan Application System

A goal-seeking, agentic AI system that automates and accelerates the home loan application process using **LangGraph** for agent orchestration, **Streamlit** for the user interface, and **AWS Bedrock** with **S3** for enhanced capabilities.

## 🏗️ System Architecture

The system consists of 6 specialized agents working in a coordinated workflow:

1. **Intake Agent** - Conversational bot to collect user intent and basic details (AWS Bedrock + S3)
2. **Document Validator Agent** - OCR + logic-based verification of PAN, ID, payslip, and property title
3. **Credit Score Agent** - Integrates with mock credit bureau to fetch and interpret score
4. **Property Valuation Agent** - Pulls data from a mock CoreLogic-style API
5. **Eligibility Agent** - Applies bank-specific lending rules (LTV, DTI, employment status)
6. **Approval Recommender Agent** - Suggests approve/reject/escalate with reasoning

## 🔄 Workflow

```
User Input → Intake Agent → Parallel Processing → Eligibility → Approval
                                    ↓
                    [Document Validator, Credit Score, Property Valuation]
```

1. **Intake Agent** collects user information via Streamlit chatbot with AWS Bedrock
2. **Document Validator**, **Credit Score**, and **Property Valuation** agents work in parallel
3. **Eligibility Agent** evaluates loan eligibility based on all results
4. **Approval Recommender Agent** provides final recommendation
5. **S3 Storage** securely stores completed applications

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with Bedrock and S3 access
- AWS credentials configured

### Installation

1. **Clone or download the project**
   ```bash
   # If you have git
   git clone <repository-url>
   cd home_loans
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials**
   ```bash
   # Option 1: AWS CLI
   aws configure
   
   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   
   # Option 3: AWS credentials file
   # ~/.aws/credentials
   ```

4. **Create S3 bucket** (if not exists)
   ```bash
   aws s3 mb s3://your-bucket-name
   ```

5. **Run the demo (no AWS required)**
   ```bash
   python demo.py
   ```

6. **Run the full application**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
home_loans/
├── app.py                          # Main Streamlit application (AWS Bedrock + S3)
├── demo.py                         # Demo script (no dependencies)
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── env_example.txt                 # Environment variables template
├── agents/                         # Agent implementations
│   ├── __init__.py
│   ├── intake_agent.py            # Conversational intake agent (AWS Bedrock + S3)
│   ├── document_validator_agent.py # Document validation
│   ├── credit_score_agent.py      # Credit score analysis
│   ├── property_valuation_agent.py # Property valuation
│   ├── eligibility_agent.py       # Eligibility assessment
│   └── approval_recommender_agent.py # Final recommendation
└── workflow/                       # Workflow orchestration
    ├── __init__.py
    └── orchestrator.py            # LangGraph workflow
```

## 🤖 Agent Details

### Intake Agent (Enhanced with AWS Bedrock + S3)
- **Purpose**: Collects comprehensive user information through natural conversation
- **Features**: 
  - AWS Bedrock integration for enhanced LLM capabilities
  - S3 storage for secure application data
  - Enhanced field validation and data extraction
  - Improved conversational flow with intent recognition
  - Progressive information gathering
  - Validation and confirmation

### Document Validator Agent
- **Purpose**: Validates uploaded documents using OCR and verification logic
- **Features**:
  - PAN card validation
  - ID proof verification
  - Payslip analysis
  - Property title verification
  - Fraud detection

### Credit Score Agent
- **Purpose**: Fetches and analyzes credit scores from multiple bureaus
- **Features**:
  - Multi-bureau credit score aggregation
  - Risk assessment
  - Payment history analysis
  - Credit utilization evaluation

### Property Valuation Agent
- **Purpose**: Determines property value using market data and comparable sales
- **Features**:
  - Comparable sales analysis
  - Market trend evaluation
  - Location-based adjustments
  - Multiple valuation methods

### Eligibility Agent
- **Purpose**: Applies lending rules and determines eligibility
- **Features**:
  - LTV (Loan-to-Value) ratio calculation
  - DTI (Debt-to-Income) ratio analysis
  - Employment verification
  - Risk scoring

### Approval Recommender Agent
- **Purpose**: Makes final approval decisions with reasoning
- **Features**:
  - Risk-based decision making
  - Conditional approval logic
  - Escalation criteria
  - Detailed reasoning

## 🔧 Configuration

The system is highly configurable through `config.py`:

- **Lending Rules**: LTV ratios, DTI limits, credit score requirements
- **Agent Settings**: Timeouts, confidence thresholds, retry attempts
- **AWS Configuration**: Bedrock model selection, S3 bucket settings
- **Workflow Settings**: Execution timeouts, parallel processing limits

## 📊 Demo Results

Running `python demo.py` shows a complete workflow:

```
🏠 Home Loan Application System - Demo
==================================================
✅ Intake process completed! Starting loan evaluation workflow...

🔄 Starting loan application workflow...

📋 Step 1: Running parallel agents...
   ✅ Document Validation: valid
   ✅ Credit Score: 702
   ✅ Property Valuation: ₹6,204,503.52

📋 Step 2: Evaluating eligibility...
   ✅ Eligibility Status: approved

📋 Step 3: Generating approval recommendation...
   ✅ Final Decision: APPROVE

==================================================
📋 FINAL LOAN APPLICATION RESULTS
==================================================
Decision: APPROVE
Loan Amount: ₹5,000,000.0
Interest Rate: 8.5%
Loan Tenure: 20 years
Decision Type: standard_approval

🆕 New Features:
• AWS Bedrock integration for enhanced LLM capabilities
• S3 storage for secure application data
• Enhanced field validation and data extraction
• Improved conversational flow with intent recognition
```

## 🎯 Key Features

- **AWS Bedrock Integration**: Enhanced LLM capabilities with Claude 3 Sonnet
- **S3 Storage**: Secure storage of application data in AWS S3
- **Conversational Interface**: Natural language interaction with the Intake Agent
- **Parallel Processing**: Multiple agents work simultaneously for efficiency
- **Comprehensive Validation**: Document, credit, and property verification
- **Risk Assessment**: Multi-factor risk analysis and scoring
- **Configurable Rules**: Flexible lending criteria and thresholds
- **Detailed Reporting**: Complete audit trail and reasoning

## 🔮 Future Enhancements

- **Real API Integration**: Connect to actual credit bureaus and property databases
- **Document Upload**: File upload and OCR processing
- **Multi-language Support**: Support for multiple languages
- **Advanced Analytics**: Machine learning for risk prediction
- **Mobile App**: Native mobile application
- **Integration APIs**: REST APIs for external system integration
- **AWS Lambda**: Serverless processing for scalability
- **DynamoDB**: NoSQL database for application tracking

## 🛠️ Development

### Adding New Agents

1. Create a new agent class in the `agents/` directory
2. Implement the required interface methods
3. Add the agent to the workflow orchestrator
4. Update configuration as needed

### Customizing Lending Rules

Edit the `LENDING_RULES` section in `config.py` to modify:
- Loan-to-value ratios
- Debt-to-income limits
- Credit score requirements
- Employment criteria
- Property requirements

### AWS Configuration

Configure AWS services in `config.py`:
- Bedrock model selection
- S3 bucket settings
- Region configuration
- IAM permissions

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues, please refer to the demo script or check the configuration files for guidance. 