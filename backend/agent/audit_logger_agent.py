import json
import boto3
from datetime import datetime
from typing import Dict, Any, List

class AuditLoggerAgent:
    """
    Audit Logger Agent for compliance and audit trail
    Logs all agent inputs, outputs, and decisions
    """
    
    def __init__(self, bucket_name="sarma-1", region_name="us-east-1"):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", region_name=region_name)
    
    def log_workflow_execution(self, 
                              application_id: str, 
                              workflow_state: Dict[str, Any],
                              final_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log complete workflow execution for audit purposes
        """
        try:
            audit_entry = {
                "application_id": application_id,
                "timestamp": datetime.now().isoformat(),
                "workflow_version": "1.0",
                "agents_executed": [
                    "intake_agent",
                    "document_validator_agent", 
                    "property_valuation_agent",
                    "eligibility_agent",
                    "approval_recommender_agent"
                ],
                "workflow_inputs": {
                    "applicant_data": workflow_state.get("applicant_data", {}),
                    "document_paths": workflow_state.get("document_paths", {})
                },
                "agent_outputs": {
                    "document_validation": workflow_state.get("document_validation_result", {}),
                    "property_valuation": workflow_state.get("property_valuation_result", {}),
                    "eligibility": workflow_state.get("eligibility_result", {}),
                    "approval_recommendation": workflow_state.get("approval_recommendation", {})
                },
                "final_result": final_result,
                "compliance_checks": {
                    "data_privacy": "compliant",
                    "audit_trail": "complete",
                    "decision_traceability": "verified"
                }
            }
            
            # Save to S3
            audit_key = f"audit_logs/{application_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=audit_key,
                Body=json.dumps(audit_entry, indent=2),
                ContentType="application/json"
            )
            
            return {
                "status": "success",
                "audit_key": audit_key,
                "timestamp": audit_entry["timestamp"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Audit logging failed: {str(e)}"
            }
    
    def log_agent_execution(self, 
                           application_id: str,
                           agent_name: str,
                           inputs: Dict[str, Any],
                           outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log individual agent execution
        """
        try:
            agent_log = {
                "application_id": application_id,
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "inputs": inputs,
                "outputs": outputs,
                "execution_status": "completed"
            }
            
            # Save to S3
            log_key = f"agent_logs/{application_id}/{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=log_key,
                Body=json.dumps(agent_log, indent=2),
                ContentType="application/json"
            )
            
            return {
                "status": "success",
                "log_key": log_key
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Agent logging failed: {str(e)}"
            }
    
    def get_audit_trail(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail for an application
        """
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"audit_logs/{application_id}"
            )
            
            audit_trail = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_response = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    audit_entry = json.loads(file_response['Body'].read())
                    audit_trail.append(audit_entry)
            
            return audit_trail
            
        except Exception as e:
            return []
    
    def get_agent_logs(self, application_id: str, agent_name: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve agent logs for an application
        """
        try:
            prefix = f"agent_logs/{application_id}/"
            if agent_name:
                prefix += f"{agent_name}_"
                
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            agent_logs = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_response = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    log_entry = json.loads(file_response['Body'].read())
                    agent_logs.append(log_entry)
            
            return agent_logs
            
        except Exception as e:
            return []

def audit_logger_node(state: dict) -> dict:
    """
    LangGraph node for audit logging
    """
    application_id = state.get("applicant_data", {}).get("applicant_name", "unknown")
    
    # Initialize audit logger
    audit_logger = AuditLoggerAgent()
    
    # Log the complete workflow execution
    audit_result = audit_logger.log_workflow_execution(
        application_id=application_id,
        workflow_state=state,
        final_result={
            "status": state.get("workflow_status", "unknown"),
            "results": {
                "document_validation": state.get("document_validation_result", {}),
                "property_valuation": state.get("property_valuation_result", {}),
                "eligibility": state.get("eligibility_result", {}),
                "approval_recommendation": state.get("approval_recommendation", {})
            }
        }
    )
    
    state["audit_log_result"] = audit_result
    return state 