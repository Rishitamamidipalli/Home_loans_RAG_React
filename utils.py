import streamlit as st
import os
import time
import boto3
from datetime import datetime
import re
from typing import Dict, Any, List
import json
from s3_manager import S3ApplicationManager
from chatbot import HomeLoanChatbot
from typing import Dict, List, Optional
try:
    from langchain_aws import ChatBedrock
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.chains import ConversationChain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    st.error("LangChain AWS not installed. Please run: pip install langchain-aws")
def clean_token(token: str) -> str:
    """Clean and standardize token format"""
    if not token:
        return ""
    return str(token).strip().upper()
# S3 Configuration
S3_BUCKET_NAME = "sarma-1"
S3_PREFIX = "customers_data/"

FORM_FIELDS = [
    {"name": "full_name", "type": "text", "label": "Full Name", "required": True},
    {"name": "date_of_birth", "type": "date", "label": "Date of Birth", "required": True, "min_date": datetime(1915, 1, 1), "max_date": datetime.now()},
    {"name": "gender", "type": "select", "label": "Gender", "options": ["Male", "Female", "Other"], "required": True},
    {"name": "email", "type": "text", "label": "Email Address", "required": True},
    {"name": "phone", "type": "text", "label": "Phone Number (10 digits)", "required": True},
    {"name": "aadhar_number", "type": "text", "label": "Aadhar Number (12 digits)", "required": True},
    {"name": "pan_number", "type": "text", "label": "PAN Number", "required": True},
    {"name": "address", "type": "textarea", "label": "Current Address", "required": True},
    {"name": "marital_status", "type": "select", "label": "Marital Status", 
     "options": ["Single", "Married", "Divorced", "Widowed"], "required": True},
    {"name": "employment_status", "type": "select", "label": "Employment Status", 
     "options": ["Salaried", "Self-Employed"], "required": True},
    {"name": "company_name", "type": "text", "label": "Company Name/ Business Name", 
     "required_if": {"field": "employment_status", "value": "Salaried"}},
    {"name": "gst_number", "type": "text", "label": "GST Number", 
     "required_if": {"field": "employment_status", "value": "Self-Employed"}},
    {"name": "monthly_income", "type": "number", "label": "Monthly Income (₹)", "required": True},
    {"name": "existing_loans", "type": "number", "label": "Number of Existing Loans", "required": False},
    {"name": "property_value", "type": "number", "label": "Estimated Property Value (₹)", "required": True},
    {"name": "loan_amount", "type": "number", "label": "Loan Amount Required (₹)", "required": True},
    {"name": "purpose_of_loan", "type": "select", "label": "Purpose of Loan", 
     "options": ["Buying a new house", "Renovating current house", "Constructing a house on current land"], "required": True},
    {"name": "property_location_city", "type": "text", "label": "Property City", "required": True},
    {"name": "property_location_area", "type": "text", "label": "Property Area/Neighborhood", "required": True},
    {"name": "property_type", "type": "select", "label": "Property Type", 
     "options": ["Apartment", "Villa", "Plot", "Independent House"], "required": True},
    {"name": "property_size_sqft", "type": "number", "label": "Property Size (sq ft)", "required": True, "min_value": 0},
    {"name": "property_age_years", "type": "number", "label": "Property Age (years, 0 for new)", "required": True, "min_value": 0},
    {"name": "property_condition", "type": "select", "label": "Property Condition", 
     "options": ["Excellent", "Good", "Average", "Poor"], "required": True},
]

# Sample questions for quick access
SAMPLE_QUESTIONS = [
    "What is the current home loan interest rate?",
    "What documents are required for home loan?",
    "What is the eligibility criteria for home loan?",
    "I want to apply for a home loan",
    "I want to update my existing application",
    "I want to cancel my application" 
]




        
def handle_cancellation_flow():
    st.subheader("❌ Cancel Application")
    
    token = st.text_input(
        "Enter your application token to cancel:",
        key="cancel_token_input",
        placeholder="e.g. HL123456789",
        help="Enter the token you received when you submitted your application"
    )
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔍 Verify and Cancel", key="verify_cancel_button"):
            if token:
                clean_token_val = clean_token(token)  # Changed this line
                if not clean_token_val:  # Add this validation
                    st.error("Please enter a valid token")
                    return
                    
                # Show loading while checking
                with st.spinner("Checking application..."):
                    app_data = st.session_state.chatbot.s3_manager.get_application(clean_token_val)
                    
                if app_data:
                    st.session_state.cancel_token = clean_token_val  # Changed this line
                    st.session_state.show_cancel_confirmation = True
                    st.success(f"✅ Application {clean_token_val} found!")
                    st.rerun()
                else:
                    st.error(f"❌ Application with token '{clean_token_val}' not found. Please check your token and try again.")
            else:
                st.error("Please enter a token")
    
    if st.session_state.get('show_cancel_confirmation'):
        st.warning(f"⚠️ Are you sure you want to permanently cancel application {token}?")
        confirm_col1, confirm_col2 = st.columns([1, 2])
        with confirm_col1:
            if st.button("✅ Yes, Cancel Permanently", key="confirm_cancel_button"):
                if st.session_state.chatbot.s3_manager.delete_application(token):
                    st.success(f"✅ Application {token} has been cancelled.")
                    if token in st.session_state.applications:
                        del st.session_state.applications[token]
                    st.session_state.show_cancel_button = False
                    st.session_state.show_cancel_confirmation = False
                    st.session_state.current_view = "chat"
                    st.rerun()
                else:
                    st.error("Failed to cancel application. Please try again.")
        with confirm_col2:
            if st.button("❌ No, Keep My Application", key="keep_application_button"):
                st.session_state.show_cancel_confirmation = False
                st.rerun()
    
    with col2:
        if st.button("← Back to Chat", key="cancel_flow_back_button"):
            st.session_state.show_cancel_button = False
            st.session_state.current_view = "chat"
            st.rerun()

def validate_field(field: Dict, value: Any) -> tuple[bool, str]:
    if field.get('required') and not value:
        return False, f"{field['label']} is required"
    
    if field['name'] == 'email' and value:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            return False, "Please enter a valid email address"
    
    if field['name'] == 'phone' and value:
        if not re.match(r'^\d{10}$', str(value)):
            return False, "Phone number must be exactly 10 digits"
    
    if field['name'] == 'aadhar_number' and value:
        if not re.match(r'^\d{12}$', str(value)):
            return False, "Aadhar number must be exactly 12 digits"
    
    if field['name'] == 'pan_number' and value:
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value.upper()):
            return False, "PAN number format should be like ABCDE1234F"
    if field['name'] == 'property_size_sqft' and value:
        if value <= 0:
            return False, "Property size must be greater than 0"
    if field['name'] == 'property_age_years' and value:
        if value < 0:
            return False, "Property age must be non-negative"
    
    return True, ""

def generate_token() -> str:
    timestamp = int(time.time() * 1000)
    return f"HL{timestamp}"

def render_form_field(field: Dict, value: Any = None, employment_status: str = None):
    key = f"form_{field['name']}"
    
    if 'required_if' in field:
        required_field = field['required_if']['field']
        required_value = field['required_if']['value']
        if required_field == 'employment_status' and employment_status != required_value:
            return None
    
    if field['type'] == 'text':
        return st.text_input(field['label'], value=value or "", key=key)
    elif field['type'] == 'textarea':
        return st.text_area(field['label'], value=value or "", key=key)
    elif field['type'] == 'number':
        return st.number_input(field['label'], min_value=0,max_value=100000000,step=1000, value=int(value) if value else 10, key=key)
    elif field['type'] == 'date':
        min_date = field.get('min_date', datetime(1900, 1, 1))
        max_date = field.get('max_date', datetime.now())
        return st.date_input(
            field['label'],
            value=value,
            min_value=min_date,
            max_value=max_date,
            key=f"form_{field['name']}"
        )
    elif field['type'] == 'select':
        index = 0
        if value and value in field['options']:
            index = field['options'].index(value)
        return st.selectbox(field['label'], field['options'], index=index, key=key)
