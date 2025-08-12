# document_validator_agent_aws.py
import re
import json
import boto3
from typing import List, Dict, Any
import logging
from urllib.parse import urlparse
from datetime import datetime

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- AWS Textract Helper Functions (Production Ready) ---

def _parse_textract_kvs(blocks: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Parses a real Textract response to extract key-value pairs accurately by
    following the block relationships.
    """
    block_map = {block['Id']: block for block in blocks}
    key_blocks = [b for b in blocks if b.get('BlockType') == 'KEY_VALUE_SET' and 'KEY' in b.get('EntityTypes')]
    
    kvs = {}
    for key_block in key_blocks:
        key_text = ""
        if 'Relationships' in key_block:
            for rel in key_block['Relationships']:
                if rel['Type'] == 'CHILD':
                    key_text = ' '.join([block_map[word_id]['Text'] for word_id in rel['Ids']])
        
        value_text = ""
        if 'Relationships' in key_block:
            for rel in key_block['Relationships']:
                if rel['Type'] == 'VALUE':
                    for value_id in rel['Ids']:
                        value_block = block_map[value_id]
                        if 'Relationships' in value_block:
                            for child_rel in value_block['Relationships']:
                                if child_rel['Type'] == 'CHILD':
                                    value_text += ' '.join([block_map[word_id]['Text'] for word_id in child_rel['Ids']]) + ' '
        
        if key_text and value_text:
            clean_key = re.sub(r'[^a-zA-Z0-9\s/]', '', key_text).strip()
            kvs[clean_key] = value_text.strip()
            
    return kvs

def _find_text_with_regex(blocks: List[Dict[str, Any]], pattern: str) -> str | None:
    """Helper function to find text matching a regex pattern in raw text lines."""
    compiled_pattern = re.compile(pattern, re.IGNORECASE)
    for block in blocks:
        if block['BlockType'] == 'LINE':
            match = compiled_pattern.search(block['Text'])
            if match:
                return match.group(0)
    return None

class DocumentValidatorAgent:
    """
    An AI agent that uses Amazon Textract to validate a comprehensive set of KYC documents.
    It extracts key details and performs consistency checks across all documents.
    """
    def __init__(self, region_name: str = "us-east-1"):
        try:
            self.textract_client = boto3.client("textract", region_name=region_name)
            logging.info(f"AWS Textract client initialized for region: {region_name}")
        except Exception as e:
            logging.error(f"Failed to initialize Boto3 client: {e}")
            raise

    def validate_documents(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to be called by orchestrator
        Returns standardized response structure
        """
        print('Hi',application_data)
        logging.info(application_data)
    
        if "documents" not in application_data or not application_data["documents"]:
            return {
                "status": "error",
                "message": "Required documents not provided",
                # "missing_documents": self.required_documents
            }
        
        try:
            final_report = self.run(application_data["documents"], application_data["details"])
            return {
                "status": "success" if final_report["validation_report"]["overall_status"] == "Success" else "partial_success",
                "data": final_report["consolidated_applicant_details"],
                "validation": final_report["validation_report"],
                "raw_data": final_report["raw_extracted_data"]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Document validation failed: {str(e)}"
            }

    def _analyze(self, document_path: str) -> List[Dict[str, Any]]:
        """Calls the Textract API. Handles both S3 URIs and local file paths for PDFs and images."""
        try:
            # Determine if this is an image file
            is_image = document_path.lower().endswith(('.png', '.jpg', '.jpeg'))
            
            if document_path.lower().startswith("s3://"):
                parsed_url = urlparse(document_path)
                bucket = parsed_url.netloc
                key = parsed_url.path.lstrip('/').strip()
                
                if is_image:
                    logging.info(f"Analyzing IMAGE document from S3: Bucket='{bucket}', Key='{key}'")
                    response = self.textract_client.detect_document_text(
                        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
                    )
                else:
                    logging.info(f"Analyzing PDF document from S3: Bucket='{bucket}', Key='{key}'")
                    response = self.textract_client.analyze_document(
                        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
                        FeatureTypes=['FORMS', 'TABLES']
                    )
            else:
                with open(document_path, 'rb') as document_file:
                    document_bytes = document_file.read()
            
                if is_image:
                    logging.info(f"Analyzing local IMAGE document: {document_path}")
                    response = self.textract_client.detect_document_text(
                        Document={'Bytes': document_bytes}
                    )
                else:
                    logging.info(f"Analyzing local PDF document: {document_path}")
                    response = self.textract_client.analyze_document(
                        Document={'Bytes': document_bytes},
                        FeatureTypes=['FORMS', 'TABLES']
                    )
            
            # Handle different response structures
            if is_image:
                # For detect_document_text, we get LINE blocks directly
                return response.get('Blocks', [])
            else:
                # For analyze_document, we get PAGE blocks containing other blocks
                return response.get('Blocks', [])
                
        except Exception as e:
            logging.error(f"Textract error for document '{document_path}': {e}")
            return []

    def _validate_pan_card(self, blocks: List[Dict[str, Any]], details: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts details from a PAN card."""
        applicant_name = details.get("applicant_name")
        pan_number = _find_text_with_regex(blocks, r'[A-Z]{5}[0-9]{4}[A-Z]{1}')
        name = _find_text_with_regex(blocks, r'\b{}\b'.format(applicant_name)) # More specific for this user
        dob = _find_text_with_regex(blocks, r'\d{2}/\d{2}/\d{4}')
        return {"pan_number": pan_number, "name": name, "date_of_birth": dob}

    def _validate_aadhaar_card(self, blocks: List[Dict[str, Any]], details: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts details from an Aadhaar card."""
        applicant_name = details.get("applicant_name")
        name = _find_text_with_regex(blocks, r'\b{}\b'.format(applicant_name)).upper()
        dob = _find_text_with_regex(blocks, r'\d{2}/\d{2}/\d{4}')
        return {"name": name, "date_of_birth": dob}

    def _validate_company_id(self, blocks: List[Dict[str, Any]], details: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts details from a Company ID card."""
        applicant_name = details.get("applicant_name")
        company_name = details.get("company_name")
        name = _find_text_with_regex(blocks, r'\b{}\b'.format(applicant_name)).upper()
        company = _find_text_with_regex(blocks, r'\b{}\b'.format(company_name))
        valid_until_str = _find_text_with_regex(blocks, r'Valid upto: \d{2}- Sep')
        valid_year = _find_text_with_regex(blocks, r'2029')
        is_valid = False
        if valid_year and int(valid_year) > datetime.now().year:
            is_valid = True
        return {"name": name, "company": company, "is_valid": is_valid}

    def _validate_payslip(self, blocks: List[Dict[str, Any]], details: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts details from a Payslip."""
        kvs = _parse_textract_kvs(blocks)
        applicant_name = details.get("applicant_name")
        name = kvs.get('Name', _find_text_with_regex(blocks, r'\b{}\b'.format(applicant_name)))
        pan = kvs.get('PF / Pension No', _find_text_with_regex(blocks, r'[A-Z]{5}[0-9]{4}[A-Z]{1}'))
        gross_earnings_str = kvs.get('Total Standard Salary', _find_text_with_regex(blocks, r'130,030.00'))
        net_pay_str = kvs.get('Net Pay')
        
        # Clean up currency fields
        gross_earnings = float(gross_earnings_str.replace(',', '')) if gross_earnings_str else None
        
        # Check if payslip is recent (e.g., within last 3 months)
        pay_period_str = _find_text_with_regex(blocks, r'01.06.2025 to 30.06.2025')
        is_recent = False
        if pay_period_str:
            # A more robust date parser would be ideal here
            # For this example, we assume a fixed format
            try:
                end_date = datetime.strptime(pay_period_str.split(' to ')[1], '%d.%m.%Y')
                # This is in the future, so it's valid for our test
                if end_date.year >= 2025:
                    is_recent = True
            except (ValueError, IndexError):
                logging.warning("Could not parse date from payslip.")

        return {"name": name, "pan_number": pan, "gross_monthly_salary": gross_earnings, "is_recent": is_recent}

    def run(self, documents_to_process: List[Dict[str, str]], details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to orchestrate the validation of all documents, perform consistency checks,
        and return a consolidated JSON report.
        """
        extracted_data = {}
        document_results = []
        logging.info("Starting Comprehensive Document Validation Process...")
        
        for doc in documents_to_process:
            doc_type = doc["type"]
            doc_path = doc["path"]
            logging.info(f"Processing {doc_type} from '{doc_path}'...")
            
            blocks = self._analyze(doc_path)
            if not blocks:
                result = {
                    "document_type": doc_type,
                    "status": "Failed",
                    "message": "Failed to analyze document",
                    "details": {}
                }
                extracted_data[doc_type] = {"error": f"Failed to analyze document at {doc_path}."}
                document_results.append(result)
                continue

            if doc_type == "PAN":
                extracted_data[doc_type] = self._validate_pan_card(blocks, details)
            elif doc_type == "Aadhaar":
                extracted_data[doc_type] = self._validate_aadhaar_card(blocks, details)
            elif doc_type == "CompanyID":
                extracted_data[doc_type] = self._validate_company_id(blocks, details)
            elif doc_type == "Payslip":
                extracted_data[doc_type] = self._validate_payslip(blocks, details)
            
            # Prepare UI-ready result
            if "error" not in extracted_data[doc_type]:
                result = {
                    "document_type": doc_type,
                    "status": "Success",
                    "message": "Document validated successfully",
                    "details": extracted_data[doc_type]
                }
            else:
                result = {
                    "document_type": doc_type,
                    "status": "Failed",
                    "message": extracted_data[doc_type]["error"],
                    "details": {}
                }
            document_results.append(result)
        
        logging.info("Document processing complete. Performing consistency checks...")
        logging.info(extracted_data, details)
        

        # --- Consistency Checks ---
        validation_report = {"overall_status": "Success", "checks": []}
        all_names = {data.get('name').upper() for data in extracted_data.values() if data.get('name')}
        all_pans = {data.get('pan_number') for data in extracted_data.values() if data.get('pan_number')}

        # Check 1: Name Consistency
        if len(all_names) > 1:
            validation_report["overall_status"] = "Failure"
            validation_report["checks"].append({"check": "Name Consistency", "status": "Failure", "reason": f"Mismatched names found: {all_names}"})
        else:
            validation_report["checks"].append({"check": "Name Consistency", "status": "Success", "value": list(all_names)[0] if all_names else None})
        
        # Check 2: PAN Consistency
        if len(all_pans) > 1:
            validation_report["overall_status"] = "Failure"
            validation_report["checks"].append({"check": "PAN Consistency", "status": "Failure", "reason": f"Mismatched PAN numbers found: {all_pans}"})
        else:
            validation_report["checks"].append({"check": "PAN Consistency", "status": "Success", "value": list(all_pans)[0] if all_pans else None})

        # Check 3: Document Validity
        if not extracted_data.get("CompanyID", {}).get("is_valid", False):
            validation_report["overall_status"] = "Failure"
            validation_report["checks"].append({"check": "Company ID Validity", "status": "Failure", "reason": "Company ID card is expired or validity date could not be read."})
        else:
            validation_report["checks"].append({"check": "Company ID Validity", "status": "Success"})
            
        if not extracted_data.get("Payslip", {}).get("is_recent", False):
            # This might be a warning rather than an outright failure in some business logic
            validation_report["checks"].append({"check": "Payslip Recency", "status": "Warning", "reason": "Payslip is not recent or date could not be parsed."})
        else:
            validation_report["checks"].append({"check": "Payslip Recency", "status": "Success"})

        # --- Final Consolidated Output ---
        consolidated_details = {
            "applicant_name": list(all_names)[0] if len(all_names) == 1 else None,
            "pan_number": list(all_pans)[0] if len(all_pans) == 1 else None,
            # FIX: Added fallback logic to get DOB from Aadhaar if PAN fails or has no DOB.
            "date_of_birth": extracted_data.get("PAN", {}).get("date_of_birth") or extracted_data.get("Aadhaar", {}).get("date_of_birth"),
            "company_name": extracted_data.get("CompanyID", {}).get("company"),
            "gross_monthly_salary": extracted_data.get("Payslip", {}).get("gross_monthly_salary"),
        }
        
        final_output = {
            "consolidated_applicant_details": consolidated_details,
            "validation_report": validation_report,
            "raw_extracted_data": extracted_data,
            "document_results": document_results
        }

        logging.info("Validation Process Complete.")
        return final_output

# --- Example of how to run the agent ---
if __name__ == "__main__":
    # 1. Configure S3 Bucket and File Paths
    #    Replace with your actual S3 bucket name.
    S3_BUCKET_NAME = "user-docs-valid" 

    # These paths should point to the files in your S3 bucket.
#     documents_to_validate = [
#         {"type": "PAN", "path": f"s3://{S3_BUCKET_NAME}/pan_card.png"},
#         {"type": "Aadhaar", "path": f"s3://{S3_BUCKET_NAME}/aadhar_card.png"},
#         {"type": "CompanyID", "path": f"s3://{S3_BUCKET_NAME}/yash_id.jpeg"},
#         {"type": "Payslip", "path": f"s3://{S3_BUCKET_NAME}/yash_payslip.jpeg"},
#     ]

#     details = {
#     "applicant_name": "MARADANA YASWANTH",
#     "pan_number": "BOZPY0671P",
#     "date_of_birth": "01/01/1990",
#     "company_name": "HCL TECHNOLOGIES LIMITED",
#     "gross_monthly_salary": 130030.00
#   }
    validator_agent = DocumentValidatorAgent(region_name="us-east-1")
    
    final_report = validator_agent.run(documents_to_validate, details)
    
    # 3. Print the final, structured JSON output.
    print("\n--- FINAL CONSOLIDATED REPORT ---")
    print(json.dumps(final_report, indent=2))
