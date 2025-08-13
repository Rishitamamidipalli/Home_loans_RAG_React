from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import tempfile
import json
from datetime import datetime

# Import existing modules
from s3_manager import S3ApplicationManager
from orchestration_agent import HomeLoanOrchestrator
from chatbot import HomeLoanChatbot
from utils import *

app = FastAPI(title="Home Loan Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
s3_manager = S3ApplicationManager()
orchestrator = HomeLoanOrchestrator()
chatbot = HomeLoanChatbot()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    show_form_button: bool = False
    show_upload_button: bool = False
    show_update_button: bool = False
    show_cancel_button: bool = False

class ApplicationForm(BaseModel):
    # Personal Information
    full_name: str
    date_of_birth: str
    phone: str
    email: str
    pan_number: str
    aadhar_number: int
    marital_status: str
    existing_loan_amount: float
    
    # Employment Information
    employment_status: str
    employer_name: str
    job_title: str
    employment_duration_years: int
    employment_duration_months: int
    annual_income: float
    additional_income: float
    
    '''# Financial Information
    monthly_debt_payments: float
    credit_score: int
    down_payment: float
    savings_amount: float
    checking_balance: float
    investment_accounts: float
    retirement_accounts: float'''
    
    # Property Information
    property_type: str
    property_value: float
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    loan_purpose: str
    loan_amount: float
    loan_term: int

class ApplicationResponse(BaseModel):
    success: bool
    message: str
    application_id: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None

# In-memory storage for session data (replace with Redis in production)
sessions = {}

@app.get("/")
async def root():
    return {"message": "Home Loan Assistant API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_data: ChatMessage):
    """Handle chat interactions"""
    try:
        # Initialize session if not exists
        if chat_data.session_id not in sessions:
            sessions[chat_data.session_id] = {
                "chat_history": [{
                    "role": "assistant",
                    "content": "Hello! I'm your Home Loan Assistant. I can help you with information about home loans, eligibility, interest rates, and more. How can I assist you today?"
                }],
                "applications": {},
                "show_form_button": False,
                "show_upload_button": False,
                "show_update_button": False,
                "show_cancel_button": False
            }
        
        session = sessions[chat_data.session_id]
        
        # Add user message to history
        session["chat_history"].append({
            "role": "user", 
            "content": chat_data.message
        })
        
        # Get response from chatbot
        response = chatbot.get_response(chat_data.message, session["chat_history"])
        
        # Add assistant response to history
        session["chat_history"].append({
            "role": "assistant",
            "content": response
        })
        
        # Determine button visibility
        print(session)
        print(chat_data.message)
        user_wants_to_apply = "apply" in chat_data.message.lower() or "application" in chat_data.message.lower()
        assistant_suggests_apply = "application" in response.lower()
        user_wants_to_upload = "upload" in chat_data.message.lower() or "document" in chat_data.message.lower()

        # Show form button if user wants to apply or assistant suggests it
        session["show_form_button"] = user_wants_to_apply or assistant_suggests_apply

        # Show upload button if user asks to upload or if they have a pending application
        has_pending_application = session.get("application_status") == "pending_documents"
        session["show_upload_button"] = user_wants_to_upload or has_pending_application
        
        return ChatResponse(
            response=response,
            show_form_button=session["show_form_button"],
            show_upload_button=session["show_upload_button"],
            show_update_button=session["show_update_button"],
            show_cancel_button=session["show_cancel_button"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history and button states for a session"""
    if session_id not in sessions:
        # Return a default state if session doesn't exist
        return {
            "history": [{
                "role": "assistant",
                "content": "Hello! I'm your Home Loan Assistant. How can I assist you today?"
            }],
            "show_upload_button": False
        }
    
    session = sessions[session_id]
    return {
        "history": session.get("chat_history", []),
        "show_form_button": session.get("show_form_button", False),
        "show_upload_button": session.get("show_upload_button", False),
        "show_update_button": session.get("show_update_button", False),
        "show_cancel_button": session.get("show_cancel_button", False)
    }

@app.post("/api/application", response_model=ApplicationResponse)
async def submit_application(request: Request, session_id: str = Form(...)):
    """Submit loan application (accepts multipart form data from the frontend)."""
    try:
        # Read all fields submitted as multipart/form-data
        form = await request.form()
        # Convert to a plain dict and exclude session_id (already captured)
        form_data = {k: v for k, v in form.items() if k != "session_id"}

        # Generate application ID using HL<timestamp> format
        # Reuse the existing generate_token() logic from utils.py
        application_id = generate_token()

        # Store application in session
        if session_id not in sessions:
            sessions[session_id] = {"applications": {}}

        sessions[session_id]["applications"][application_id] = form_data

        # Persist the application to S3 so it appears under:
        # s3://sarma-1/customers_data/<application_id>/<application_id>_basic_info.json
        try:
            s3_payload = {
                **form_data,
                "application_id": application_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            s3_manager.save_application(application_id, s3_payload)
        except Exception as e:
            # Do not fail the request if S3 persistence fails; just proceed
            pass

        # Store application status as 'pending_documents' - workflow runs after upload
        sessions[session_id]["application_status"] = "pending_documents"
        sessions[session_id]["current_application_id"] = application_id
        
        # Add a chat message about successful submission and next steps
        if "chat_history" not in sessions[session_id]:
            sessions[session_id]["chat_history"] = []
        
        sessions[session_id]["chat_history"].append({
            "role": "assistant",
            "content": f"🎉 Great! Your loan application has been submitted successfully.\n\n📋 **Your Application ID:** {application_id}\n\n📄 **Next Step:** Please upload your required documents (income proof, ID proof, address proof, etc.) to complete your application. Click the 'Upload Documents' button below to get started."
        })
        
        # Set flags to show upload button in chat
        sessions[session_id]["show_upload_button"] = True
        sessions[session_id]["show_form_button"] = False
        
        return ApplicationResponse(
            success=True,
            message=f"Application submitted! Your ID is {application_id}. Please proceed to upload documents.",
            application_id=application_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    token: str = Form(...)  # Keep token for now, but use session data for ID
):
    """Upload document to S3"""
    try:
        # Save uploaded file temporarily (cross-platform temp dir)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # The 'token' from the frontend is not the application ID.
        # Get the correct application ID from the session.
        if session_id not in sessions or "current_application_id" not in sessions[session_id]:
            raise HTTPException(status_code=400, detail="No active application found for this session.")
        
        application_id = sessions[session_id]["current_application_id"]

        # Upload to S3 using the correct application_id
        success = s3_manager.upload_document(application_id, temp_path, file.filename)
        
        if success:
            # Check if this is the first document upload for a pending application
            if (sessions[session_id].get("application_status") == "pending_documents"):
                
                # Get the application data
                if application_id in sessions[session_id]["applications"]:
                    form_data = sessions[session_id]["applications"][application_id]
                    
                    # Run orchestrator workflow now that documents are uploaded
                    try:
                        # Pass the correct application_id and the path to the temp file
                        workflow_result = orchestrator.run_workflow(form_data, {application_id: temp_path})
                        
                        # Update application status
                        sessions[session_id]["application_status"] = "processing"
                        
                        # Add chat message about processing
                        sessions[session_id]["chat_history"].append({
                            "role": "assistant",
                            "content": f"📄 Document uploaded successfully! Your application {application_id} is now being processed by our loan officers. You will receive updates on the status shortly."
                        })
                        
                        # Hide upload button, processing has started
                        sessions[session_id]["show_upload_button"] = False
                        
                    except Exception as e:
                        # If workflow fails, still confirm upload but note processing error
                        sessions[session_id]["chat_history"].append({
                            "role": "assistant",
                            "content": f"📄 Document uploaded successfully! However, there was an issue starting the processing workflow: {str(e)}. Please contact support."
                        })
            
            # Clean up temp file AFTER all processing is done
            os.remove(temp_path)

            return DocumentUploadResponse(
                success=True,
                message="Document uploaded successfully!",
                filename=file.filename
            )
        else:
            # Clean up temp file even if S3 upload fails
            os.remove(temp_path)
            return DocumentUploadResponse(
                success=False,
                message="Failed to upload document"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{token}")
async def list_documents(token: str):
    """List uploaded documents"""
    try:
        documents = s3_manager.list_documents(token)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{token}/{filename}")
async def delete_document(token: str, filename: str):
    """Delete uploaded document"""
    try:
        s3_manager.delete_document(token, filename)
        return {"success": True, "message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/application/{session_id}/{application_id}")
async def get_application(session_id: str, application_id: str):
    """Get application details"""
    if session_id not in sessions or application_id not in sessions[session_id]["applications"]:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return sessions[session_id]["applications"][application_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
