import streamlit as st
import os
import time
import boto3
from datetime import datetime
import re
from typing import Dict, Any, List, Optional
import json
import botocore
import uuid

# Updated LangChain imports
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
LANGCHAIN_AVAILABLE = True
# S3 Configuration
S3_BUCKET_NAME = "sarma-1"
S3_PREFIX = "customers_data/"

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


class S3ApplicationManager:
    def __init__(self, region_name="us-east-1"):
        self.s3 = boto3.client('s3', region_name=region_name)
    
    def ensure_folder_exists(self, token: str) -> bool:
        """Ensure the token folder exists in S3"""
        try:
            clean_token_val = clean_token(token)
            folder_key = f"{S3_PREFIX}{clean_token_val}/"
            self.s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=folder_key,
                Body=b'',
                ContentType='application/x-directory'
            )
            return True
        except Exception as e:
            st.error(f"Failed to create folder in S3: {str(e)}")
            return False
    
    def save_application(self, token: str, application_data: dict):
        try:
            clean_token_val = clean_token(token)
            
            # Ensure the folder exists
            if not self.ensure_folder_exists(clean_token_val):
                return False
                
            # Save the application data with the new structure
            key = f"{S3_PREFIX}{clean_token_val}/{clean_token_val}_basic_info.json"
            self.s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=key,
                Body=json.dumps(application_data, default=str, indent=2),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            st.error(f"Failed to save application to S3: {str(e)}")
            return False
    
    def get_application(self, token: str) -> Optional[dict]:
        try:
            clean_token_val = clean_token(token)
            if not clean_token_val:
                return None
                
            key = f"{S3_PREFIX}{clean_token_val}/{clean_token_val}_basic_info.json"
            response = self.s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            st.error(f"Error retrieving application: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def update_application(self, token: str, updated_data: dict):
        try:
            clean_token_val = clean_token(token)
            existing_data = self.get_application(clean_token_val)
            if not existing_data:
                return False
            
            existing_data.update(updated_data)
            existing_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.save_application(clean_token_val, existing_data)
        except Exception as e:
            st.error(f"Failed to update application in S3: {str(e)}")
            return False
    
    def delete_application(self, token: str) -> bool:
        try:
            clean_token_val = clean_token(token)
            prefix = f"{S3_PREFIX}{clean_token_val}/"
            
            # List and delete all objects in the folder
            objects_to_delete = []
            list_response = self.s3.list_objects_v2(
                Bucket=S3_BUCKET_NAME,
                Prefix=prefix
            )
            
            if 'Contents' in list_response:
                objects_to_delete = [{'Key': obj['Key']} for obj in list_response['Contents']]
                self.s3.delete_objects(
                    Bucket=S3_BUCKET_NAME,
                    Delete={'Objects': objects_to_delete}
                )
            
            return True
        except Exception as e:
            st.error(f"Failed to delete application from S3: {str(e)}")
            return False
    
    def list_applications(self) -> list:
        try:
            response = self.s3.list_objects_v2(
                Bucket=S3_BUCKET_NAME,
                Prefix=S3_PREFIX
            )
            return [obj['Key'].replace(S3_PREFIX, '').replace('.json', '').split('/')[0] 
                   for obj in response.get('Contents', []) 
                   if obj['Key'].endswith('.json')]
        except Exception as e:
            st.error(f"Failed to list applications from S3: {str(e)}")
            return []
    def upload_document(self, token: str, file_obj, doc_type: str) -> str:
        """
        Upload a document to S3 and return the full S3 path
        Format: s3://{bucket}/{prefix}{token}/documents/{token}_{doc_type}.ext
        """
        try:
            print(token,file_obj,doc_type)
            clean_token_val = clean_token(token)
            
            # 1. Ensure documents folder exists
            documents_prefix = f"{S3_PREFIX}{clean_token_val}/documents/"
            self.s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=documents_prefix,
                Body=b'',
                ContentType='application/x-directory'
            )
            
            # 2. Get file extension and document type
            if hasattr(file_obj, 'filename'):  # FastAPI UploadFile
                filename = file_obj.filename
            elif hasattr(file_obj, 'name'):    # Regular file object
                filename = file_obj.name
            else:                              # SpooledTemporaryFile
                filename = doc_type + '.jpg'   # Default extension
                
            file_base = os.path.splitext(filename)[0]
            doc_type = file_base.split('_')[0]  # Extract PAN from PAN.jpg or similar
            file_ext = os.path.splitext(filename)[1][1:].lower() if '.' in filename else 'jpg'
            
            if file_ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # 3. Upload file
            file_key = f"{documents_prefix}{clean_token_val}_{doc_type}.{file_ext}"
            
            if hasattr(file_obj, 'read'):
                file_bytes = file_obj.read()
            elif hasattr(file_obj, 'getvalue'):
                file_bytes = file_obj.getvalue()
            else:
                raise ValueError("Invalid file object - no readable content")
                
            if not file_bytes:
                raise ValueError("Empty file content")
                
            self.s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_key,
                Body=file_bytes,
                ContentType=self._get_content_type(file_ext)
            )
            
            # Return full S3 path
            return f"s3://{S3_BUCKET_NAME}/{file_key}"
            
        except Exception as e:
            st.error(f"Failed to upload document: {str(e)}")
            raise  # Re-raise to handle in calling code
    def list_documents(self, token: str) -> list:
        """List all documents with full S3 paths"""
        try:
            clean_token_val = clean_token(token)
            prefix = f"{S3_PREFIX}{clean_token_val}/documents/"
            
            response = self.s3.list_objects_v2(
                Bucket=S3_BUCKET_NAME,
                Prefix=prefix
            )
            
            return [{
                'name': obj['Key'].split('/')[-1],
                's3_path': f"s3://{S3_BUCKET_NAME}/{obj['Key']}",
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            } for obj in response.get('Contents', []) if obj['Key'] != prefix]
        except Exception as e:
            st.error(f"Failed to list documents: {str(e)}")
            return []
    
    def _get_content_type(self, file_ext: str) -> str:
        """Map file extension to content type"""
        return {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }.get(file_ext, 'application/octet-stream')
 
    def list_documents(self, token: str) -> list:
        """List all documents for a given token and clean filenames by removing token prefix"""
        try:
            clean_token_val = clean_token(token)
            prefix = f"customers_data/{clean_token_val}/documents/"
            response = self.s3.list_objects_v2(
                Bucket="sarma-1",
                Prefix=prefix
            )
            
            documents = []
            for obj in response.get('Contents', []):
                if obj['Key'] == prefix:  # Skip the folder itself
                    continue
                    
                filename = obj['Key'].split('/')[-1]
                # Remove token prefix if present (both with underscore and hyphen cases)
                if filename.startswith(f"{clean_token_val}_"):
                    clean_filename = filename[len(clean_token_val)+1:]
                elif filename.startswith(f"{clean_token_val}-"):
                    clean_filename = filename[len(clean_token_val)+1:]
                else:
                    clean_filename = filename
                    
                documents.append({
                    'name': clean_filename,
                    'original_name': filename,  # Keep original filename with token
                    's3_path': f"s3://{S3_BUCKET_NAME}/{obj['Key']}",
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'file_id': filename  # Use original filename as file_id
                })
                
            return documents
        except Exception as e:
            st.error(f"Failed to list documents: {str(e)}")
            return []
    def delete_document(self, token: str, filename: str) -> None:
        """
        Delete a document from S3
        Format: {prefix}{token}/documents/{filename}
        """
        try:
            actual_token=filename 
            actual_file_name=token
            clean_token_val = clean_token(actual_token)
            file_key = f"{S3_PREFIX}{clean_token_val}/documents/{actual_file_name}"
            print("file_key",file_key)
            self.s3.delete_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_key
            )
        except Exception as e:
            print(f"Failed to delete document {filename}: {str(e)}")
            raise
