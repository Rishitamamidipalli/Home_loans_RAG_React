import streamlit as st
import os
import time
import boto3
from datetime import datetime
import re
from typing import Dict, Any, List
import json
from s3_manager import S3ApplicationManager
from orchestration_agent import HomeLoanOrchestrator
from chatbot import HomeLoanChatbot
from utils import * 
from graphviz import Digraph
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
LANGCHAIN_AVAILABLE = True

# Configure page
st.set_page_config(
    page_title="Home Loan Assistant",
    layout="wide"
)
def clean_token(token: str) -> str:
    """Clean and standardize token format"""
    if not token:
        return ""
    return str(token).strip().upper()
# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": "Hello! I'm your Home Loan Assistant. I can help you with information about home loans, eligibility, interest rates, and more. How can I assist you today?"
    }]
if 'applications' not in st.session_state:
    st.session_state.applications = {}
if 'current_view' not in st.session_state:
    st.session_state.current_view = "chat"
if 'show_form_button' not in st.session_state:
    st.session_state.show_form_button = False
if 'show_update_button' not in st.session_state:
    st.session_state.show_update_button = False
if 'show_cancel_button' not in st.session_state:
    st.session_state.show_cancel_button = False
if 'show_cancel_confirmation' not in st.session_state:
    st.session_state.show_cancel_confirmation = False
if 'show_upload_button' not in st.session_state:
    st.session_state.show_upload_button = False

# S3 Configuration
S3_BUCKET_NAME = "sarma-1"
S3_PREFIX = "customers_data/"

#Running the orchestration agent
def run_orchestrator_workflow(form_data: dict, document_paths: dict):
    """Run the full loan processing workflow"""
    with st.spinner("Processing your application..."):
        # Prepare the applicant_data structure
        applicant_data = {
            "applicant_name": form_data.get("full_name"),
            "loan_amount": float(form_data.get("loan_amount", 0)),
            "monthly_income": float(form_data.get("monthly_income", 0)),
            "employment_status": form_data.get("employment_status"),
            "company_name": form_data.get("company_name"),
            "property_value":  form_data.get("property_value"),
            "property_details": {
                "size_sqft": float(form_data.get("property_size_sqft", 0)),
                "property_type": form_data.get("property_type"),
                "city": form_data.get("property_location_city"),
                "area": form_data.get("property_location_area"),
                "age_years": int(form_data.get("property_age_years", 0)),
                "condition": form_data.get("property_condition"),
                "amenities": []  # Add if collected
            },
            "pan_number": form_data.get("pan_number"),
            "aadhar_number": form_data.get("aadhar_number")
        }
        
        # Initialize and run orchestrator
        orchestrator = HomeLoanOrchestrator()
        
        try:
            result = orchestrator.run_workflow(applicant_data, document_paths)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "errors": [str(e)]
            }

# Form field definitions
def render_application_form(edit_mode=False, existing_data=None):
    st.subheader("🏠 Home Loan Application" + (" - Edit Mode" if edit_mode else ""))
    
    # Initialize form data in session state if not exists
    if 'form_data' not in st.session_state:
        st.session_state.form_data = existing_data if existing_data else {}
    col1,back_col = st.columns([5,1])
    with back_col:
        if st.button("← Back to Chat", key="edit_form_back_button"):
            if 'form_data' in st.session_state:
                del st.session_state.form_data
            st.session_state.current_view = "chat"
            if hasattr(st.session_state, 'edit_token'):
                del st.session_state.edit_token
            st.session_state.show_form_button = False
            st.session_state.show_update_button = False
            st.rerun()
    
    # Add Back to Chat button at the top in edit mode
    
    with st.form("home_loan_form", clear_on_submit=False):  # Changed to prevent auto-clear
        form_data = {}
        validation_errors = []
        
        st.markdown("### Personal Information")
        col1, col2 = st.columns(2)

        with col1:
            form_data['full_name'] = render_form_field(
                FORM_FIELDS[0], st.session_state.form_data.get('full_name')
            )
            form_data['gender'] = render_form_field(
                FORM_FIELDS[2], st.session_state.form_data.get('gender')
            )
            form_data['phone'] = render_form_field(
                FORM_FIELDS[4], st.session_state.form_data.get('phone')
            )
            form_data['pan_number'] = render_form_field(
                FORM_FIELDS[6], st.session_state.form_data.get('pan_number')
            )

        with col2:
            form_data['date_of_birth'] = render_form_field(
                FORM_FIELDS[1], st.session_state.form_data.get('date_of_birth')
            )
            form_data['email'] = render_form_field(
                FORM_FIELDS[3], st.session_state.form_data.get('email')
            )
            form_data['aadhar_number'] = render_form_field(
                FORM_FIELDS[5], st.session_state.form_data.get('aadhar_number')
            )
            form_data['marital_status'] = render_form_field(
                FORM_FIELDS[8], st.session_state.form_data.get('marital_status')
            )

        # New row for loan-related fields before address
        col1_loans, col2_purpose = st.columns(2)
        with col1_loans:
            form_data['existing_loans'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'existing_loans'),
                st.session_state.form_data.get('existing_loans')
            )
        with col2_purpose:
            form_data['purpose_of_loan'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'purpose_of_loan'),
                st.session_state.form_data.get('purpose_of_loan')
            )

        # Address field
        form_data['address'] = render_form_field(
            FORM_FIELDS[7], st.session_state.form_data.get('address')
        )

        st.markdown("### Employment Information")
        col1, col2, col3 = st.columns(3)

        with col1:
            form_data['employment_status'] = render_form_field(
                FORM_FIELDS[9], st.session_state.form_data.get('employment_status')
            )
        with col2:
            form_data['monthly_income'] = render_form_field(
                FORM_FIELDS[12], st.session_state.form_data.get('monthly_income')
            )
        with col3:
            if form_data['employment_status'] == 'Salaried':
                form_data['company_name'] = render_form_field(
                    FORM_FIELDS[10], st.session_state.form_data.get('company_name'),
                    form_data['employment_status']
                )
            elif form_data['employment_status'] == 'Self-Employed':
                form_data['gst_number'] = render_form_field(
                    FORM_FIELDS[11], st.session_state.form_data.get('gst_number'),
                    form_data['employment_status']
                )

        st.markdown("### Property Information")
        col1, col2 = st.columns(2)

        with col1:
            form_data['property_location_city'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_location_city'),
                st.session_state.form_data.get('property_location_city')
            )
            form_data['property_location_area'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_location_area'),
                st.session_state.form_data.get('property_location_area')
            )
            form_data['property_type'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_type'),
                st.session_state.form_data.get('property_type')
            )
            form_data['property_size_sqft'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_size_sqft'),
                st.session_state.form_data.get('property_size_sqft')
            )

        with col2:
            form_data['property_age_years'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_age_years'),
                st.session_state.form_data.get('property_age_years')
            )
            form_data['property_condition'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_condition'),
                st.session_state.form_data.get('property_condition')
            )
            form_data['property_value'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'property_value'),
                st.session_state.form_data.get('property_value')
            )
            form_data['loan_amount'] = render_form_field(
                next(f for f in FORM_FIELDS if f['name'] == 'loan_amount'),
                st.session_state.form_data.get('loan_amount')
            )
        
        # Create columns for buttons
        col1, col2 = st.columns([1, 3])
        
        with col1:
            submitted = st.form_submit_button("Update Application" if edit_mode else "Submit Application")
        
        if submitted:
            validation_errors = []  # Reset validation errors for each submission
            
            # Perform validation
            for field in FORM_FIELDS:
                field_name = field['name']
                field_value = form_data.get(field_name)
                
                if 'required_if' in field:
                    required_field = field['required_if']['field']
                    required_value = field['required_if']['value']
                    if form_data.get(required_field) != required_value:
                        continue
                
                is_valid, error_msg = validate_field(field, field_value)
                if not is_valid:
                    validation_errors.append(error_msg)
            
            if validation_errors:
                # Save current form data to session state
                st.session_state.form_data = form_data
                # Display all validation errors
                for error in validation_errors:
                    st.error(error)
                # Stop further execution
                st.stop()
            else:
                # Process successful submission
                chatbot = st.session_state.get('chatbot')
                if not chatbot or not hasattr(chatbot, 's3_manager'):
                    st.error("Application manager not available. Please try again.")
                    st.stop()
                        
                if edit_mode and hasattr(st.session_state, 'edit_token'):
                    token = st.session_state.edit_token
                    if chatbot.s3_manager.update_application(token, form_data):
                        st.session_state.applications[token].update(form_data)
                        st.session_state.applications[token]['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.success(f"✅ Application {token} updated successfully!")
                        # Clear form data from session state
                        if 'form_data' in st.session_state:
                            del st.session_state.form_data
                        del st.session_state.edit_token
                        st.session_state.current_view = "chat"
                        st.session_state.show_form_button = False
                        st.session_state.show_update_button = False
                    else:
                        st.error("Failed to update application in S3. Please try again.")
                else:
                    token = generate_token()
                    form_data['token'] = token
                    form_data['submission_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if chatbot.s3_manager.save_application(token, form_data):
                        st.session_state.applications[token] = form_data
                        st.success(f"✅ Application submitted successfully! with token {token}")
                        st.info("Save this token to check status or edit your application later.")
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"Your home loan application has been submitted with token {token}. You can use this token to check status or make edits."
                            f"To proceed further we need you to upload some documents "
                        })
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": "What would you like to do next?"
                        })
                        
                        st.session_state.current_view = "document_upload"
                        st.session_state.upload_token = token
                        st.session_state.show_upload_button = True
                        
                        st.session_state.current_token = token
                        # Clear form data from session state
                        if 'form_data' in st.session_state:
                            del st.session_state.form_data
                        st.session_state.current_view = "chat"
                        st.session_state.show_form_button = False
                        st.session_state.show_update_button = False
                    else:
                        st.error("Failed to save application to S3. Please try again.")
                
                st.rerun()
        
        # Add cancel button outside the form submission
        if edit_mode:
            with col2:
                if st.form_submit_button("Cancel", type="secondary"):
                    # Clear form data from session state
                    if 'form_data' in st.session_state:
                        del st.session_state.form_data
                    st.session_state.current_view = "chat"
                    if hasattr(st.session_state, 'edit_token'):
                        del st.session_state.edit_token
                    st.session_state.show_form_button = False
                    st.session_state.show_update_button = False
                    st.rerun()
def render_document_upload(token: str, s3_manager: S3ApplicationManager):
    # Add back to chat button at top
    if st.button("← Back to Chat", key="back_to_chat_top"):
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"Your application {token} is not yet submitted. You may upload additional documents or update your documents later if needed. Note your application token {token} for future reference."
        })
        st.session_state.current_view = "chat"
        st.rerun()
    
    st.subheader(f"📁 Document Upload for Application {token}")
    
    REQUIRED_DOCS = {
        "PAN": {
            "description": "PAN Card (Front)",
            "types": ["jpg", "png", "pdf"]
        },
        "Aadhaar": {
            "description": "Aadhaar Card (Front + Back)",
            "types": ["jpg", "png", "pdf"]
        },
        "CompanyID": {
            "description": "Company ID Card/Letter",
            "types": ["jpg", "png", "pdf"]
        },
        "Payslip": {
            "description": "Latest Payslip (3 months)",
            "types": ["pdf","png", "jpg"]
        }
    }
    
    uploaded_files = {
    doc['name'].split('.')[0]: doc['s3_path']
    for doc in (s3_manager.list_documents(token) or [])
}
    uploaded_list = s3_manager.list_documents(token) or []
    

    for doc_type, config in REQUIRED_DOCS.items():
        st.markdown(f"### {doc_type}")
        st.caption(config["description"])
        
        uploaded_file = st.file_uploader(
            f"Upload {doc_type}",
            type=config["types"],
            key=f"upload_{doc_type}"
        )
        
        if uploaded_file:
            try:
                # Delete all files from uploaded_list containing doc_type in their name (any extension)
                for item in uploaded_list:
                    filename = item.get("name", "")
                    if filename.lower().startswith(doc_type.lower()): 
                        actual_filename = token + "_" + filename    
                        s3_manager.delete_document(token, actual_filename)
                        st.warning(f"Deleted previous file: {filename}")
                        if doc_type in uploaded_files:
                            del uploaded_files[doc_type]

                # Upload new file to S3
                print(token,uploaded_file,doc_type)
                print("token:",token,"uploaded_file:",uploaded_file,"doc_type:",doc_type)
                s3_path = s3_manager.upload_document(token, uploaded_file, doc_type)
                uploaded_files[doc_type] = s3_path
                st.success(f"{doc_type} uploaded successfully to: {s3_path}")

            except Exception as e:
                st.error(f"Failed to upload {doc_type}: {str(e)}")
    
    # Display uploaded documents
    st.divider()
    st.subheader("Uploaded Documents")
    progress_value = min(len(uploaded_list) / len(REQUIRED_DOCS), 1.0)
    st.progress(progress_value, text=f"Upload progress: {len(uploaded_list)} of {len(REQUIRED_DOCS)} documents uploaded")
    
    if uploaded_list:
        for doc in uploaded_list:
            doc_name = doc['name'].split('_')[-1].split('.')[0]
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- **{doc_name}** ({doc['size']/1024:.1f} KB)")
            with col2:
                if st.button("Delete", key=f"del_{doc['name']}"):
                    actual_file_name = token + "_" + doc['name']
                    s3_manager.delete_document(token, actual_file_name)
                    
    else:
        st.warning("No documents uploaded yet")
    
    # Process Application Button
    if st.button("✅ Process My Application", type="primary"):
        if len(uploaded_list) < len(REQUIRED_DOCS):
            st.error("Please upload all required documents first")
            return
            
        form_data = s3_manager.get_application(token)
        if not form_data:
            st.error("Application data not found!")
            return
        
        # Use the exact S3 paths we got from upload_document()
        print(form_data)
        result = run_orchestrator_workflow(form_data, uploaded_files)
        st.session_state.workflow_result = result
        st.session_state.current_view = "results"
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"All documents for application {token} have been uploaded successfully and results are displaed to you!."})
        st.rerun()
    
    if st.button("← Back to Application"):
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"Your application {token} is not yet submitted. You may upload additional documents or update your documents later if needed. Note your application token {token} for future reference."
        })
        st.session_state.current_view = "chat"
        st.rerun()

def render_chat_interface():
    if LANGCHAIN_AVAILABLE:
        region_name = "us-east-1"
        try:
            sts_client = boto3.client('sts', region_name=region_name)
            identity = sts_client.get_caller_identity()
            
            s3 = boto3.client('s3', region_name=region_name)
            s3.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
        except Exception as e:
            st.error(f"❌ AWS Credentials Error: {str(e)}")
    else:
        st.error("LangChain AWS not available")
        region_name = "us-east-1"

    try:
        if LANGCHAIN_AVAILABLE and ('chatbot' not in st.session_state or st.session_state.get('current_region') != region_name):
            st.session_state.chatbot = HomeLoanChatbot(region_name=region_name)
            st.session_state.current_region = region_name
        elif not LANGCHAIN_AVAILABLE:
            st.session_state.chatbot = HomeLoanChatbot()
        
        chatbot = st.session_state.chatbot
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {str(e)}")
        return
    
    if LANGCHAIN_AVAILABLE:
        if not chatbot.llm:
            st.warning(f"⚠️ Chatbot unavailable - using fallback responses")
    else:
        st.info("ℹ️ Using fallback responses - install langchain-aws for Bedrock")
    
    st.markdown("Quick Questions:")
    cols = st.columns(3)
    
    for i, question in enumerate(SAMPLE_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"sample_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Thinking..."):
                    response = chatbot.get_response(question, st.session_state.chat_history)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
  
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Display post-submission buttons if they exist
    if 'post_submission_buttons' in st.session_state and st.session_state.post_submission_buttons:
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button(st.session_state.post_submission_buttons[0]["label"]):
                st.session_state.current_view = "document_upload"
                st.session_state.upload_token = st.session_state.current_token
                st.session_state.current_token = st.session_state.current_token  # Ensure current_token is set
                st.rerun()
        with col2:
            if st.button(st.session_state.post_submission_buttons[1]["label"]):
                del st.session_state.post_submission_buttons
                st.rerun()
    
    if st.session_state.show_form_button:
        # Create columns for side-by-side buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📝 Apply for Home Loan", 
                        use_container_width=True, 
                        key="apply_button"):  # Stable key
                st.session_state.current_view = "application_form"
                st.rerun()
        with col2:
            if st.button("← Back to Chat", 
                        use_container_width=True, 
                        key="back_button"):  # Stable key
                st.session_state.show_form_button = False
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Would you like to ask something else about home loans?"
                })
                st.rerun()
    if st.session_state.get("show_existing_customer_question", False):
        st.write("Are you an existing customer?")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Yes, I have an existing application",use_container_width=True):
                st.session_state.is_existing_customer = True
                st.session_state.show_existing_customer_question = False
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "I'm an existing customer"
                })
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "I see you are a exixting customer.Please provide your application token number (format: HL followed by 13 digits) so I can assist you further."
                })
                
                #st.session_state.show_upload_button = True
                st.rerun()
        with col2:
            if st.button("No, I'm a new customer",use_container_width=True):
                st.session_state.is_existing_customer = False
                st.session_state.show_existing_customer_question = False

                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "I'm a new customer"
                })

                st.session_state.show_form_button= True
                st.rerun()
    if st.session_state.show_update_button:
        token_input = st.text_input(
            "Application token:", 
            key="update_token_input_field",
            placeholder="e.g. HL123456789",
            help="Enter the token you received when you submitted your application"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔍 Find Application", use_container_width=True, key="find_app_button"):
                if token_input:
                    clean_token_val = clean_token(token_input)  # Use clean_token function
                    if not clean_token_val:
                        st.error("Please enter a valid token")
                    else:
                        with st.spinner("Searching for application..."):
                            app_data = st.session_state.chatbot.s3_manager.get_application(clean_token_val)
                            
                        if app_data:
                            st.session_state.applications[clean_token_val] = app_data
                            st.session_state.edit_token = clean_token_val
                            st.session_state.current_view = "edit_form"
                            st.session_state.show_update_button = False
                            st.success(f"✅ Application {clean_token_val} found!")
                            st.rerun()
                        else:
                            st.error(f"❌ Application with token '{clean_token_val}' not found. Please check your token and try again.")
                else:
                    st.error("Please enter a token")
                    
        with col2:
            if st.button("❌ Cancel", use_container_width=True, key="cancel_update_button"):
                st.session_state.show_update_button = False
                st.rerun()
    
    if st.session_state.show_upload_button:
        st.info("Please enter your application token to upload documents")
        token_input = st.text_input(
            "Application Token:",
            key="upload_token_input_field",
            placeholder="e.g.HL1234567890123",
            help="Enter the token you received when you submitted your application"
        )

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("📤 Proceed to Document Upload", use_container_width=True):
                if token_input:
                    clean_token_val = clean_token(token_input)  # Use clean_token function
                    if not clean_token_val:
                        st.error("Please enter a valid token")
                    else:
                        st.session_state.current_view = "document_upload"
                        st.session_state.upload_token = clean_token_val
                        st.rerun()
        with col2:
            if st.button("← Back to Chat", use_container_width=True):
                st.session_state.show_upload_button = False
                st.rerun()
                
    if prompt := st.chat_input("Ask me about home loans or use your application token..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        try:
            with st.spinner("Thinking..."):
                response = chatbot.get_response(prompt, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.write(response)
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}. Please try again."
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.error(error_msg)
        
        st.rerun()
def render_results():
    # Set page config (if not already set elsewhere)
    st.set_page_config(layout="wide", page_title="Loan Application Results")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .card {
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .success-card {
            background-color: #e8f5e9;
            border-left: 5px solid #4caf50;
        }
        .warning-card {
            background-color: #fff8e1;
            border-left: 5px solid #ffc107;
        }
        .error-card {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
        }
        .info-card {
            background-color: #e3f2fd;
            border-left: 5px solid #2196f3;
        }
        .metric-card {
            padding: 15px;
            border-radius: 8px;
            background-color: #f5f5f5;
        }
        .stProgress > div > div > div > div {
            background-color: #4caf50;
        }
        .st-eb {
            padding: 0px;
        }
        .tab-content {
            padding: 15px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    if 'workflow_result' not in st.session_state:
        st.error("No results available")
        if st.button("← Back to Application"):
            st.session_state.current_view = "chat"
            st.rerun()
        return
    
    result = st.session_state.workflow_result
    results = result.get("results", {})
    doc_result = results.get("document_validation", {})
    credit_result = results.get("credit_score", {})
    prop_result = results.get("property_valuation", {})
    elig_result = results.get("eligibility", {})
    rec_result = results.get("approval_recommendation", {})

    # Main header with status
    st.title("📊 Loan Application Dashboard")
    
    # Overall application status card
    overall_status = "Pending"
    status_color = "#FFC107"
    if elig_result.get("is_eligible", False):
        overall_status = "Approved"
        status_color = "#4CAF50"
    elif elig_result.get("is_eligible", False) is False:
        overall_status = "Rejected"
        status_color = "#F44336"
    token = st.session_state.get('upload_token', '')
    clean_token_val = clean_token(token)
    s3_manager = S3ApplicationManager()
    app_data = s3_manager.get_application(clean_token_val)
    st.markdown(f"""
    <div class="card" style="border-left: 5px solid {status_color};">
        <h3 style="margin-top:0;">Application Status: <span style="color:{status_color};">{overall_status}</span></h3>
        <div style="display: flex; justify-content: space-between;">
            <div>
                <p><strong>Application ID:</strong> {st.session_state.get('upload_token', 'N/A')}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            </div>
            <div>
                <p><strong>Applicant:</strong> {app_data.get('full_name', 'N/A')}</p>
                <p><strong>Loan Amount:</strong> ₹{app_data.get('loan_amount', 0):,}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin:0; color:#2196F3;">Credit Score</h4>
            <h2 style="margin:0;">{credit_result.get('credit_score', 'N/A')}</h2>
            <p style="margin:0; font-size:12px;">{credit_result.get('score_category', '')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin:0; color:#4CAF50;">Property Value</h4>
            <h2 style="margin:0;">₹{prop_result.get('estimated_property_value', 0):,}</h2>
            <p style="margin:0; font-size:12px;">{prop_result.get('price_per_sqft', 0):,}/sq.ft</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        max_eligible = float(rec_result["recommendation"].split("maximum LTV-eligible loan amount is ₹")[1].split(" ")[0].replace(",",""))
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin:0; color:#9C27B0;">Loan Eligibility</h4>
            <h2 style="margin:0;">₹{max_eligible:,.2f}</h2>
            <p style="margin:0; font-size:12px;">Max amount</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin:0; color:#FF9800;">Risk Level</h4>
            <h2 style="margin:0;">{elig_result.get('risk_level', 'Medium')}</h2>
            <p style="margin:0; font-size:12px;">Based on profile</p>
        </div>
        """, unsafe_allow_html=True)

    # Results navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Application Overview", 
        "📄 Documents", 
        "🏠 Property", 
        "💳 Credit", 
        "✅ Recommendations"
    ])
        
    with tab1:
        st.subheader("Application Summary")
        
        # Progress tracker
        st.markdown("### 📌 Application Progress")
        steps = ["Document Verification", "Credit Check", "Property Valuation", "Eligibility", "Approval"]
        current_step = 4 if overall_status == "Approved" else 3
        st.progress(current_step/4)
        
        cols = st.columns(5)
        for i, step in enumerate(steps):
            with cols[i]:
                if i <= current_step:
                    st.success(f"✓ {step}")
                else:
                    st.info(step)
        # Quick stats
        st.subheader("📊 Quick Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
    
            with st.expander("📝 Application Details", expanded=True):
                token = st.session_state.get('upload_token', '')
                clean_token_val = clean_token(token)
                s3_manager = S3ApplicationManager()
                app_data = s3_manager.get_application(clean_token_val)
                st.write(f"**Loan Amount Requested:** ₹{app_data.get('loan_amount', 0):,}")
                st.write(f"**Loan Purpose:** {app_data.get('purpose_of_loan', 'N/A')}")
                st.write(f"**Employment Type:** {app_data.get('employment_status', 'N/A')}")
                st.write(f"**Monthly Income:** ₹{app_data.get('monthly_income', 0):,}")
        
        with col2:
            with st.expander("🔍 Eligibility Summary", expanded=True):
                st.write(f"**Eligibility Status:** {'✅ Eligible' if elig_result.get('is_eligible') else '❌ Not Eligible'}")
                max_eligible = float(rec_result["recommendation"].split("maximum LTV-eligible loan amount is ₹")[1].split(" ")[0].replace(",",""))
                st.write(f"**Maximum Eligible Amount:** ₹{max_eligible:,.2f}")
                recommended_amount = float(rec_result["table"][2]["loan_amount"].replace("₹","").replace(",",""))
                st.write(f"**Recommended Loan Amount:** ₹{recommended_amount:,.2f}")
                st.write(f"**Risk Assessment:** {credit_result['risk_assessment']['risk_level'].title()} (Score: {credit_result['risk_assessment']['risk_score']})")

    with tab2:
        st.subheader("Document Verification")
        
        if not doc_result:
            st.warning("No document validation results available")
        else:
            # Document cards
            doc_types = {
                "PAN": {"icon": "🆔", "title": "PAN Card"},
                "Aadhaar": {"icon": "🆔", "title": "Aadhaar Card"},
                "Payslip": {"icon": "💰", "title": "Salary Slip"},
                "CompanyID": {"icon": "🏢", "title": "Employment Proof"}
            }
            
            for doc_type, doc_meta in doc_types.items():
                doc_data = doc_result.get("raw_data", {}).get(doc_type, {})
                if doc_data:
                    status = "✅ Verified" if doc_data.get("is_valid", True) else "❌ Issues Found"
                    card_class = "success-card" if doc_data.get("is_valid", True) else "error-card"
                    
                    with st.expander(f"{doc_meta['icon']} {doc_meta['title']} - {status}", expanded=False):
                        st.markdown(f"""
                        <div class="card {card_class}">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <p><strong>Status:</strong> {status}</p>
                                    <p><strong>Name:</strong> {doc_data.get('name', 'N/A')}</p>
                                </div>
                                <div>
                                    <p><strong>Validity:</strong> {'Valid' if doc_data.get('is_valid', True) else 'Invalid'}</p>
                                    {f"<p><strong>Date of Birth:</strong> {doc_data.get('date_of_birth', 'N/A')}</p>" if doc_type in ["PAN", "Aadhaar"] else "<p></p>"}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show validation details if available
                        if "validation_notes" in doc_data:
                            st.markdown("**Validation Notes:**")
                            st.info(doc_data["validation_notes"])

    with tab3:
        st.subheader("Property Valuation")
        
        if not prop_result:
            st.warning("No property valuation results available")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="card info-card">
                    <h3 style="margin-top:0;">🏡 Property Details</h3>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <p><strong>Location:</strong> {}</p>
                            <p><strong>Type:</strong> {}</p>
                        </div>
                        <div>
                            <p><strong>Size:</strong> {} sq.ft</p>
                            <p><strong>Age:</strong> {} years</p>
                        </div>
                    </div>
                </div>
                """.format(
                    f"{prop_result.get('property_data', {}).get('city', 'N/A')}, {prop_result.get('property_data', {}).get('area', 'N/A')}",
                    prop_result.get('property_data', {}).get('property_type', 'N/A'),
                    prop_result.get('property_data', {}).get('size_sqft', 'N/A'),
                    prop_result.get('property_data', {}).get('age_years', 'N/A')
                ), unsafe_allow_html=True)
                
                st.markdown("""
                <div class="card" style="margin-top:20px;">
                    <h3 style="margin-top:0;">📊 Valuation Method</h3>
                    <p><strong>Approach:</strong> {}</p>
                    <p><strong>Confidence:</strong> {:.0f}%</p>
                    <p><strong>Market Comparison:</strong> {}</p>
                </div>
                """.format(
                    prop_result.get('valuation_method', 'Automated Valuation Model (AVM)'),
                    prop_result.get('confidence_score', 0) * 100,
                    "Used comparable properties" if prop_result.get('used_comparables', False) else "No direct comparables"
                ), unsafe_allow_html=True)
            
            with col2:
                token = st.session_state.get('upload_token', '')
                clean_token_val = clean_token(token)
                s3_manager = S3ApplicationManager()
                app_data = s3_manager.get_application(clean_token_val)
                st.markdown("""
                <div class="card success-card">
                    <h3 style="margin-top:0;">💰 Valuation Summary</h3>
                    <div style="text-align: center;">
                        <h1 style="margin:10px 0; color:#4CAF50;">₹{:,}</h1>
                        <p>Estimated Property Value</p>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top:15px;">
                        <div style="text-align: center;">
                            <h3 style="margin:5px 0;">₹{:,}</h3>
                            <p>Per Sq.Ft</p>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="margin:5px 0;">{:,}</h3>
                            <p>Sq.Ft</p>
                        </div>
                        <div style="text-align: center;">
                            <h3 style="margin:5px 0;">{:.0f}%</h3>
                            <p>LTV Ratio</p>
                        </div>
                    </div>
                </div>
                """.format(
                    prop_result.get('estimated_property_value', 0),
                    prop_result.get('price_per_sqft', 0),
                    prop_result.get('property_data', {}).get('size_sqft', 0),
                    (app_data.get('loan_amount', 0) / app_data.get('property_value', 1)) * 100
                ), unsafe_allow_html=True)
                
                # Valuation range visualization
                min_val = int(prop_result.get('estimated_property_value', 0) * 0.95)
                max_val = int(prop_result.get('estimated_property_value', 0) * 1.05)
                st.markdown(f"""
                <div style="margin-top:20px;">
                    <h4>Valuation Range</h4>
                    <div style="background: #f5f5f5; padding:10px; border-radius:5px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span>₹{min_val:,}</span>
                            <span>₹{max_val:,}</span>
                        </div>
                        <div style="height:10px; background:linear-gradient(90deg, #f44336, #ffeb3b, #4caf50); border-radius:5px; position:relative;">
                            <div style="position:absolute; left:50%; top:-5px; width:2px; height:20px; background:#000;"></div>
                        </div>
                        <div style="text-align:center; margin-top:5px;">
                            <span>₹{prop_result.get('estimated_property_value', 0):,}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab4:
        st.subheader("Credit Analysis")
        
        if not credit_result:
            st.warning("No credit score results available")
        else:
            score = credit_result.get('credit_score', 0)
            score_category = credit_result.get('score_category', 'Average')
            
            if score >= 750:
                color = "#4CAF50"  # Green
            elif score >= 650:
                color = "#8BC34A"  # Light green
            elif score >= 550:
                color = "#FFC107"  # Yellow
            else:
                color = "#F44336"  # Red
            
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <h3 style="margin-top:0;">Your Credit Score</h3>
                <div style="width:150px; height:150px; margin:0 auto; border-radius:50%; 
                    background:conic-gradient({color} 0% {score/10}%, #e0e0e0 {score/10}% 100%);
                    display:flex; align-items:center; justify-content:center;">
                    <div style="background:white; width:120px; height:120px; border-radius:50%; 
                        display:flex; align-items:center; justify-content:center;">
                        <h1 style="margin:0; color:{color};">{score}</h1>
                    </div>
                </div>
                <h3 style="color:{color};">{score_category}</h3>
                <p>{credit_result.get('score_message', '')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if score < 700:
            with st.expander("💡 Credit Improvement Tips", expanded=True):
                st.markdown("""
                - **Pay bills on time:** Set up automatic payments for at least the minimum amount due
                - **Reduce credit utilization:** Aim to use less than 30% of your available credit
                - **Avoid new credit applications:** Each hard inquiry can slightly lower your score
                - **Check for errors:** Review your credit report annually for inaccuracies
                - **Keep old accounts open:** Longer credit history improves your score
                    """)
    
    with tab5:
    
        st.subheader("Loan Recommendation")
        


        rec_result = result.get("results", {}).get("approval_recommendation", {})
        st.write(rec_result.get("recommendation"))
        if not rec_result:
            st.warning("No recommendation available")
        elif rec_result.get("status") == "success":
            # Display scenario analysis if available
            if "scenario_analysis" in rec_result:
                with st.expander("📊 Your Financial Scenario Analysis", expanded=True):
                    st.write(rec_result["scenario_analysis"])
            
            # Display loan options as compact cards
            if "table" in rec_result and rec_result["table"]:
                st.markdown("### Available Loan Options")
                
                # Create compact cards in columns
                cols = st.columns(len(rec_result["table"]))
                for idx, option in enumerate(rec_result["table"]):
                    with cols[idx]:
                        with st.container(border=True, height=350):  # Slightly taller to accommodate more info
                            # Style based on loan type
                            card_style = ""
                            if "Special" in option.get("option", ""):
                                card_style = "border-left: 5px solid #FF4B4B; background-color: #FFF5F5;"
                            elif "Premium" in option.get("option", ""):
                                card_style = "border-left: 5px solid #4B8DFF; background-color: #F5F9FF;"
                            else:
                                card_style = "border-left: 5px solid #00C853; background-color: #F5FFF7;"
                            
                            st.markdown(f"""<style>.card-{idx} {{{card_style}}}</style>""", 
                                        unsafe_allow_html=True)
                            st.markdown(f'<div class="card-{idx}">', unsafe_allow_html=True)
                            
                            # Header with icon
                            if "Special" in option.get("option", ""):
                                st.subheader(f"⚠️ {option.get('option', '')}")
                                st.caption("Higher interest due to credit risk")
                            else:
                                st.subheader(f"✅ {option.get('option', '')}")
                                st.caption("Standard eligibility terms")
                            
                            # Compact metrics with better formatting
                            st.markdown(f"""
                            **Loan Amount:**  
                            {option.get('loan_amount', 'N/A')}  
                            
                            **Interest Rate:**  
                            {option.get('interest_rate', 'N/A')}  
                            
                            **Tenure:**  
                            {option.get('tenure', 'N/A')} years  
                            
                            **Monthly EMI:**  
                            {option.get('monthly_emi', 'N/A')}  
                            """)
                            
                            # Eligibility badge with more context
                            if option.get("eligibility", "").lower() == "eligible":
                                st.success("✔️ Eligible (meets all criteria)")
                            else:
                                st.warning(f"❗ {option.get('eligibility', 'Conditional Approval')}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display offer rationale if available
            if "offer_rationale" in rec_result:
                with st.expander("ℹ️ Why these options were recommended", expanded=True):
                    st.write(rec_result["offer_rationale"])
            
            # Suggested next steps with icons
            st.divider()
            st.markdown("### 📝 Suggested Next Steps")
            st.markdown("""
            1. **Review** the loan options above  
            2. **Compare** EMI amounts with your budget  
            3. **Contact** a loan officer for clarification  
            4. **Consider** adjusting your amount if needed  
            """)
            
            # Additional warnings if applicable
            if "LTV exceeded" in str(rec_result.get("recommendation", "")):
                st.warning("ℹ️ Note: The recommended amount is lower than requested due to LTV limits")
            elif "not eligible" in str(rec_result.get("recommendation", "")).lower():
                st.error("🚨 Current application doesn't meet standard eligibility criteria")
        else:
            st.error("Recommendation generation failed")
            st.error(rec_result.get("message", "Unknown error"))
    
    
    # Footer with navigation
    st.markdown("---")
    col1, col2 = st.columns([2,1])
    with col1:
        pass
    with col2:
        if st.button("← Back to Application", use_container_width=True):
            st.session_state.current_view = "chat"
            st.rerun()
    

def main():
    st.title("Home Loan Assistant")
    
    if hasattr(st.session_state, 'edit_token') and st.session_state.current_view == "edit_form":
        if st.session_state.edit_token not in st.session_state.applications:
            app_data = st.session_state.chatbot.s3_manager.get_application(st.session_state.edit_token)
            if app_data:
                st.session_state.applications[st.session_state.edit_token] = app_data
        
        existing_data = st.session_state.applications.get(st.session_state.edit_token, {})
        if existing_data:
            render_application_form(edit_mode=True, existing_data=existing_data)
        else:
            st.error(f"Application with token {st.session_state.edit_token} not found")
            if st.button("← Back to Chat"):
                st.session_state.current_view = "chat"
                if hasattr(st.session_state, 'edit_token'):
                    del st.session_state.edit_token
                st.session_state.show_form_button = False
                st.session_state.show_update_button = False
                st.rerun()
    
    elif st.session_state.current_view == "application_form":
        render_application_form()
        
        if st.button("← Back to Chat"):
            st.session_state.current_view = "chat"
            st.session_state.show_form_button = False
            st.session_state.show_update_button = False
            st.rerun()
        
    elif st.session_state.current_view == "document_upload":
        if 'upload_token' not in st.session_state or not st.session_state.upload_token:
            st.error("No application token found. Please submit an application first.")
            if st.button("← Back to Chat"):
                st.session_state.current_view = "chat"
                st.rerun()
        else:
            token = st.session_state.upload_token
            s3_manager = st.session_state.chatbot.s3_manager
            render_document_upload(token, s3_manager)

    elif st.session_state.current_view == "results":
        render_results()  # <-- This is the new results page
    elif st.session_state.show_cancel_button:
        handle_cancellation_flow()
    
    else:
        render_chat_interface()
    with st.sidebar:
    # 1. NEW CHAT BUTTON
        if st.button("🆕 New Chat", 
                    key="new_chat_button",
                    help="Start a fresh conversation",
                    use_container_width=True):
            # Save current chat to history before resetting (if not empty)
            if len(st.session_state.chat_history) > 1:  # More than just initial greeting
                timestamp = datetime.now().strftime("%m/%d %I:%M %p")
                if 'chat_history_sessions' not in st.session_state:
                    st.session_state.chat_history_sessions = {}
                st.session_state.chat_history_sessions[timestamp] = st.session_state.chat_history.copy()
            
            # Reset to fresh chat
            st.session_state.chat_history = [{
                "role": "assistant",
                "content": "Hello! I'm your Home Loan Assistant. How can I help you today?"
            }]
            
            # Clear any form states
            for key in ['form_data', 'show_form_button', 'show_update_button','show_upload_button','show_existing_customer_question']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
        
        # 2. CHAT HISTORY SECTION
        st.markdown("---")
        st.header("📚 Chat History")
        
        # Display saved chats if they exist
        if hasattr(st.session_state, 'chat_history_sessions') and st.session_state.chat_history_sessions:
            # Sort chats by most recent first
            sorted_sessions = sorted(
                st.session_state.chat_history_sessions.items(),
                key=lambda x: datetime.strptime(x[0], "%m/%d %I:%M %p"),
                reverse=True
            )
            
            # Display as selectable items
            selected_chat = st.selectbox(
                "Previous conversations",
                options=["Select a chat..."] + [f"Chat {i+1} ({date})" 
                                            for i, (date, _) in enumerate(sorted_sessions)],
                key="chat_history_selector"
            )
            
            # Load selected chat
            if selected_chat != "Select a chat...":
                # Extract the timestamp from the selected option
                selected_timestamp = selected_chat.split("(")[1].rstrip(")")
                st.session_state.chat_history = st.session_state.chat_history_sessions[selected_timestamp].copy()
                st.rerun()
        else:
            st.caption("No previous chats yet")
        st.markdown("---")
        st.header("💰 EMI Calculator")

        # Default values
        default_loan_amount = 5000000  # ₹50 lakhs
        default_interest_rate = 8.5    # 8.5%
        default_tenure = 240           # 20 years (240 months)

        # Loan amount input
        loan_amount = st.number_input(
            "Loan Amount (₹)",
            min_value=100,
            max_value=100000000,
            value=default_loan_amount,
            step=10000
        )

        # Interest rate slider
        interest_rate = st.slider(
            "Interest Rate (%)",
            min_value=5.0,
            max_value=20.0,
            value=default_interest_rate,
            step=0.1,
            format="%.1f%%"
        )

        # Tenure slider (in months)
        tenure = st.slider(
            "Tenure (months)",
            min_value=3,
            max_value=360,
            value=default_tenure,
            step=1
        )

        # Calculate EMI and total interest
        monthly_rate = interest_rate / 12 / 100
        emi = (loan_amount * monthly_rate * (1 + monthly_rate)**tenure) / ((1 + monthly_rate)**tenure - 1)
        total_payment = emi * tenure
        total_interest = total_payment - loan_amount

        # Display results in a single box with smaller font
        with st.container(border=True):
            st.markdown("""
            <style>
            .small-metric {
                font-size: 14px !important;
            }
            </style>
            """, unsafe_allow_html=True)
        
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<p class="small-metric">Monthly EMI</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="small-metric">₹{emi:,.0f}</p>', unsafe_allow_html=True)
            with col2:
                st.markdown('<p class="small-metric">Total Interest</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="small-metric">₹{total_interest:,.0f}</p>', unsafe_allow_html=True)
            with col3:
                st.markdown('<p class="small-metric">Total Payment</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="small-metric">₹{total_payment:,.0f}</p>', unsafe_allow_html=True)

        # Add some explanation
        st.caption("Note: This is an estimate. Actual terms may vary based on your eligibility.")

if __name__ == "__main__":
    main()