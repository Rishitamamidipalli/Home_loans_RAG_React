import streamlit as st
import os
import boto3
from datetime import datetime
import re
from typing import Dict, Any, List
import json
from s3_manager import S3ApplicationManager
from rag_system import HomeLoanRAGSystem

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
LANGCHAIN_AVAILABLE = True


def clean_token(token: str) -> str:
    """Clean and standardize token format"""
    if not token:
        return ""
    return str(token).strip().upper()

class HomeLoanChatbot:
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.llm = None
        self.memory = None
        self.conversation = None
        self.s3_manager = S3ApplicationManager(region_name)
        self.rag_system = HomeLoanRAGSystem()
        # Initialize RAG system with better error handling
        '''try:
            self.rag_system = HomeLoanRAGSystem()
            if not self.rag_system.is_initialized():
                st.warning("RAG system not available. Basic queries will use fallback responses.")
                # Try to reset and reinitialize if not working
                HomeLoanRAGSystem.reset_instance()
                self.rag_system = HomeLoanRAGSystem()
                if self.rag_system.is_initialized():
                    st.success("RAG system successfully reinitialized!")
        except Exception as e:
            st.error(f"Failed to initialize RAG system: {str(e)}")
            # Reset instance and try once more
            try:
                HomeLoanRAGSystem.reset_instance()
                self.rag_system = HomeLoanRAGSystem()
                if self.rag_system.is_initialized():
                    st.success("RAG system recovered after reset!")
                else:
                    st.warning("RAG system unavailable. Using fallback responses.")
                    self.rag_system = None
            except Exception as e2:
                st.error(f"RAG system completely unavailable: {str(e2)}")
                self.rag_system = None'''
        
        self.system_prompt ="""
You are a home loan bot that ONLY responds using the predefined tags below. Follow these rules strictly:

1. **Respond with `<<BASIC_QUERY>>` ONLY IF the user's message is clearly about**:
   - Home loan interest rates
   - Eligibility
   - EMI calculation
   - Required documents

   ✅ Example triggers:
   - "What is the home loan interest rate?"
   - "Am I eligible for a loan?"
   - "What documents do I need?"
   - "How is EMI calculated?"

   ❌ Do NOT respond with `<<BASIC_QUERY>>` for:
   - Casual or off-topic questions
   - Non-home-loan-related messages

2. **For any message NOT related to home loans**, reply EXACTLY with:
   "Please ask relevant home loan questions only."

3. **For application actions**, respond with **EXACTLY** these phrases **and nothing else**:  
        a. When the user wants to apply for a new loan, respond with exactly: "<<APPLICATION_FORM>>"
        b. When user mentions anything about documents, files, uploading, or updating files:
                    If token is present: "<<UPLOAD_DOCUMENTS>> [token_number]"
                    If no token provided: "<<REQUEST_DOCUMENT_ACTION>>"
        c. When the user wants to update/cancel an application but hasn't provided a token, respond with exactly: "<<REQUEST_TOKEN>> [update/cancel]"
        d. When you detect an application token in the message (format: HL followed by 13 digits example: HL1234567890123), respond with exactly: "<<FOUND_TOKEN>> [token_number] [action]" where action is one of: view/update/cancel/upload
        e. For status inquiries about existing applications, respond with exactly: "<<STATUS_REQUEST>>"
        f. For all other home loan queries, provide professional, helpful responses. 

4. **Token rules**:
   - Only accept token in exact format: HL followed by exactly 13 digits
   - Never accept partial or malformed tokens

5. **Strict output rules**:
   - No explanations, no extra messages
   - Respond ONLY with the exact tag or phrase
   - Never break format or improvise

Current date: {current_date}""".format(current_date=datetime.now().strftime("%Y-%m-%d"))

        
        if LANGCHAIN_AVAILABLE:
            try:
                self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)
                self._initialize_bedrock_llm()
            except Exception as e:
                st.error(f"Failed to initialize LLM: {str(e)}")
                self.llm = None
   
    def _initialize_bedrock_llm(self):
        if not LANGCHAIN_AVAILABLE:
            return
            
        try:
            bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name
            )
            
            self.llm = ChatBedrock(
                client=bedrock_client,
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                model_kwargs={
                    "max_tokens": 8000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            if self.llm and self.memory:
                prompt_template = PromptTemplate(
                    input_variables=["history", "input"],
                    template=f"{self.system_prompt}\n\nConversation History:\n{{history}}\n\nHuman: {{input}}\nAssistant:"
                )
                
                self.conversation = ConversationChain(
                    llm=self.llm,
                    memory=self.memory,
                    prompt=prompt_template,
                    verbose=False
                )
            
        except Exception as e:
            st.error(f"AWS Bedrock initialization failed: {str(e)}")
            self.llm = None

    def get_response(self, message: str, chat_history: list) -> str:
        # Skip processing if in document upload view
        if st.session_state.get('current_view') == 'document_upload':
            return ""

        try:
            # Always try to use the LLM first for semantic understanding
            if self.llm and self.conversation:
                try:
                    # Update memory with recent chat history
                    self._update_memory_from_history(chat_history)
                    
                    # Get response from AWS Bedrock
                    llm_response = self.conversation.predict(input=message).strip()
                    print('xxxxxxxxxxxxxxxxx',llm_response)
                    if "<<BASIC_QUERY>>" in llm_response:
                        # Use RAG system to answer basic queries
                        print(f"DEBUG: RAG system initialized: {self.rag_system.is_initialized() if self.rag_system else False}")
                        if self.rag_system and self.rag_system.is_initialized():
                            print(f"DEBUG: Searching for query: {message}")
                            # First test the search directly
                            search_results = self.rag_system.search_similar_documents(message, top_k=3)
                            print(f"DEBUG: Found {len(search_results)} documents")
                            
                            rag_response = self.rag_system.generate_rag_response(message, self.conversation)
                            if "<<BASIC_QUERY>>" in rag_response:
                                rag_response = rag_response.replace("<<BASIC_QUERY>>", "")
                            return rag_response
                        else:
                            # Fallback response when RAG is not available
                            return "I'd be happy to help with your home loan query. However, our knowledge base is currently unavailable. Please contact our support team for detailed information about home loans, interest rates, eligibility criteria, and documentation requirements."
                    elif "<<APPLICATION_FORM>>" in llm_response:
                    # First check if we've already asked about existing customer status
                        if "is_existing_customer" not in st.session_state:
                            st.session_state.show_existing_customer_question = True
                            return "Are you an existing customer? (Please select below)"
                        else:
                            # If we know they're existing, show update button
                            if st.session_state.is_existing_customer:
                                st.session_state.show_update_button = True
                                st.session_state.application_mode = "update"
                                return "I see you're an existing customer. Please provide your application token to update your details."
                            # Otherwise show new application button
                            else:
                                st.session_state.show_form_button = True
                                st.session_state.application_mode = "new"
                                return "I can help you apply for a home loan. Please provide the following details:"
                    elif "<<REQUEST_TOKEN>>" in llm_response:
                        action = llm_response.split("<<REQUEST_TOKEN>>")[1].strip().lower()
                        if action.lower() in ["upload", "[upload]"]:
                            st.session_state.show_upload_button = True
                        if action.lower() in ["cancel", "[cancel]"]:
                            st.session_state.show_cancel_button = True
                            return f"How can i assist you further?."
                        elif action.lower() in ["update", "[update]"]:
                            st.session_state.show_update_button = True
                        
                        return f"Please provide your application token number (format: HL followed by 13 digits) so I can assist you with {action}."
                    elif "<<STATUS_REQUEST>>" in llm_response:
                        return "Please provide your application token number (format: HL followed by 13 digits) so I can assist you with status request."
                    elif "<<FOUND_TOKEN>>" in llm_response:
                        parts = llm_response.split("<<FOUND_TOKEN>>")[1].strip().split()
                        token = parts[0]
                        action = parts[1] if len(parts) > 1 else "view"
                        if not re.match(r'^HL\d{13}$', token):
                            return "Invalid token format. Please provide a valid token (HL followed by 13 digits)."
                        return self.handle_token_query(token, message)
                    elif "<<UPLOAD_DOCUMENTS>>" in llm_response or "<<REQUEST_DOCUMENT_ACTION>>" in llm_response:
                        if "<<REQUEST_DOCUMENT_ACTION>>" in llm_response:
                            # Case where user asked about documents but didn't provide token
                            st.session_state.show_upload_button = True
                            return "Please provide your application token to upload or update documents."
                        elif "<<UPLOAD_DOCUMENTS>>" in llm_response:
                            token_match = re.search(r'HL\d{13}', llm_response)
                            if token_match:
                                token = token_match.group(0)
                                if re.match(r'^HL\d{13}$', token):
                                    st.session_state.current_view = "document_upload"
                                    st.session_state.show_upload_button = False
                                    st.session_state.upload_token = token
                                    
                                    return f"Ready to upload documents for application. "
                            return "Please provide a valid application token to upload documents."
                    # Default case - return the LLM's response
                    return llm_response
                except Exception as e:
                    st.error(f"Error getting response from LLM: {str(e)}")
                    # Fall through to basic response
            
            # Fallback for when LLM isn't available
            return self._fallback_response(message)
                
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return "I encountered an error processing your request. Please try again."

    def _update_memory_from_history(self, chat_history: list):
        try:
            if not self.memory:
                return
                
            self.memory.clear()
            
            if chat_history:
                for msg in chat_history[-10:]:
                    if msg.get("role") == "user":
                        self.memory.chat_memory.add_user_message(msg.get("content", ""))
                    elif msg.get("role") == "assistant":
                        self.memory.chat_memory.add_ai_message(msg.get("content", ""))
        except Exception as e:
            st.error(f"Error updating memory: {str(e)}")

    def _fallback_response(self, message: str) -> str:
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['eligibility', 'eligible', 'qualify']):
            return "To be eligible for a home loan, you typically need: 1) Stable income for 2+ years, 2) Good credit score (750+), 3) Age between 23-70 years, 4) Debt-to-income ratio below 40%."
        
        elif any(word in message_lower for word in ['interest', 'rate', 'emi']):
            return "Current home loan interest rates range from 8.5% to 11.5% per annum. Rates depend on your credit profile, loan amount, and tenure."
        
        elif any(word in message_lower for word in ['documents', 'papers', 'required']):
            return "Required documents include: 1) Identity proof, 2) Address proof, 3) Income proof, 4) Bank statements, 5) Property documents."
        
        elif any(word in message_lower for word in ['tenure', 'duration', 'repayment']):
            return "Home loan tenure typically ranges from 10 to 30 years. Longer tenure means lower EMI but higher total interest."
        
        elif any(word in message_lower for word in ['application', 'apply', 'form']):
            st.session_state.show_form_button = True
            return "You can apply for a home loan by clicking the 'Apply for Home Loan' button."
        
        elif any(word in message_lower for word in ['update', 'edit', 'change']):
            st.session_state.show_update_button = True
            return "Please provide your application token number to update your application."
        
        elif any(word in message_lower for word in ['cancel', 'delete', 'terminate']):
            st.session_state.show_cancel_button = True
            return "Please provide your application token number to cancel your application."
        
        else:
            return "I'm here to help with your home loan queries! Ask me about eligibility, interest rates, documents, or application process."

    def handle_token_query(self, token: str, message: str) -> str:
        """Handle token-based queries including document uploads"""
        clean_token_val = clean_token(token)
        
        # Validate token format
        if not clean_token_val or not re.match(r'^HL\d{13}$', clean_token_val):
            return "Invalid token format. Please provide a valid token (HL followed by 13 digits)."
        
        # Check application existence (session cache or S3)
        if clean_token_val not in st.session_state.applications:
            app_data = self.s3_manager.get_application(clean_token_val)
            if app_data:
                st.session_state.applications[clean_token_val] = app_data
            else:
                return f"I couldn't find an application with token {clean_token_val}. Please check your token and try again."
        
        app_data = st.session_state.applications[clean_token_val]
        message_lower = message.lower()  # Case-insensitive matching
        
        
        if any(word in message_lower for word in ['upload', 'document', 'documents', 'file', 'files']):
            st.session_state.current_view = "document_upload"
            st.session_state.upload_token = clean_token_val
            st.session_state.current_token = clean_token_val
            st.session_state.show_upload_button = False # Also set current_token for document upload view
            return f"Ready to upload documents for application . "
        
        elif any(word in message_lower for word in ['edit', 'modify', 'change', 'update']):
            st.session_state.edit_token = clean_token_val
            st.session_state.current_view = "edit_form"
            st.session_state.form_data = app_data
            st.rerun()
            return f"Found your application {clean_token_val}. Please update your information below."
        
        # Cancel application
        elif any(word in message_lower for word in ['cancel', 'delete', 'terminate']):
            st.session_state.cancel_token = clean_token_val
            st.session_state.show_cancel_button = True
            st.rerun()
            return f"Found your application {clean_token_val}. Please confirm cancellation below."
        
        # Document upload
        
        # Status check
        elif any(word in message_lower for word in ['status', 'check', 'details']):
            documents = self.s3_manager.list_documents(clean_token_val)
            doc_count = len(documents)
            if doc_count == 0:
                doc_list = "No documents uploaded yet."
            else:
                doc_list = "\n".join([f"• {doc['name']}" for doc in documents])
            return (
                f"Application {clean_token_val} details:\n\n"
                f"\nSubmitted: {app_data['submission_time']}\n\n"
                f"\nLoan Amount: ₹{app_data.get('loan_amount', 0):,}\n\n"
                f"\nDocuments Uploaded: {doc_count}\n\n"
                f"\nDocument List:\n{doc_list}"
            )
                
        # Default response
        else:
            documents = self.s3_manager.list_documents(clean_token_val)
            if len(documents) == 4:
                return (
                    f"Found your application {clean_token_val}.\n\n"
                    "You can:\n"
                    "- Check status/details\n"
                    "- Update application\n"
                    "- Change uploaded documents\n"
                    "- Cancel application\n"
                    "Please specify what you'd like to do."
                )
            else:
                return (
                    f"Found your application {clean_token_val}.\n\n"
                    "You can:\n"
                    "- Check status/details\n"
                    "- Update application\n"
                    "- Upload documents\n"
                    "- Cancel application\n"
                    "Please specify what you'd like to do."
                )